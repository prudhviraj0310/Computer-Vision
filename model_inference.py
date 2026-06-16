import os
import re
import cv2
import numpy as np
import time

# Try importing ML dependencies. If not installed, we gracefully fallback
# to simulation mode to keep the API server running, while preserving
# the actual PyTorch code for production use.
HAS_AI_LIBS = False
try:
    import torch
    from ultralytics import YOLO
    import easyocr
    HAS_AI_LIBS = True
    print("[TrafficEye AI] AI libraries (PyTorch, YOLOv11, EasyOCR) detected. Running in REAL mode.")
except ImportError:
    print("[TrafficEye AI] Warning: ML libraries not found. Running in SIMULATED mode.")


# ─── Indian License Plate Regex Parser (VAAHAN format) ──────────────────────
# Format: XX-00-XX-0000 or XX00XX0000 (state code, district, series, number)
INDIAN_PLATE_REGEX = re.compile(
    r'([A-Z]{2})\s*[-]?\s*(\d{1,2})\s*[-]?\s*([A-Z]{1,3})\s*[-]?\s*(\d{1,4})',
    re.IGNORECASE
)

def parse_indian_plate(raw_text: str) -> str:
    """
    Validates and formats an OCR-read string into standard Indian plate format.
    Returns formatted plate like 'KA-51-MD-9041' or original text if no match.
    """
    cleaned = raw_text.upper().strip()
    match = INDIAN_PLATE_REGEX.search(cleaned)
    if match:
        state, district, series, number = match.groups()
        return f"{state}-{district.zfill(2)}-{series}-{number.zfill(4)}"
    return cleaned


class TrafficEyeDetector:
    def __init__(self):
        self.has_models = HAS_AI_LIBS
        if self.has_models:
            try:
                # Load YOLOv11 models (nano model for vehicle detection)
                # 'yolo11n.pt' auto-downloads from Ultralytics on first run.
                self.vehicle_model = YOLO("yolo11n.pt")
                # OCR reader for license plates
                self.ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
            except Exception as e:
                print(f"[TrafficEye AI] Warning: Failed to load AI models ({e}). Falling back to simulated mode.")
                self.has_models = False
                self.vehicle_model = None
                self.ocr_reader = None
        else:
            self.vehicle_model = None
            self.ocr_reader = None

    def enhance_image(self, img):
        """
        Applies CLAHE (Contrast Limited Adaptive Histogram Equalization)
        to normalize lighting and remove shadows.
        """
        if img is None or img.size == 0:
            return img
        # Convert to YUV color space
        yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        # Apply CLAHE to Y channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        yuv[:, :, 0] = clahe.apply(yuv[:, :, 0])
        # Convert back to BGR
        enhanced = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        return enhanced

    def _crop_and_ocr_plate(self, img, detections):
        """
        Finds license plate regions from detections and runs OCR only on
        the cropped plate region (not the full image). Falls back to full
        image OCR if no plate-like bounding box is found.
        """
        plate_text = ""
        ocr_conf = 0.0

        if not self.ocr_reader:
            return "UNKNOWN", 0.0

        h, w = img.shape[:2]

        # Strategy 1: Look for small boxes that could be license plates
        # License plates are typically small, wide rectangles
        candidate_crops = []
        for d in detections:
            box = d["box"]
            bw = box[2] - box[0]
            bh = box[3] - box[1]
            aspect_ratio = bw / max(bh, 1)
            # Plate-like aspect ratio (2:1 to 5:1) and reasonable size
            if 1.5 < aspect_ratio < 6.0 and bw > 40 and bh > 15:
                candidate_crops.append(box)

        # Strategy 2: For vehicles, crop the lower portion (where plate usually is)
        vehicle_classes = ["car", "truck", "bus", "motorcycle"]
        for d in detections:
            if d["class"].lower() in vehicle_classes:
                box = d["box"]
                bh = box[3] - box[1]
                # Lower 40% of vehicle bounding box is likely plate area
                plate_region = [
                    max(0, box[0] - 10),
                    box[1] + int(bh * 0.6),
                    min(w, box[2] + 10),
                    min(h, box[3] + 10)
                ]
                candidate_crops.append(plate_region)

        # Run OCR on candidate crops first
        for crop_box in candidate_crops:
            x1, y1, x2, y2 = [int(c) for c in crop_box]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            if x2 <= x1 or y2 <= y1:
                continue
            crop = img[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            try:
                ocr_results = self.ocr_reader.readtext(crop)
                for (bbox, text, prob) in ocr_results:
                    cleaned = "".join([c for c in text if c.isalnum() or c in ['-', ' ']]).strip().upper()
                    if len(cleaned) >= 6:
                        parsed = parse_indian_plate(cleaned)
                        if prob > ocr_conf:
                            plate_text = parsed
                            ocr_conf = round(prob * 100, 1)
            except Exception:
                continue

        # Fallback: run OCR on full image if no plate found from crops
        if not plate_text and self.ocr_reader:
            try:
                ocr_results = self.ocr_reader.readtext(img)
                for (bbox, text, prob) in ocr_results:
                    cleaned = "".join([c for c in text if c.isalnum() or c in ['-', ' ']]).strip().upper()
                    if len(cleaned) >= 6:
                        parsed = parse_indian_plate(cleaned)
                        plate_text = parsed
                        ocr_conf = round(prob * 100, 1)
                        break
            except Exception:
                pass

        if not plate_text:
            plate_text = "UNREADABLE"
            ocr_conf = 0.0

        return plate_text, ocr_conf

    def run_inference_frame(self, frame):
        """
        Processes a cv2 frame directly (for live camera / video stream).
        Does NOT require a file path — works with in-memory frames.
        """
        if frame is None or frame.size == 0:
            return self._empty_result()

        # If AI models not available, return simulation
        if not self.has_models:
            return self._run_simulated_inference_generic()

        # 1. Image Enhancement
        enhanced = self.enhance_image(frame)

        # 2. Run YOLO detection
        detections = self._run_yolo_detection(enhanced)

        # 3. OCR on cropped plate regions
        plate_text, ocr_conf = self._crop_and_ocr_plate(enhanced, detections)

        # 4. Classify violations
        violation_result = self._classify_violations(enhanced, detections)

        return {
            "is_real_ai": True,
            "plate": plate_text,
            "ocr_confidence": ocr_conf,
            "violation_type": violation_result["violation_type"],
            "risk_score": violation_result["risk_score"],
            "severity": violation_result["severity"],
            "fine": violation_result["fine"],
            "vehicle": violation_result["vehicle"],
            "detections": detections,
            "details": violation_result["details"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "processing_ms": 0  # Will be set by caller
        }

    def run_inference(self, image_path: str):
        """
        Processes a traffic image from file path. Enhances it, detects
        vehicles/infractions, extracts license plate via OCR, and
        calculates risk scores.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")

        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not decode image at {image_path}")

        # If AI models not available, use simulation
        if not self.has_models:
            filename = os.path.basename(image_path).lower()
            return self._run_simulated_inference(filename)

        # Use the frame-based pipeline (shared logic)
        start_time = time.time()

        # 1. Image Enhancement
        enhanced = self.enhance_image(img)

        # 2. Run YOLO detection
        detections = self._run_yolo_detection(enhanced)

        # 3. OCR on cropped plate regions
        plate_text, ocr_conf = self._crop_and_ocr_plate(enhanced, detections)

        # 4. Classify violations
        violation_result = self._classify_violations(enhanced, detections)

        elapsed_ms = round((time.time() - start_time) * 1000, 1)

        return {
            "is_real_ai": True,
            "plate": plate_text,
            "ocr_confidence": ocr_conf,
            "violation_type": violation_result["violation_type"],
            "risk_score": violation_result["risk_score"],
            "severity": violation_result["severity"],
            "fine": violation_result["fine"],
            "vehicle": violation_result["vehicle"],
            "detections": detections,
            "details": violation_result["details"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "processing_ms": elapsed_ms
        }

    def _run_yolo_detection(self, enhanced_img):
        """Run YOLOv11 object detection and return parsed detections list."""
        detections = []
        results = self.vehicle_model(enhanced_img, verbose=False)

        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = box.conf[0].item()
                cls_id = int(box.cls[0].item())
                cls_name = self.vehicle_model.names[cls_id]

                detections.append({
                    "box": [round(x1), round(y1), round(x2), round(y2)],
                    "class": cls_name,
                    "confidence": round(conf * 100, 1)
                })

        return detections

    def _classify_violations(self, enhanced_img, detections):
        """
        Analyzes detections to classify traffic violations.
        Uses spatial overlap analysis, color detection, and class relationships.
        """
        violation_type = "NO_VIOLATION"
        risk_score = 10
        severity = "info"
        fine = "$0.00"
        vehicle_class = "Automobile"
        speed_str = None
        location_str = None
        weather_str = "unknown"

        detected_classes = [d["class"].lower() for d in detections]
        has_person = "person" in detected_classes
        has_cell_phone = "cell phone" in detected_classes
        has_motorcycle = "motorcycle" in detected_classes or "bicycle" in detected_classes
        has_traffic_light = "traffic light" in detected_classes

        # Identify vehicle type
        if "motorcycle" in detected_classes:
            vehicle_class = "Motorcycle"
        elif "bus" in detected_classes:
            vehicle_class = "Bus"
        elif "truck" in detected_classes:
            vehicle_class = "Truck"
        elif "car" in detected_classes:
            vehicle_class = "Sedan"

        person_boxes = [d["box"] for d in detections if d["class"].lower() == "person"]
        motorcycle_boxes = [d["box"] for d in detections if d["class"].lower() in ["motorcycle", "bicycle"]]
        phone_boxes = [d["box"] for d in detections if d["class"].lower() == "cell phone"]
        traffic_light_boxes = [d["box"] for d in detections if d["class"].lower() == "traffic light"]

        # ─── 1. MOBILE PHONE USE ─────────────────────────────────────────
        phone_violation = False
        if has_cell_phone and has_person:
            for p_box in person_boxes:
                p_height = p_box[3] - p_box[1]
                upper_body = [p_box[0], p_box[1], p_box[2], p_box[1] + int(p_height * 0.6)]
                for ph_box in phone_boxes:
                    if self._get_overlap(upper_body, ph_box) > 0.05:
                        phone_violation = True
                        break
                if phone_violation:
                    break

        if has_cell_phone and (phone_violation or not has_motorcycle):
            violation_type = "MOBILE_PHONE_USE"
            risk_score = 75
            severity = "MEDIUM"
            fine = "$120.00"

        # ─── 2. TRIPLE RIDING ────────────────────────────────────────────
        elif has_motorcycle and len(person_boxes) >= 3:
            for m_box in motorcycle_boxes:
                # Use 20% overlap threshold (stricter to avoid pedestrian false positives)
                overlapping_people = sum(
                    1 for p_box in person_boxes if self._get_overlap(m_box, p_box) > 0.20
                )
                if overlapping_people >= 3:
                    violation_type = "TRIPLE_RIDING"
                    risk_score = 85
                    severity = "HIGH"
                    fine = "$150.00"
                    vehicle_class = "Motorcycle"
                    break

        # ─── 3. HELMET NON-COMPLIANCE ────────────────────────────────────
        # NOTE: YOLO COCO model cannot detect helmets directly.
        # We detect motorcycle + rider and flag as POTENTIAL helmet violation.
        # In production, a custom helmet classifier (fine-tuned YOLO weights)
        # would be used to confirm helmet presence/absence.
        elif has_motorcycle and has_person:
            motorcycle_rider_found = False
            for m_box in motorcycle_boxes:
                for p_box in person_boxes:
                    if self._get_overlap(m_box, p_box) > 0.15:
                        motorcycle_rider_found = True
                        break
                if motorcycle_rider_found:
                    break

            if motorcycle_rider_found:
                # Flag as potential violation — needs helmet classifier confirmation
                violation_type = "HELMET_CHECK_REQUIRED"
                risk_score = 65
                severity = "MEDIUM"
                fine = "$150.00"
                vehicle_class = "Motorcycle"

        # ─── 4. RED LIGHT VIOLATION ──────────────────────────────────────
        elif has_traffic_light and any(
            v in detected_classes for v in ["car", "motorcycle", "bus", "truck"]
        ):
            is_red = False
            for tl_box in traffic_light_boxes:
                x1, y1, x2, y2 = [int(c) for c in tl_box]
                if x2 > x1 and y2 > y1:
                    h, w = enhanced_img.shape[:2]
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w, x2), min(h, y2)
                    crop = enhanced_img[y1:y2, x1:x2]
                    if crop.size > 0:
                        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
                        height = crop.shape[0]
                        top_half = hsv[:int(height * 0.4), :]
                        if top_half.size > 0:
                            mask1 = cv2.inRange(top_half, np.array([0, 70, 70]), np.array([10, 255, 255]))
                            mask2 = cv2.inRange(top_half, np.array([160, 70, 70]), np.array([180, 255, 255]))
                            red_pixels = cv2.countNonZero(mask1) + cv2.countNonZero(mask2)
                            total_pixels = top_half.shape[0] * top_half.shape[1]
                            # Require at least 5% red pixels (not just 3 pixels)
                            if total_pixels > 0 and (red_pixels / total_pixels) > 0.05:
                                is_red = True
                                break

            if is_red:
                violation_type = "RED_LIGHT_VIOLATION"
                risk_score = 92
                severity = "HIGH"
                fine = "$300.00"

        return {
            "violation_type": violation_type,
            "risk_score": risk_score,
            "severity": severity,
            "fine": fine,
            "vehicle": vehicle_class,
            "details": {
                "speed": speed_str,
                "location": location_str,
                "weather": weather_str
            }
        }

    @staticmethod
    def _get_overlap(box1, box2):
        """Calculate overlap ratio between two bounding boxes."""
        x_left = max(box1[0], box2[0])
        y_top = max(box1[1], box2[1])
        x_right = min(box1[2], box2[2])
        y_bottom = min(box1[3], box2[3])
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        inter_area = (x_right - x_left) * (y_bottom - y_top)
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
        if box1_area == 0 or box2_area == 0:
            return 0.0
        return inter_area / min(box1_area, box2_area)

    def _empty_result(self):
        """Return an empty/no-detection result."""
        return {
            "is_real_ai": False,
            "plate": "NONE",
            "ocr_confidence": 0.0,
            "violation_type": "NO_VIOLATION",
            "risk_score": 0,
            "severity": "info",
            "fine": "$0.00",
            "vehicle": "Unknown",
            "detections": [],
            "details": {"speed": None, "location": None, "weather": "unknown"},
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "processing_ms": 0
        }

    def _run_simulated_inference_generic(self):
        """Generic simulated result for live stream frames when AI not available."""
        import random
        scenarios = [
            ("HELMET_NON_COMPLIANCE", 78, "HIGH", "$150.00", "Motorcycle", "MH-12-JN-8832"),
            ("RED_LIGHT_VIOLATION", 92, "HIGH", "$300.00", "Sedan", "KA-51-MD-9041"),
            ("SEATBELT_NON_COMPLIANCE", 64, "MEDIUM", "$120.00", "SUV", "DL-03-CB-5512"),
            ("TRIPLE_RIDING", 85, "HIGH", "$150.00", "Motorcycle", "KA-09-EF-3421"),
            ("NO_VIOLATION", 10, "info", "$0.00", "Sedan", "KA-01-AB-1234"),
        ]
        # 40% chance of no violation, 60% chance of random violation
        if random.random() < 0.4:
            s = scenarios[4]
        else:
            s = random.choice(scenarios[:4])

        return {
            "is_real_ai": False,
            "plate": s[5],
            "ocr_confidence": round(random.uniform(85, 98), 1),
            "violation_type": s[0],
            "risk_score": s[1],
            "severity": s[2],
            "fine": s[3],
            "vehicle": s[4],
            "detections": [
                {"box": [200, 150, 560, 320], "class": s[4], "confidence": round(random.uniform(88, 97), 1)}
            ],
            "details": {
                "speed": f"{random.randint(20, 65)} km/h",
                "location": random.choice(["Sector-4 Crossroads", "Gravel Junction", "Silk Board Junction", "KR Puram Signal"]),
                "weather": random.choice(["Clear", "Foggy", "Rainy", "Overcast"])
            },
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "processing_ms": round(random.uniform(50, 200), 1)
        }

    def _run_simulated_inference(self, filename: str):
        """
        Simulates model output based on filename keywords.
        Only used when AI libraries are NOT installed.
        """
        if "red" in filename or "light" in filename:
            return {
                "is_real_ai": False,
                "plate": "KA-51-MD-9041",
                "ocr_confidence": 90.5,
                "violation_type": "RED_LIGHT_VIOLATION",
                "risk_score": 92,
                "severity": "HIGH",
                "fine": "$300.00",
                "vehicle": "Sedan",
                "detections": [
                    {"box": [200, 150, 560, 320], "class": "Sedan", "confidence": 95.2},
                    {"box": [624, 57, 688, 140], "class": "Traffic Light", "confidence": 98.7}
                ],
                "details": {"speed": "58 km/h", "location": "Gravel Junction", "weather": "Heavy Rain"},
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "processing_ms": 45.2
            }
        elif "seatbelt" in filename or "belt" in filename:
            return {
                "is_real_ai": False,
                "plate": "DL-03-CB-5512",
                "ocr_confidence": 96.5,
                "violation_type": "SEATBELT_NON_COMPLIANCE",
                "risk_score": 64,
                "severity": "MEDIUM",
                "fine": "$120.00",
                "vehicle": "SUV",
                "detections": [
                    {"box": [160, 114, 640, 323], "class": "SUV", "confidence": 97.4},
                    {"box": [384, 152, 496, 220], "class": "Driver", "confidence": 89.2}
                ],
                "details": {"speed": "112 km/h", "location": "Expressway Exit 7", "weather": "Sunny"},
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "processing_ms": 38.7
            }
        elif "parking" in filename:
            return {
                "is_real_ai": False,
                "plate": "TX-99-ER-0043",
                "ocr_confidence": 94.0,
                "violation_type": "ILLEGAL_PARKING",
                "risk_score": 45,
                "severity": "LOW",
                "fine": "$100.00",
                "vehicle": "Delivery Van",
                "detections": [
                    {"box": [180, 120, 580, 340], "class": "Delivery Van", "confidence": 93.1}
                ],
                "details": {"speed": "0 km/h", "location": "Downtown Boulevard", "weather": "Clear"},
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "processing_ms": 42.0
            }
        else:
            # Default helmet violation simulation
            return {
                "is_real_ai": False,
                "plate": "MH-12-JN-8832",
                "ocr_confidence": 94.8,
                "violation_type": "HELMET_NON_COMPLIANCE",
                "risk_score": 78,
                "severity": "HIGH",
                "fine": "$150.00",
                "vehicle": "Motorcycle",
                "detections": [
                    {"box": [240, 133, 560, 342], "class": "Motorcycle", "confidence": 92.4},
                    {"box": [336, 144, 432, 201], "class": "Rider 1", "confidence": 88.5},
                    {"box": [416, 167, 512, 228], "class": "Rider 2 (Violator)", "confidence": 96.1}
                ],
                "details": {"speed": "42 km/h", "location": "Sector-4 Crossroads", "weather": "Foggy"},
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "processing_ms": 51.3
            }


# ─── Module-level singleton ─────────────────────────────────────────────────
# Used by Celery workers and stream processor to avoid re-loading models.
_detector_instance = None

def get_detector() -> TrafficEyeDetector:
    """Returns a singleton TrafficEyeDetector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = TrafficEyeDetector()
    return _detector_instance
