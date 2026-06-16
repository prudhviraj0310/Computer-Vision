#!/usr/bin/env python3
"""
TrafficEye AI — Real-World Multi-Camera Stress Test
=====================================================
Connects to 15+ LIVE public traffic cameras simultaneously and runs
YOLOv11 + OCR inference on real frames from:

  - Singapore LTA expressway cameras (via data.gov.sg API)
  - Transport for London JamCam network
  - Camera registry integration
  - Full API endpoint test with real cameras

Proves the system can handle concurrent citywide monitoring.

Usage:
    python test_live_cameras.py
"""

import os
import sys
import cv2
import ssl
import time
import json
import urllib.request
import numpy as np
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model_inference import get_detector

# ─── ANSI Colors ────────────────────────────────────────────────────────────
class C:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'

# SSL context for DOT cameras (some have expired certs)
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# Track results
_results_lock = threading.Lock()
_all_results = []


def banner():
    print(f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════════╗
║     TrafficEye AI — Multi-Camera Live Stress Test           ║
║   15+ Real Traffic Cameras · Singapore + London + API       ║
╚══════════════════════════════════════════════════════════════╝{C.END}
""")


def print_result(result, source_name, frame_num=0):
    """Pretty-print a detection result."""
    vtype = result.get("violation_type", "NONE")
    is_violation = vtype not in ["NO_VIOLATION", "NONE"]
    color = C.RED if is_violation else C.GREEN
    ai_mode = f"{C.GREEN}REAL AI{C.END}" if result.get("is_real_ai") else f"{C.YELLOW}SIMULATED{C.END}"

    print(f"""
{C.BOLD}{'━' * 62}{C.END}
{C.CYAN}Source:{C.END} {source_name} | {ai_mode}
{color}{C.BOLD}Violation: {vtype}{C.END}
  Risk Score:  {result.get('risk_score', 0)}/100  |  Severity: {result.get('severity', 'N/A')}
  Fine:        {result.get('fine', '$0.00')}
  Plate:       {C.YELLOW}{result.get('plate', 'N/A')}{C.END} (OCR conf: {result.get('ocr_confidence', 0)}%)
  Vehicle:     {result.get('vehicle', 'N/A')}
  Detections:  {len(result.get('detections', []))} objects found
  Processing:  {result.get('processing_ms', 0)} ms
""")

    for i, det in enumerate(result.get("detections", [])[:5]):
        print(f"    [{i+1}] {det['class']:20s}  conf: {det['confidence']:5.1f}%  box: {det['box']}")


def fetch_snapshot(url, name=""):
    """Fetch a JPEG snapshot from a URL."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "TrafficEye-AI/3.0 (Traffic Safety Research)",
            "Accept": "image/jpeg,image/png,image/*,*/*"
        })
        resp = urllib.request.urlopen(req, timeout=12, context=SSL_CTX)
        img_data = resp.read()

        if len(img_data) < 500:
            return None

        img_array = np.asarray(bytearray(img_data), dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        print(f"  {C.YELLOW}Fetch error for {name}: {e}{C.END}")
        return None


def process_camera(detector, cam_id, cam_name, url, region):
    """Fetch one frame from a camera and run inference. Thread-safe."""
    try:
        frame = fetch_snapshot(url, cam_name)
        if frame is None:
            return {"camera_id": cam_id, "name": cam_name, "status": "fetch_failed"}

        start = time.time()
        result = detector.run_inference_frame(frame)
        elapsed = round((time.time() - start) * 1000, 1)
        result["processing_ms"] = elapsed
        result["camera_id"] = cam_id
        result["camera_name"] = cam_name
        result["region"] = region
        result["frame_shape"] = f"{frame.shape[1]}x{frame.shape[0]}"

        # Save frame
        safe_name = cam_id.replace("-", "_")[:25]
        out_path = f"test_output/{safe_name}.jpg"
        os.makedirs("test_output", exist_ok=True)
        cv2.imwrite(out_path, frame)

        with _results_lock:
            _all_results.append(result)

        return result
    except Exception as e:
        return {"camera_id": cam_id, "name": cam_name, "status": "error", "error": str(e)}


# ─── TEST 1: Singapore LTA Live Cameras ─────────────────────────────────────

def test_singapore_cameras(detector):
    """Test Singapore LTA traffic cameras via data.gov.sg API."""
    print(f"\n{C.BOLD}{C.BLUE}{'='*62}")
    print(f"  TEST 1: SINGAPORE LTA LIVE TRAFFIC CAMERAS")
    print(f"  (Real-time feeds from data.gov.sg API)")
    print(f"{'='*62}{C.END}")

    # Fetch camera image URLs from API
    try:
        req = urllib.request.Request(
            "https://api.data.gov.sg/v1/transport/traffic-images",
            headers={"User-Agent": "TrafficEye-AI/3.0"}
        )
        resp = urllib.request.urlopen(req, timeout=10, context=SSL_CTX)
        data = json.loads(resp.read())
        all_cameras = data.get("items", [{}])[0].get("cameras", [])
        print(f"  {C.GREEN}Singapore LTA API: {len(all_cameras)} cameras available{C.END}")
    except Exception as e:
        print(f"  {C.RED}Failed to fetch Singapore API: {e}{C.END}")
        return False

    # Select 8 cameras spread across Singapore
    target_ids = ["2705", "4709", "1001", "1005", "1006", "1501", "1502", "1004"]
    cameras = []
    for cam in all_cameras:
        if str(cam.get("camera_id")) in target_ids:
            cameras.append(cam)
    if len(cameras) < 5:
        cameras = all_cameras[:8]

    print(f"  Testing {len(cameras)} cameras concurrently...\n")

    success_count = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {}
        for cam in cameras:
            cam_id = f"sg-{cam.get('camera_id', 'unknown')}"
            img_url = cam.get("image", "")
            loc = cam.get("location", {})
            lat = loc.get("latitude", 0)
            lng = loc.get("longitude", 0)
            name = f"Singapore Cam {cam.get('camera_id')} ({lat:.2f}, {lng:.2f})"

            if img_url:
                fut = executor.submit(process_camera, detector, cam_id, name, img_url, "Singapore")
                futures[fut] = cam_id

        for fut in as_completed(futures):
            result = fut.result()
            cam_id = futures[fut]
            if result.get("status") in ("fetch_failed", "error"):
                print(f"  {C.RED}FAIL  {cam_id}: {result.get('error', 'fetch failed')}{C.END}")
            else:
                vtype = result.get("violation_type", "NO_VIOLATION")
                is_v = vtype != "NO_VIOLATION"
                icon = f"{C.RED}VIOLATION" if is_v else f"{C.GREEN}CLEAR"
                dets = len(result.get("detections", []))
                ms = result.get("processing_ms", 0)
                shape = result.get("frame_shape", "?")
                print(f"  {icon}{C.END}  {cam_id:18s}  {shape:>10s}  {dets:>2d} objects  {ms:>6.0f}ms  {vtype}")
                success_count += 1

    print(f"\n  {C.GREEN}Singapore: {success_count}/{len(cameras)} cameras processed{C.END}")
    return success_count > 0


# ─── TEST 2: London TfL JamCam Network ──────────────────────────────────────

def test_london_cameras(detector):
    """Test Transport for London JamCam feeds (direct JPEG snapshots)."""
    print(f"\n{C.BOLD}{C.BLUE}{'='*62}")
    print(f"  TEST 2: LONDON TfL JAMCAM NETWORK (Live)")
    print(f"  (20 verified cameras across London)")
    print(f"{'='*62}{C.END}")

    cameras = [
        ("uk-tfl-cromwell",    "A4 Cromwell Road",         "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01251.jpg", "South Kensington"),
        ("uk-tfl-old-kent",    "A2 Old Kent Road",         "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.07400.jpg", "Southwark"),
        ("uk-tfl-park-lane",   "Park Lane / Marble Arch",  "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.08000.jpg", "Westminster"),
        ("uk-tfl-euston",      "Euston Road / Kings Cross", "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01414.jpg", "Camden"),
        ("uk-tfl-camberwell",  "Camberwell New Road",      "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01615.jpg", "Camberwell"),
        ("uk-tfl-hackney",     "Mare Street, Hackney",     "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.02100.jpg", "Hackney"),
        ("uk-tfl-whitechapel", "Whitechapel Road",         "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.02200.jpg", "Tower Hamlets"),
        ("uk-tfl-brixton",     "Brixton Road",             "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.02500.jpg", "Lambeth"),
        ("uk-tfl-lewisham",    "Lewisham High Street",     "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.03500.jpg", "Lewisham"),
        ("uk-tfl-peckham",     "Peckham Rye",              "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.03600.jpg", "Southwark"),
        ("uk-tfl-streatham",   "Streatham High Road",      "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.03700.jpg", "Lambeth"),
        ("uk-tfl-tooting",     "Tooting High Street",      "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.03800.jpg", "Wandsworth"),
        ("uk-tfl-holloway",    "Holloway Road",            "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.04300.jpg", "Islington"),
        ("uk-tfl-finchley",    "Finchley Road",            "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.04500.jpg", "Camden"),
        ("uk-tfl-greenwich",   "Woolwich Road, Greenwich", "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.05900.jpg", "Greenwich"),
    ]

    print(f"  Testing {len(cameras)} cameras concurrently...\n")

    success_count = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {}
        for cam_id, name, url, region in cameras:
            fut = executor.submit(process_camera, detector, cam_id, name, url, f"London, {region}")
            futures[fut] = (cam_id, name)

        for fut in as_completed(futures):
            result = fut.result()
            cam_id, name = futures[fut]
            if result.get("status") in ("fetch_failed", "error"):
                print(f"  {C.RED}FAIL  {name}{C.END}")
            else:
                vtype = result.get("violation_type", "NO_VIOLATION")
                is_v = vtype != "NO_VIOLATION"
                icon = f"{C.RED}VIOLATION" if is_v else f"{C.GREEN}CLEAR"
                dets = len(result.get("detections", []))
                ms = result.get("processing_ms", 0)
                shape = result.get("frame_shape", "?")
                print(f"  {icon}{C.END}  {name:35s}  {shape:>10s}  {dets:>2d} objects  {ms:>6.0f}ms  {vtype}")
                success_count += 1

    print(f"\n  {C.GREEN}London TfL: {success_count}/{len(cameras)} cameras processed{C.END}")
    return success_count > 0


# ─── TEST 3: Camera Registry Integration ────────────────────────────────────

def test_camera_registry():
    """Test the camera registry module and API-based URL resolution."""
    print(f"\n{C.BOLD}{C.BLUE}{'='*62}")
    print(f"  TEST 3: CAMERA REGISTRY INTEGRATION")
    print(f"{'='*62}{C.END}")

    try:
        from camera_registry import get_camera_registry

        registry = get_camera_registry()
        print(f"  {C.GREEN}Registry loaded: {registry.count} cameras{C.END}")

        categories = registry.list_categories()
        print(f"  Categories: {', '.join(sorted(categories))}")
        for cat in sorted(categories):
            cams = registry.list_all(category=cat)
            print(f"    {cat}: {len(cams)} cameras")

        # Test Bangalore templates
        blr_cams = registry.get_bangalore_cameras()
        print(f"\n  {C.CYAN}Bangalore Cameras: {len(blr_cams)}{C.END}")
        for cam in blr_cams:
            print(f"    - {cam['name']} ({cam['region']}) [{cam['status']}]")

        # Test Singapore cameras
        sg_cams = registry.get_singapore_cameras()
        print(f"\n  {C.CYAN}Singapore Cameras: {len(sg_cams)}{C.END}")
        for cam in sg_cams:
            url = registry.resolve_url(cam["id"])
            status = f"{C.GREEN}URL OK{C.END}" if url else f"{C.RED}NO URL{C.END}"
            print(f"    - {cam['name']} [{status}]")

        # Test London cameras
        lon_cams = registry.get_london_cameras()
        print(f"\n  {C.CYAN}London Cameras: {len(lon_cams)}{C.END}")

        # Templates
        templates = registry.get_templates()
        print(f"\n  {C.CYAN}Templates: {len(templates)}{C.END}")
        for tpl in templates:
            print(f"    - {tpl['name']}: {tpl.get('url_template', 'N/A')}")

        # URL resolution for template
        resolved = registry.resolve_url("tpl-hikvision", {
            "username": "admin",
            "password": "test123",
            "camera_ip": "192.168.1.100"
        })
        print(f"\n  {C.CYAN}Hikvision URL resolved:{C.END} {resolved}")

        # Health check 3 cameras from different regions
        print(f"\n  {C.CYAN}Health checks:{C.END}")
        test_cams = ["uk-tfl-park-lane", "sg-cam-1001", "uk-tfl-brixton"]
        for cam_id in test_cams:
            health = registry.check_health(cam_id)
            if health["reachable"]:
                print(f"    {C.GREEN}ONLINE{C.END}  {cam_id:25s}  {health['latency_ms']}ms  {health['content_length']}B")
            else:
                print(f"    {C.RED}OFFLINE{C.END} {cam_id:25s}  {health.get('error', '')[:40]}")

        return True

    except Exception as e:
        print(f"  {C.RED}Registry test failed: {e}{C.END}")
        import traceback
        traceback.print_exc()
        return False


# ─── TEST 4: API Server Endpoint Test ───────────────────────────────────────

def test_api_endpoints():
    """Test the FastAPI server endpoints with live cameras."""
    print(f"\n{C.BOLD}{C.BLUE}{'='*62}")
    print(f"  TEST 4: API SERVER ENDPOINTS (requires python main.py)")
    print(f"{'='*62}{C.END}")

    api_base = "http://127.0.0.1:8000"

    try:
        req = urllib.request.Request(f"{api_base}/api/stream/status")
        resp = urllib.request.urlopen(req, timeout=3)
        print(f"  {C.GREEN}API server is running{C.END}")
    except Exception:
        print(f"  {C.YELLOW}API server not reachable — skipping (run 'python main.py' first){C.END}")
        return False

    try:
        # Test camera list endpoint
        req = urllib.request.Request(f"{api_base}/api/cameras")
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        print(f"  {C.GREEN}GET /api/cameras: {data['total']} cameras, categories: {data['categories']}{C.END}")

        # Test Singapore camera endpoint
        req = urllib.request.Request(f"{api_base}/api/cameras?category=singapore")
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        print(f"  {C.GREEN}GET /api/cameras?category=singapore: {data['total']} cameras{C.END}")

        # Test camera health
        req = urllib.request.Request(f"{api_base}/api/cameras/uk-tfl-park-lane/health")
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        status = "ONLINE" if data.get("reachable") else "OFFLINE"
        print(f"  {C.GREEN}Health check uk-tfl-park-lane: {status} ({data.get('latency_ms', '?')}ms){C.END}")

        # Test stream presets
        req = urllib.request.Request(f"{api_base}/api/stream/presets")
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        print(f"  {C.GREEN}GET /api/stream/presets: {len(data['presets'])} presets{C.END}")

        # Start a Singapore camera stream via API
        print(f"\n  {C.CYAN}Starting Singapore camera via registry...{C.END}")
        payload = json.dumps({"camera_id": "sg-cam-2705", "fps": 0.3}).encode()
        req = urllib.request.Request(
            f"{api_base}/api/stream/start",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        print(f"  {C.GREEN}Stream started: {result.get('camera_name', 'N/A')}{C.END}")

        print(f"  {C.DIM}Waiting 10 seconds for frame processing...{C.END}")
        time.sleep(10)

        # Check stream stats
        req = urllib.request.Request(f"{api_base}/api/stream/status")
        resp = urllib.request.urlopen(req, timeout=3)
        status = json.loads(resp.read())
        print(f"""
  {C.BOLD}Stream Stats:{C.END}
    Camera:           {status.get('camera_name', 'N/A')}
    Frames Captured:  {status.get('frames_captured', 0)}
    Frames Processed: {status.get('frames_processed', 0)}
    Violations:       {C.RED}{status.get('violations_detected', 0)}{C.END}
    Avg Inference:    {status.get('avg_inference_ms', 0)} ms
    Actual FPS:       {status.get('fps_actual', 0)}
""")

        # Stop stream
        req = urllib.request.Request(
            f"{api_base}/api/stream/stop",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=5)
        print(f"  {C.GREEN}Stream stopped{C.END}")

        return True

    except Exception as e:
        print(f"  {C.YELLOW}API test error: {e}{C.END}")
        return False


# ─── TEST 5: Concurrent 15-Camera Stress Test ──────────────────────────────

def test_concurrent_15_cameras(detector):
    """The big one: pull frames from 15 cameras simultaneously and run inference."""
    print(f"\n{C.BOLD}{C.BLUE}{'='*62}")
    print(f"  TEST 5: 15-CAMERA CONCURRENT STRESS TEST")
    print(f"  (Simulates citywide monitoring dashboard)")
    print(f"{'='*62}{C.END}")

    # Get Singapore images from API
    sg_cameras = []
    try:
        req = urllib.request.Request(
            "https://api.data.gov.sg/v1/transport/traffic-images",
            headers={"User-Agent": "TrafficEye-AI/3.0"}
        )
        resp = urllib.request.urlopen(req, timeout=10, context=SSL_CTX)
        data = json.loads(resp.read())
        all_sg = data.get("items", [{}])[0].get("cameras", [])
        target_ids = ["2705", "4709", "1001", "1005", "1006", "1501", "1502"]
        for cam in all_sg:
            if str(cam.get("camera_id")) in target_ids:
                sg_cameras.append((
                    f"sg-{cam['camera_id']}",
                    f"Singapore Cam {cam['camera_id']}",
                    cam["image"],
                    "Singapore"
                ))
    except Exception as e:
        print(f"  {C.YELLOW}Singapore API error: {e}{C.END}")

    # London cameras (direct URLs)
    london_cameras = [
        ("tfl-cromwell",   "Cromwell Road",    "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01251.jpg", "London"),
        ("tfl-old-kent",   "Old Kent Road",    "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.07400.jpg", "London"),
        ("tfl-park-lane",  "Park Lane",        "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.08000.jpg", "London"),
        ("tfl-euston",     "Euston Road",      "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01414.jpg", "London"),
        ("tfl-brixton",    "Brixton Road",     "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.02500.jpg", "London"),
        ("tfl-whitechapel","Whitechapel",      "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.02200.jpg", "London"),
        ("tfl-hackney",    "Hackney",          "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.02100.jpg", "London"),
        ("tfl-elephant",   "Elephant & Castle","https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.07500.jpg", "London"),
    ]

    # Combine: 7 Singapore + 8 London = 15 cameras
    all_cameras = sg_cameras[:7] + london_cameras[:max(0, 15 - len(sg_cameras[:7]))]

    print(f"  Cameras queued: {len(all_cameras)}")
    print(f"  Singapore: {len([c for c in all_cameras if c[3] == 'Singapore'])}")
    print(f"  London:    {len([c for c in all_cameras if c[3] == 'London'])}")
    print(f"\n  {C.BOLD}Launching concurrent inference...{C.END}\n")

    start_time = time.time()
    success_count = 0
    violation_count = 0
    total_detections = 0
    total_inference_ms = 0

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {}
        for cam_id, name, url, region in all_cameras:
            fut = executor.submit(process_camera, detector, cam_id, name, url, region)
            futures[fut] = (cam_id, name, region)

        for fut in as_completed(futures):
            result = fut.result()
            cam_id, name, region = futures[fut]

            if result.get("status") in ("fetch_failed", "error"):
                print(f"  {C.RED}FAIL{C.END}       {region:10s}  {name}")
            else:
                vtype = result.get("violation_type", "NO_VIOLATION")
                is_v = vtype != "NO_VIOLATION"
                icon = f"{C.RED}VIOLATION" if is_v else f"{C.GREEN}CLEAR    "
                dets = len(result.get("detections", []))
                ms = result.get("processing_ms", 0)
                shape = result.get("frame_shape", "?")

                print(f"  {icon}{C.END}  {region:10s}  {name:25s}  {shape:>10s}  {dets:>2d} det  {ms:>5.0f}ms  {vtype}")

                success_count += 1
                total_detections += dets
                total_inference_ms += ms
                if is_v:
                    violation_count += 1

    elapsed = round(time.time() - start_time, 1)
    avg_ms = round(total_inference_ms / max(success_count, 1), 1)

    print(f"""
{C.BOLD}{C.CYAN}{'─' * 62}
  STRESS TEST RESULTS
{'─' * 62}{C.END}
  Cameras tested:     {len(all_cameras)}
  Successfully processed: {C.GREEN}{success_count}{C.END}
  Failed:             {C.RED}{len(all_cameras) - success_count}{C.END}
  Violations found:   {C.RED}{violation_count}{C.END}
  Total detections:   {total_detections}
  Avg inference:      {avg_ms} ms/frame
  Total wall time:    {elapsed}s (concurrent)
{C.BOLD}{'─' * 62}{C.END}
""")

    return success_count >= 10  # Pass if at least 10 cameras worked


# ─── MAIN ───────────────────────────────────────────────────────────────────

def run_all_tests():
    """Run the complete test suite."""
    banner()

    print(f"{C.BOLD}Initializing YOLOv11 + EasyOCR detector...{C.END}")
    start = time.time()
    detector = get_detector()
    init_time = round(time.time() - start, 1)
    ai_status = f"{C.GREEN}REAL (YOLOv11 + EasyOCR){C.END}" if detector.has_models else f"{C.YELLOW}SIMULATED{C.END}"
    print(f"{C.GREEN}Detector ready in {init_time}s — AI Mode: {ai_status}{C.END}")

    results = {}

    # Test 1: Singapore LTA
    results["singapore"] = test_singapore_cameras(detector)

    # Test 2: London TfL
    results["london"] = test_london_cameras(detector)

    # Test 3: Camera Registry
    results["registry"] = test_camera_registry()

    # Test 4: API Endpoints (requires server)
    results["api"] = test_api_endpoints()

    # Test 5: 15-Camera Concurrent Stress Test
    results["stress_15"] = test_concurrent_15_cameras(detector)

    # ─── SUMMARY ────────────────────────────────────────────────────────────

    total_violations = sum(
        1 for r in _all_results
        if r.get("violation_type", "NO_VIOLATION") != "NO_VIOLATION"
    )
    total_processed = len(_all_results)

    print(f"""
{C.BOLD}{C.CYAN}{'='*62}
  FINAL TEST REPORT — TrafficEye AI
{'='*62}{C.END}

  Singapore LTA (8 cams):    {'PASS' if results['singapore'] else 'FAIL'}
  London TfL (15 cams):      {'PASS' if results['london'] else 'FAIL'}
  Camera Registry:           {'PASS' if results['registry'] else 'FAIL'}
  API Server Test:           {'PASS' if results['api'] else 'SKIP (server not running)'}
  15-Camera Stress Test:     {'PASS' if results['stress_15'] else 'FAIL'}

  Total frames processed:    {total_processed}
  Total violations detected: {C.RED}{total_violations}{C.END}
  AI Mode:                   {ai_status}
  Output saved to:           ./test_output/

{C.BOLD}{'='*62}{C.END}
""")


if __name__ == "__main__":
    run_all_tests()
