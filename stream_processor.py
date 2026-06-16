"""
TrafficEye AI — Live Camera Stream Processor
=============================================
Connects to MJPEG, RTSP, HLS, or JPEG snapshot feeds and runs
YOLOv11 + OCR inference on each frame in a background thread.

Supports:
  - Real-world traffic cameras (DOT snapshots, TfL JamCams, Caltrans, etc.)
  - Indian traffic cameras (Hikvision/Dahua RTSP with auth)
  - Phone cameras (IP Webcam, RTSP Camera Server)
  - Local video files (for demo/presentation)
  - Webcam (device index 0, 1, etc.)
  - Multi-camera concurrent streaming

Results are pushed to connected WebSocket clients in real-time.
"""

import os
import cv2
import time
import json
import asyncio
import threading
import queue
import logging
import ssl
from datetime import datetime
from typing import Optional, Dict, List, Callable

logger = logging.getLogger("StreamProcessor")


class StreamManager:
    """
    Manages a single video/camera stream connection and frame processing.
    Runs capture and inference in separate background threads to avoid
    frame backpressure (capture never blocks on slow inference).
    """

    def __init__(self, detector, on_result: Optional[Callable] = None, target_fps: float = 2.0):
        self.detector = detector
        self.on_result = on_result
        self.target_fps = target_fps

        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_queue: queue.Queue = queue.Queue(maxsize=5)
        self._capture_thread: Optional[threading.Thread] = None
        self._inference_thread: Optional[threading.Thread] = None
        self._running = False
        self._stream_url = ""
        self._stream_type = "unknown"
        self._camera_id = None  # Registry camera ID if connected via registry
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._stats = {
            "frames_captured": 0,
            "frames_processed": 0,
            "violations_detected": 0,
            "avg_inference_ms": 0.0,
            "last_violation": None,
            "started_at": None,
            "fps_actual": 0.0,
            "camera_id": None,
            "camera_name": None,
            "reconnect_count": 0,
        }
        self._inference_times: List[float] = []
        self._ws_clients: List = []
        self._ws_lock = threading.Lock()
        self._stats_lock = threading.Lock()
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def status(self) -> dict:
        with self._stats_lock:
            snapshot = self._stats.copy()
        return {
            "running": self._running,
            "stream_url": self._stream_url,
            "stream_type": self._stream_type,
            "target_fps": self.target_fps,
            **snapshot
        }

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """Store a reference to the asyncio event loop for thread-safe WebSocket sends."""
        self._event_loop = loop

    def start(self, stream_url: str, stream_type: str = "auto", camera_id: str = None, camera_name: str = None):
        """
        Connect to a stream and start processing.

        Args:
            stream_url: URL or device index
            stream_type: "mjpeg", "rtsp", "hls", "snapshot", "webcam", "file", or "auto"
            camera_id: Optional camera registry ID for tracking
            camera_name: Optional human-readable camera name
        """
        if self._running:
            self.stop()

        self._stream_url = stream_url
        self._stream_type = stream_type if stream_type != "auto" else self._detect_stream_type(stream_url)
        self._camera_id = camera_id
        self._reconnect_attempts = 0

        logger.info(f"[StreamManager] Starting stream: {stream_url} (type: {self._stream_type})")

        # Reset stats
        with self._stats_lock:
            self._stats = {
                "frames_captured": 0,
                "frames_processed": 0,
                "violations_detected": 0,
                "avg_inference_ms": 0.0,
                "last_violation": None,
                "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fps_actual": 0.0,
                "camera_id": camera_id,
                "camera_name": camera_name,
                "reconnect_count": 0,
            }
        self._inference_times = []

        # Open video capture
        if self._stream_type == "webcam":
            cap_source = int(stream_url) if stream_url.isdigit() else 0
        elif self._stream_type == "snapshot":
            cap_source = None
        else:
            cap_source = stream_url

        if cap_source is not None:
            self._cap = self._open_capture(cap_source)
            if not self._cap or not self._cap.isOpened():
                raise ConnectionError(f"Failed to open stream: {stream_url}")

        self._running = True

        self._capture_thread = threading.Thread(
            target=self._capture_loop, daemon=True, name="StreamCapture"
        )
        self._capture_thread.start()

        self._inference_thread = threading.Thread(
            target=self._inference_loop, daemon=True, name="StreamInference"
        )
        self._inference_thread.start()

        logger.info(f"[StreamManager] Stream started successfully. Processing at {self.target_fps} FPS.")

    def _open_capture(self, source) -> Optional[cv2.VideoCapture]:
        """Open a cv2.VideoCapture with optimized settings for real cameras."""
        cap = cv2.VideoCapture(source)

        if cap.isOpened():
            # Buffer size 1 = always get latest frame (critical for live feeds)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # For RTSP streams, prefer TCP transport (more reliable than UDP)
            if isinstance(source, str) and source.lower().startswith("rtsp://"):
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
                # Set RTSP transport to TCP via environment
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

        return cap

    def stop(self):
        """Stop the stream and clean up."""
        logger.info("[StreamManager] Stopping stream...")
        self._running = False

        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=3.0)
        if self._inference_thread and self._inference_thread.is_alive():
            self._inference_thread.join(timeout=5.0)

        if self._cap:
            self._cap.release()
            self._cap = None

        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except queue.Empty:
                break

        logger.info("[StreamManager] Stream stopped.")

    def add_ws_client(self, ws):
        """Register a WebSocket client for real-time result pushes."""
        with self._ws_lock:
            self._ws_clients.append(ws)

    def remove_ws_client(self, ws):
        """Unregister a WebSocket client."""
        with self._ws_lock:
            if ws in self._ws_clients:
                self._ws_clients.remove(ws)

    def _detect_stream_type(self, url: str) -> str:
        """Auto-detect stream type from URL pattern."""
        url_lower = url.lower()
        if url.isdigit():
            return "webcam"
        elif url_lower.startswith("rtsp://"):
            return "rtsp"
        elif ".m3u8" in url_lower or "manifest" in url_lower:
            return "hls"
        elif url_lower.endswith((".mp4", ".avi", ".mkv", ".mov")):
            return "file"
        elif url_lower.endswith((".jpg", ".jpeg", ".png")):
            return "snapshot"
        elif "image" in url_lower or "snapshot" in url_lower or "/api/image/" in url_lower:
            return "snapshot"
        elif "jamcams" in url_lower or "cctv" in url_lower:
            return "snapshot"
        elif "/video" in url_lower or "mjpeg" in url_lower or "mjpg" in url_lower:
            return "mjpeg"
        elif "data.gov.sg" in url_lower or "images.data.gov" in url_lower:
            return "snapshot"
        elif "tfl.gov.uk" in url_lower or "highwaysengland" in url_lower:
            return "snapshot"
        elif "dot.ca.gov" in url_lower or "dot.state" in url_lower:
            return "snapshot"
        elif "ohgo.com" in url_lower or "nyctmc.org" in url_lower:
            return "snapshot"
        elif "511" in url_lower and ".gov" in url_lower:
            return "snapshot"
        else:
            return "rtsp"

    def _capture_loop(self):
        """
        Background thread: captures frames from the stream.
        Drops frames if the inference thread falls behind.
        Handles reconnection for real-world cameras.
        """
        frame_interval = 1.0 / self.target_fps
        last_capture_time = 0

        while self._running:
            now = time.time()
            if now - last_capture_time < frame_interval:
                time.sleep(0.01)
                continue

            try:
                if self._stream_type == "snapshot":
                    frame = self._fetch_snapshot(self._stream_url)
                else:
                    if self._cap is None or not self._cap.isOpened():
                        if self._reconnect_attempts >= self._max_reconnect_attempts:
                            logger.error("[StreamManager] Max reconnection attempts reached. Stopping.")
                            self._running = False
                            break

                        self._reconnect_attempts += 1
                        with self._stats_lock:
                            self._stats["reconnect_count"] = self._reconnect_attempts
                        backoff = min(3 * self._reconnect_attempts, 30)
                        logger.warning(f"[StreamManager] Video capture lost. Reconnecting in {backoff}s (attempt {self._reconnect_attempts})...")
                        time.sleep(backoff)

                        if self._stream_type == "webcam":
                            cap_source = int(self._stream_url) if self._stream_url.isdigit() else 0
                        else:
                            cap_source = self._stream_url
                        self._cap = self._open_capture(cap_source)
                        continue

                    ret, frame = self._cap.read()
                    if not ret:
                        if self._stream_type == "file":
                            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            continue
                        else:
                            logger.warning("[StreamManager] Frame read failed. Retrying...")
                            time.sleep(1)
                            continue
                    else:
                        # Reset reconnect counter on successful read
                        self._reconnect_attempts = 0

                if frame is not None and frame.size > 0:
                    with self._stats_lock:
                        self._stats["frames_captured"] += 1
                    last_capture_time = now

                    if self._frame_queue.full():
                        try:
                            self._frame_queue.get_nowait()
                        except queue.Empty:
                            pass

                    self._frame_queue.put(frame, block=False)

            except Exception as e:
                logger.error(f"[StreamManager] Capture error: {e}")
                time.sleep(1)

        logger.info("[StreamManager] Capture loop ended.")

    def _inference_loop(self):
        """
        Background thread: pulls frames from queue and runs AI inference.
        Pushes results to WebSocket clients and callback.
        """
        while self._running:
            try:
                frame = self._frame_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                start_time = time.time()
                result = self.detector.run_inference_frame(frame)
                elapsed_ms = round((time.time() - start_time) * 1000, 1)
                result["processing_ms"] = elapsed_ms

                # Attach camera info to result
                result["camera_id"] = self._camera_id
                with self._stats_lock:
                    result["camera_name"] = self._stats.get("camera_name")

                with self._stats_lock:
                    self._stats["frames_processed"] += 1
                    self._inference_times.append(elapsed_ms)

                    if len(self._inference_times) > 50:
                        self._inference_times = self._inference_times[-50:]
                    self._stats["avg_inference_ms"] = round(
                        sum(self._inference_times) / len(self._inference_times), 1
                    )

                    if self._stats["started_at"]:
                        elapsed_sec = time.time() - time.mktime(
                            time.strptime(self._stats["started_at"], "%Y-%m-%d %H:%M:%S")
                        )
                        if elapsed_sec > 0:
                            self._stats["fps_actual"] = round(
                                self._stats["frames_processed"] / elapsed_sec, 2
                            )

                    if result.get("violation_type", "NO_VIOLATION") != "NO_VIOLATION":
                        self._stats["violations_detected"] += 1
                        self._stats["last_violation"] = {
                            "type": result["violation_type"],
                            "plate": result.get("plate", "UNKNOWN"),
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "risk_score": result.get("risk_score", 0),
                            "camera_id": self._camera_id,
                        }

                # Save violation snapshot image
                if result.get("violation_type", "NO_VIOLATION") != "NO_VIOLATION":
                    try:
                        snap_dir = "violation_snapshots"
                        os.makedirs(snap_dir, exist_ok=True)
                        snap_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{result['violation_type']}.jpg"
                        snap_path = os.path.join(snap_dir, snap_name)
                        cv2.imwrite(snap_path, frame)
                        result["snapshot_path"] = snap_path
                    except Exception as snap_err:
                        logger.error(f"[StreamManager] Snapshot save error: {snap_err}")

                if self.on_result:
                    try:
                        self.on_result(result)
                    except Exception as e:
                        logger.error(f"[StreamManager] Result callback error: {e}")

                self._broadcast_result(result)

            except Exception as e:
                logger.error(f"[StreamManager] Inference error: {e}")

        logger.info("[StreamManager] Inference loop ended.")

    def _fetch_snapshot(self, url: str):
        """Fetch a JPEG snapshot from a URL and decode to cv2 frame."""
        import urllib.request
        import numpy as np

        try:
            # SECURITY NOTE: SSL certificate verification is intentionally disabled here.
            # Many government DOT / traffic cameras use expired or self-signed certificates.
            # This is acceptable because we are only *reading* public image data, not
            # transmitting sensitive information. In a production deployment behind a
            # corporate network, consider using a custom CA bundle instead.
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(url, headers={
                "User-Agent": "TrafficEye-AI/3.0 (Traffic Safety Research)",
                "Accept": "image/jpeg,image/png,image/*,*/*"
            })
            resp = urllib.request.urlopen(req, timeout=10, context=ctx)
            data = resp.read()

            if len(data) < 500:
                logger.warning(f"[StreamManager] Snapshot too small ({len(data)} bytes), likely not an image")
                return None

            img_array = np.asarray(bytearray(data), dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            logger.error(f"[StreamManager] Snapshot fetch error: {e}")
            return None

    def _broadcast_result(self, result: dict):
        """Send inference result to all connected WebSocket clients."""
        with self._ws_lock:
            if not self._ws_clients:
                return
            clients_snapshot = list(self._ws_clients)

        with self._stats_lock:
            stats_snapshot = self._stats.copy()

        payload = {
            "type": "violation_detected" if result.get("violation_type", "NO_VIOLATION") != "NO_VIOLATION" else "frame_processed",
            "data": {
                "violation_type": result.get("violation_type"),
                "plate": result.get("plate"),
                "risk_score": result.get("risk_score"),
                "severity": result.get("severity"),
                "fine": result.get("fine"),
                "vehicle": result.get("vehicle"),
                "is_real_ai": result.get("is_real_ai"),
                "processing_ms": result.get("processing_ms"),
                "detections_count": len(result.get("detections", [])),
                "timestamp": result.get("timestamp"),
                "details": result.get("details", {}),
                "camera_id": result.get("camera_id"),
                "camera_name": result.get("camera_name"),
            },
            "stats": stats_snapshot
        }

        message = json.dumps(payload)
        dead_clients = []

        loop = self._event_loop
        for ws in clients_snapshot:
            try:
                if loop is not None and loop.is_running():
                    asyncio.run_coroutine_threadsafe(ws.send_text(message), loop)
                else:
                    # Fallback: try to create a new loop (should not normally happen)
                    asyncio.run(ws.send_text(message))
            except Exception:
                dead_clients.append(ws)

        if dead_clients:
            with self._ws_lock:
                for ws in dead_clients:
                    if ws in self._ws_clients:
                        self._ws_clients.remove(ws)


class MultiStreamManager:
    """
    Manages multiple concurrent camera streams for citywide monitoring.
    Each stream runs its own capture + inference threads via StreamManager.
    """

    def __init__(self, detector, on_result: Optional[Callable] = None, max_streams: int = 8):
        self.detector = detector
        self.on_result = on_result
        self.max_streams = max_streams
        self._streams: Dict[str, StreamManager] = {}
        self._lock = threading.Lock()

    def start_camera(self, camera_id: str, url: str, stream_type: str = "auto",
                     camera_name: str = None, fps: float = 1.0) -> Dict:
        """Start processing a camera feed."""
        with self._lock:
            if camera_id in self._streams and self._streams[camera_id].is_running:
                return {"status": "already_running", "camera_id": camera_id}

            if len(self._streams) >= self.max_streams:
                return {"status": "error", "message": f"Max {self.max_streams} concurrent streams reached"}

            sm = StreamManager(self.detector, on_result=self.on_result, target_fps=fps)
            try:
                sm.start(url, stream_type, camera_id=camera_id, camera_name=camera_name)
                self._streams[camera_id] = sm
                return {"status": "started", "camera_id": camera_id, "camera_name": camera_name}
            except ConnectionError as e:
                return {"status": "error", "message": str(e)}

    def stop_camera(self, camera_id: str) -> Dict:
        """Stop a specific camera stream."""
        with self._lock:
            if camera_id not in self._streams:
                return {"status": "not_found", "camera_id": camera_id}
            self._streams[camera_id].stop()
            del self._streams[camera_id]
            return {"status": "stopped", "camera_id": camera_id}

    def stop_all(self):
        """Stop all camera streams."""
        with self._lock:
            for cam_id, sm in self._streams.items():
                sm.stop()
            self._streams.clear()

    def get_status(self, camera_id: str = None) -> Dict:
        """Get status of one or all streams."""
        if camera_id:
            sm = self._streams.get(camera_id)
            return sm.status if sm else {"running": False, "camera_id": camera_id}

        return {
            "active_streams": len(self._streams),
            "max_streams": self.max_streams,
            "cameras": {
                cam_id: sm.status for cam_id, sm in self._streams.items()
            }
        }

    def add_ws_client(self, ws):
        """Register a WebSocket client on all active streams."""
        for sm in self._streams.values():
            sm.add_ws_client(ws)

    def remove_ws_client(self, ws):
        """Remove a WebSocket client from all streams."""
        for sm in self._streams.values():
            sm.remove_ws_client(ws)

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """Propagate event loop reference to all active streams."""
        for sm in self._streams.values():
            sm.set_event_loop(loop)


# ─── Module-level singletons ────────────────────────────────────────────────
_stream_manager: Optional[StreamManager] = None
_multi_stream_manager: Optional[MultiStreamManager] = None

def get_stream_manager(detector=None, on_result=None) -> StreamManager:
    """Returns a singleton StreamManager instance."""
    global _stream_manager
    if _stream_manager is None:
        if detector is None:
            from model_inference import get_detector
            detector = get_detector()
        _stream_manager = StreamManager(detector, on_result=on_result)
    return _stream_manager

def get_multi_stream_manager(detector=None, on_result=None) -> MultiStreamManager:
    """Returns a singleton MultiStreamManager instance."""
    global _multi_stream_manager
    if _multi_stream_manager is None:
        if detector is None:
            from model_inference import get_detector
            detector = get_detector()
        _multi_stream_manager = MultiStreamManager(detector, on_result=on_result)
    return _multi_stream_manager
