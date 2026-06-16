import os
import re
import uuid
import shutil
import logging
import json
import secrets
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

# Local database and models
from database import engine, get_db, Base
import models
from evidence_generator import generate_citation_json
from model_inference import get_detector

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrafficEyeAPI")

# Initialize database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title="TrafficEye AI Backend",
    description="Intelligent Traffic Violation Detection & Enforcement System API — Real Camera Integration",
    version="4.0.0"
)

# ─────────────────────────────────────────────────────────────────────────────
# CORS — configurable origins (FIX 6)
# ─────────────────────────────────────────────────────────────────────────────
_default_origins = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", _default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# API Key middleware (FIX 7)
# ─────────────────────────────────────────────────────────────────────────────
API_KEY = os.getenv("API_KEY", secrets.token_urlsafe(32))

# Read-only safe methods/paths that don't require auth
_OPEN_METHODS = {"GET", "HEAD", "OPTIONS"}

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """Require X-API-Key header for mutating requests (POST/PUT/DELETE)."""
    if request.method in _OPEN_METHODS:
        return await call_next(request)
    # WebSocket upgrade requests are handled separately
    if request.url.path.startswith("/ws/"):
        return await call_next(request)
    key = request.headers.get("X-API-Key", "")
    if not secrets.compare_digest(key, API_KEY):
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
    return await call_next(request)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _mask_url_password(url: str) -> str:
    """Replace password component in a URL with '***' to avoid leaking credentials."""
    # Matches  ://user:password@  and replaces the password portion
    return re.sub(r'(://[^:]+:)[^@]+(@)', r'\1***\2', url)


# --- Seeding Database ---
def seed_database():
    db = None
    try:
        db = next(get_db())
        # 1. Seed Citations (if empty)
        if db.query(models.Violation).count() == 0:
            logger.info("[TrafficEye AI] Database empty. Seeding violations, vehicles, and analytics...")

            def ensure_vehicle(plate, v_type):
                v = db.query(models.Vehicle).filter_by(plate=plate).first()
                if not v:
                    v = models.Vehicle(plate=plate, type=v_type, last_seen="2026-06-15 13:20")
                    db.add(v)
                    db.commit()
                return v

            seeds = [
                ("TKT-6623", "2026-06-15 08:32", "MH-12-JN-8832", "HELMET_NON_COMPLIANCE", "Motorcycle", 78, "96%", "$150.00", "PENDING_REVIEW"),
                ("TKT-6590", "2026-06-15 10:14", "KA-51-MD-9041", "RED_LIGHT_VIOLATION", "Sedan", 92, "95%", "$300.00", "APPROVED"),
                ("TKT-6541", "2026-06-15 11:45", "DL-03-CB-5512", "SEATBELT_NON_COMPLIANCE", "SUV", 64, "89%", "$120.00", "APPROVED"),
                ("TKT-6430", "2026-06-15 13:20", "TX-99-ER-0043", "ILLEGAL_PARKING", "Delivery Van", 45, "94%", "$100.00", "DISMISSED"),
                ("TKT-6391", "2026-06-14 15:40", "MH-12-JN-8832", "STOP_LINE_VIOLATION", "Motorcycle", 62, "84%", "$80.00", "APPROVED"),
                ("TKT-6302", "2026-06-14 17:15", "DL-01-AA-9999", "WRONG_SIDE_DRIVING", "SUV", 88, "97%", "$250.00", "APPROVED"),
                ("TKT-6298", "2026-06-14 19:42", "KA-51-MD-9041", "TRIPLE_RIDING", "Sedan", 82, "93%", "$150.00", "APPROVED"),
                ("TKT-6112", "2026-06-13 21:05", "MH-12-JN-8832", "HELMET_NON_COMPLIANCE", "Motorcycle", 78, "91%", "$150.00", "APPROVED")
            ]

            for s in seeds:
                ensure_vehicle(s[2], s[4])
                v = models.Violation(
                    id=s[0], timestamp=s[1], plate=s[2], type=s[3],
                    vehicle=s[4], risk_score=s[5], confidence=s[6], fine=s[7], status=s[8]
                )
                db.add(v)
            db.commit()

        # 2. Seed Junctions (Bangalore real locations)
        if db.query(models.Junction).count() == 0:
            logger.info("[TrafficEye AI] Seeding Bangalore junctions...")
            junctions = [
                models.Junction(name="Silk Board Junction", latitude=12.9170, longitude=77.6230, base_risk_score=95),
                models.Junction(name="KR Puram Signal", latitude=13.0012, longitude=77.6870, base_risk_score=91),
                models.Junction(name="Hebbal Flyover", latitude=13.0358, longitude=77.5970, base_risk_score=88),
                models.Junction(name="Marathahalli Bridge", latitude=12.9591, longitude=77.6974, base_risk_score=85),
                models.Junction(name="Electronic City Toll", latitude=12.8456, longitude=77.6603, base_risk_score=78),
                models.Junction(name="Majestic Bus Station", latitude=12.9772, longitude=77.5713, base_risk_score=82),
                models.Junction(name="Tin Factory Junction", latitude=13.0067, longitude=77.6500, base_risk_score=90),
                models.Junction(name="Whitefield Main Road", latitude=12.9698, longitude=77.7500, base_risk_score=75),
            ]
            db.add_all(junctions)
            db.commit()

        # 3. Seed Hotspots
        if db.query(models.Hotspot).count() == 0:
            logger.info("[TrafficEye AI] Seeding Bangalore hotspots...")
            hotspots = [
                models.Hotspot(junction_name="Silk Board Junction", predicted_risk=95, peak_hours="08:00 - 10:30, 17:30 - 20:00", patrol_count=5),
                models.Hotspot(junction_name="KR Puram Signal", predicted_risk=91, peak_hours="08:00 - 10:00, 18:00 - 20:00", patrol_count=4),
                models.Hotspot(junction_name="Hebbal Flyover", predicted_risk=88, peak_hours="07:30 - 09:30, 17:00 - 19:30", patrol_count=3),
                models.Hotspot(junction_name="Marathahalli Bridge", predicted_risk=85, peak_hours="08:30 - 10:30, 17:30 - 19:30", patrol_count=3),
                models.Hotspot(junction_name="Electronic City Toll", predicted_risk=78, peak_hours="08:00 - 10:00, 18:00 - 20:00", patrol_count=2),
                models.Hotspot(junction_name="Majestic Bus Station", predicted_risk=82, peak_hours="07:00 - 09:00, 17:00 - 19:00", patrol_count=3),
                models.Hotspot(junction_name="Tin Factory Junction", predicted_risk=90, peak_hours="08:00 - 10:00, 17:30 - 20:00", patrol_count=4),
                models.Hotspot(junction_name="Whitefield Main Road", predicted_risk=75, peak_hours="09:00 - 11:00, 18:00 - 20:00", patrol_count=2),
            ]
            db.add_all(hotspots)
            db.commit()

        # 4. Seed Predictions
        if db.query(models.Prediction).count() == 0:
            logger.info("[TrafficEye AI] Seeding predictive models...")
            predictions = [
                models.Prediction(junction_name="Silk Board Junction", hour=18, predicted_violations=62.5, recommendation="Deploy 5 officers at Silk Board Junction between 5:30 PM and 8 PM. Focus on helmet and signal violations."),
                models.Prediction(junction_name="KR Puram Signal", hour=8, predicted_violations=48.2, recommendation="Deploy 4 officers at KR Puram between 8 AM and 10 AM. Heavy two-wheeler traffic zone."),
                models.Prediction(junction_name="Hebbal Flyover", hour=17, predicted_violations=35.8, recommendation="Deploy 3 officers at Hebbal Flyover between 5 PM and 7:30 PM. Watch for wrong-side driving."),
                models.Prediction(junction_name="Marathahalli Bridge", hour=9, predicted_violations=30.4, recommendation="Deploy 3 officers at Marathahalli between 8:30 AM and 10:30 AM. IT corridor rush hour."),
                models.Prediction(junction_name="Tin Factory Junction", hour=18, predicted_violations=45.0, recommendation="Deploy 4 officers at Tin Factory between 5:30 PM and 8 PM. Signal violation hotspot."),
            ]
            db.add_all(predictions)
            db.commit()

    except Exception as e:
        logger.error(f"[TrafficEye AI] Error seeding database: {e}")
        if db is not None:
            db.rollback()
    finally:
        if db is not None:
            db.close()

seed_database()

# --- API Endpoints ---

@app.post("/api/analyze")
async def analyze_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Receives an image upload, runs CV model analysis, saves the violation
    to the database, and returns the annotated violation output.
    """
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        detector = get_detector()
        result = detector.run_inference(temp_path)

        plate = result.get("plate", "")
        existing_count = db.query(models.Violation).filter(models.Violation.plate == plate).count()

        offender_status = "First-time Offender"
        if existing_count >= 1:
            offender_status = f"Repeat Offender ({existing_count + 1} Violations)"

        result["offender_status"] = offender_status
        ticket_id = f"TKT-{uuid.uuid4().hex[:4].upper()}"
        result["ticket_id"] = ticket_id
        result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Save vehicle to DB
        vehicle = db.query(models.Vehicle).filter_by(plate=plate).first()
        if not vehicle and plate and plate != "UNREADABLE" and plate != "NONE":
            vehicle = models.Vehicle(plate=plate, type=result.get("vehicle", "Automobile"), last_seen=result["timestamp"])
            db.add(vehicle)
            db.commit()

        # Save violation to DB
        if result.get("violation_type", "NO_VIOLATION") != "NO_VIOLATION":
            try:
                v = models.Violation(
                    id=ticket_id,
                    timestamp=result["timestamp"],
                    plate=plate if plate and plate != "UNREADABLE" else "UNKNOWN",
                    type=result.get("violation_type", "UNKNOWN"),
                    vehicle=result.get("vehicle", "Automobile"),
                    risk_score=result.get("risk_score", 0),
                    confidence=f"{result.get('ocr_confidence', 0)}%",
                    fine=result.get("fine", "$0.00"),
                    status="PENDING_REVIEW"
                )
                db.add(v)
                db.commit()

                # Generate JSON evidence only (PDF disabled)
                details = result.get("details", {})
                citation_info = {
                    "type": v.type, "plate": v.plate, "confidence": v.confidence,
                    "vehicle": v.vehicle, "risk_score": v.risk_score, "timestamp": v.timestamp,
                    "fine": v.fine, "location": details.get("location", "Silk Board Junction"),
                    "speed": details.get("speed", "0 km/h"), "weather": details.get("weather", "Clear")
                }
                try:
                    json_path = generate_citation_json(ticket_id, citation_info)
                    evidence = models.Evidence(
                        id=f"EVD-{uuid.uuid4().hex[:4].upper()}",
                        violation_id=v.id, annotated_image_path="",
                        pdf_path="", metadata_json=json.dumps(citation_info)
                    )
                    db.add(evidence)
                    db.commit()
                except Exception as ev_err:
                    logger.error(f"[TrafficEye AI] Evidence generation error: {ev_err}")

            except Exception as db_err:
                logger.error(f"[TrafficEye AI] DB save error: {db_err}")
                db.rollback()

        return result

    except Exception as e:
        logger.error(f"[TrafficEye AI] API Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/api/citations")
def get_citations(type_filter: str = "ALL", status_filter: str = "ALL", query: str = "", db: Session = Depends(get_db)):
    """Retrieves list of citations, supporting type and status filtering + plate search queries."""
    q = db.query(models.Violation)

    if type_filter != "ALL":
        q = q.filter(models.Violation.type == type_filter)
    if status_filter != "ALL":
        q = q.filter(models.Violation.status == status_filter)
    if query:
        q = q.filter(models.Violation.plate.like(f"%{query}%"))

    violations = q.order_by(models.Violation.timestamp.desc()).all()

    return [
        {
            "id": v.id,
            "timestamp": v.timestamp,
            "plate": v.plate,
            "type": v.type,
            "vehicle": v.vehicle,
            "risk_score": v.risk_score,
            "confidence": v.confidence,
            "fine": v.fine,
            "status": v.status
        }
        for v in violations
    ]


@app.post("/api/citations")
def create_citation(data: dict, db: Session = Depends(get_db)):
    """Inserts a verified traffic violation citation ticket into database."""
    plate = data.get("plate", "")
    vehicle = db.query(models.Vehicle).filter_by(plate=plate).first()
    if not vehicle:
        vehicle = models.Vehicle(plate=plate, type=data.get("vehicle", "Automobile"), last_seen=data.get("timestamp"))
        db.add(vehicle)
        db.commit()

    ticket_id = f"TKT-{uuid.uuid4().hex[:4].upper()}"
    v = models.Violation(
        id=ticket_id,
        timestamp=data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M")),
        plate=plate,
        type=data.get("type", "HELMET_NON_COMPLIANCE"),
        vehicle=data.get("vehicle", "Automobile"),
        risk_score=data.get("risk_score", 50),
        confidence=data.get("confidence", "90%"),
        fine=data.get("fine", "$150.00"),
        status=data.get("status", "APPROVED")
    )
    db.add(v)
    db.commit()

    # Generate JSON evidence only (PDF disabled)
    try:
        details = data.get("details", {})
        if not details:
            details = {
                "location": "Silk Board Junction",
                "speed": "42 km/h",
                "weather": "Clear"
            }
        citation_info = {
            "type": v.type, "plate": v.plate, "confidence": v.confidence,
            "vehicle": v.vehicle, "risk_score": v.risk_score, "timestamp": v.timestamp,
            "fine": v.fine, "location": details.get("location", "Silk Board Junction"),
            "speed": details.get("speed", "42 km/h"), "weather": details.get("weather", "Clear")
        }
        json_path = generate_citation_json(ticket_id, citation_info)

        evidence = models.Evidence(
            id=f"EVD-{uuid.uuid4().hex[:4].upper()}",
            violation_id=v.id,
            annotated_image_path="",
            pdf_path="",
            metadata_json=json.dumps(citation_info)
        )
        db.add(evidence)
        db.commit()
    except Exception as e:
        logger.error(f"[TrafficEye AI] Error generating evidence files: {e}")

    return {
        "id": v.id,
        "timestamp": v.timestamp,
        "plate": v.plate,
        "type": v.type,
        "vehicle": v.vehicle,
        "risk_score": v.risk_score,
        "confidence": v.confidence,
        "fine": v.fine,
        "status": v.status
    }


@app.put("/api/citations/{ticket_id}")
def update_citation_status(ticket_id: str, payload: dict, db: Session = Depends(get_db)):
    """Modifies the status (APPROVED, PENDING_REVIEW, DISMISSED) of a ticket."""
    v = db.query(models.Violation).filter_by(id=ticket_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Citation not found")

    v.status = payload.get("status", v.status)
    db.commit()

    return {
        "id": v.id,
        "timestamp": v.timestamp,
        "plate": v.plate,
        "type": v.type,
        "vehicle": v.vehicle,
        "risk_score": v.risk_score,
        "confidence": v.confidence,
        "fine": v.fine,
        "status": v.status
    }


@app.delete("/api/citations/{ticket_id}")
def delete_citation(ticket_id: str, db: Session = Depends(get_db)):
    """Removes a citation log from enforcement database."""
    v = db.query(models.Violation).filter_by(id=ticket_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Citation not found")

    db.delete(v)
    db.commit()
    return {"message": f"Citation {ticket_id} deleted successfully"}


@app.get("/api/repeat-offenders")
def get_repeat_offenders(db: Session = Depends(get_db)):
    """Aggregates top repeat offender profiles based on plate counts."""
    results = db.query(
        models.Violation.plate,
        func.count(models.Violation.id).label("count"),
        func.max(models.Violation.vehicle).label("vehicle"),
        func.avg(models.Violation.risk_score).label("avg_risk")
    ).group_by(models.Violation.plate).having(func.count(models.Violation.id) >= 2).order_by(func.count(models.Violation.id).desc()).all()

    return [
        {
            "plate": r[0],
            "violations_count": r[1],
            "vehicle": r[2],
            "avg_risk": round(r[3], 1)
        }
        for r in results
    ]


@app.get("/api/hotspots")
def get_hotspots(db: Session = Depends(get_db)):
    """Returns predictive violation hotspots mapping details."""
    hotspots = db.query(models.Hotspot).all()
    junctions = {j.name: j for j in db.query(models.Junction).all()}

    res = []
    for h in hotspots:
        j = junctions.get(h.junction_name)
        res.append({
            "name": h.junction_name,
            "risk": h.predicted_risk,
            "peak": h.peak_hours,
            "patrol": f"{h.patrol_count} Patrol Officers" if h.patrol_count > 1 else "1 Curb Officer",
            "lat": j.latitude if j else 12.9716,
            "lng": j.longitude if j else 77.5946
        })
    return res


@app.get("/api/predictions")
def get_predictions(db: Session = Depends(get_db)):
    """Returns spatial predictions and officer deployment recommendations."""
    preds = db.query(models.Prediction).all()
    return [
        {
            "id": p.id,
            "junction": p.junction_name,
            "hour": p.hour,
            "predicted_violations": p.predicted_violations,
            "recommendation": p.recommendation
        }
        for p in preds
    ]


@app.get("/api/citations/{ticket_id}/json")
def get_citation_json(ticket_id: str):
    """Serves the generated JSON metadata file."""
    json_path = os.path.join("evidence_pdfs", f"{ticket_id}.json")
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="JSON evidence not found for this citation")
    return FileResponse(json_path, media_type="application/json", filename=f"{ticket_id}.json")


# ─────────────────────────────────────────────────────────────────────────────
# REAL-WORLD CAMERA REGISTRY ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/cameras")
async def list_cameras(category: str = None, country: str = None):
    """List all registered traffic cameras, optionally filtered by category or country."""
    from camera_registry import get_camera_registry
    registry = get_camera_registry()
    cameras = registry.list_all(category=category, country=country)
    return {
        "total": len(cameras),
        "categories": registry.list_categories(),
        "cameras": cameras
    }


@app.get("/api/cameras/{camera_id}")
async def get_camera(camera_id: str):
    """Get details of a specific camera."""
    from camera_registry import get_camera_registry
    registry = get_camera_registry()
    cam = registry.get(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cam


@app.post("/api/cameras")
async def add_custom_camera(data: dict):
    """
    Add a custom camera to the registry.
    Body: {name, url, stream_type, region, country, lat, lng}
    """
    from camera_registry import get_camera_registry
    registry = get_camera_registry()
    cam = registry.add_custom(data)
    return {"status": "added", "camera": cam}


@app.delete("/api/cameras/{camera_id}")
async def remove_camera(camera_id: str):
    """Remove a camera from the registry."""
    from camera_registry import get_camera_registry
    registry = get_camera_registry()
    if registry.remove(camera_id):
        return {"status": "removed", "camera_id": camera_id}
    raise HTTPException(status_code=404, detail="Camera not found")


@app.get("/api/cameras/{camera_id}/health")
async def check_camera_health(camera_id: str):
    """Check if a camera feed is reachable and responsive."""
    from camera_registry import get_camera_registry
    registry = get_camera_registry()
    result = registry.check_health(camera_id)
    return {"camera_id": camera_id, **result}


@app.post("/api/cameras/{camera_id}/resolve")
async def resolve_camera_url(camera_id: str, params: dict = None):
    """
    Resolve a template camera URL with provided credentials.
    Body: {camera_ip: "192.168.1.100", username: "admin", password: "pass"}
    """
    from camera_registry import get_camera_registry
    registry = get_camera_registry()
    if params is None:
        params = {}
    url = registry.resolve_url(camera_id, params)
    if url is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"camera_id": camera_id, "resolved_url": _mask_url_password(url)}


# ─────────────────────────────────────────────────────────────────────────────
# LIVE CAMERA STREAM ENDPOINTS (Single Stream)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/stream/start")
async def start_stream(payload: dict):
    """
    Start processing a live camera stream.

    Body:
        {
            "url": "http://...",          // Direct URL
            "camera_id": "us-mn-i35w",    // OR use a registry camera ID
            "camera_params": {},           // For template cameras: {camera_ip, username, password}
            "type": "auto",
            "fps": 2.0
        }
    """
    from stream_processor import get_stream_manager
    from camera_registry import get_camera_registry

    url = payload.get("url", "")
    camera_id = payload.get("camera_id")
    camera_params = payload.get("camera_params", {})
    stream_type = payload.get("type", "auto")
    fps = payload.get("fps", 2.0)
    camera_name = None

    # Resolve URL from camera registry if camera_id provided
    if camera_id and not url:
        registry = get_camera_registry()
        cam = registry.get(camera_id)
        if not cam:
            raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found in registry")

        camera_name = cam.get("name", camera_id)
        url = registry.resolve_url(camera_id, camera_params)
        if not url:
            raise HTTPException(status_code=400, detail="Camera requires configuration params (camera_ip, username, password)")

        # For API-type cameras (e.g. Singapore LTA), treat as snapshot
        cam_stream_type = cam.get("stream_type", "auto")
        if stream_type == "auto":
            stream_type = "snapshot" if cam_stream_type == "api" else cam_stream_type

    if not url:
        raise HTTPException(status_code=400, detail="Stream URL or camera_id is required")

    try:
        def on_stream_violation(result):
            if result.get("violation_type", "NO_VIOLATION") == "NO_VIOLATION":
                return
            db = None
            try:
                db = next(get_db())
                plate = result.get("plate", "UNKNOWN")

                if plate and plate not in ["UNREADABLE", "NONE", "UNKNOWN"]:
                    vehicle = db.query(models.Vehicle).filter_by(plate=plate).first()
                    if not vehicle:
                        vehicle = models.Vehicle(
                            plate=plate,
                            type=result.get("vehicle", "Automobile"),
                            last_seen=datetime.now().strftime("%Y-%m-%d %H:%M")
                        )
                        db.add(vehicle)
                        db.commit()

                ticket_id = f"TKT-{uuid.uuid4().hex[:4].upper()}"
                v = models.Violation(
                    id=ticket_id,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    plate=plate,
                    type=result.get("violation_type"),
                    vehicle=result.get("vehicle", "Automobile"),
                    risk_score=result.get("risk_score", 0),
                    confidence=f"{result.get('ocr_confidence', 0)}%",
                    fine=result.get("fine", "$0.00"),
                    status="PENDING_REVIEW"
                )
                db.add(v)
                db.commit()

                # Save evidence with snapshot path
                try:
                    evidence = models.Evidence(
                        id=f"EVD-{uuid.uuid4().hex[:4].upper()}",
                        violation_id=v.id,
                        annotated_image_path=result.get("snapshot_path", ""),
                        pdf_path="",
                        metadata_json=json.dumps({
                            "type": v.type, "plate": v.plate,
                            "risk_score": v.risk_score, "timestamp": v.timestamp,
                            "camera_id": result.get("camera_id"),
                        })
                    )
                    db.add(evidence)
                    db.commit()
                except Exception as ev_err:
                    logger.error(f"[StreamManager] Evidence save error: {ev_err}")

            except Exception as e:
                logger.error(f"[StreamManager] DB save error: {e}")
                if db is not None:
                    db.rollback()
            finally:
                if db is not None:
                    db.close()

        manager = get_stream_manager(
            detector=get_detector(),
            on_result=on_stream_violation
        )
        manager.target_fps = fps
        manager.start(url, stream_type, camera_id=camera_id, camera_name=camera_name)

        return {
            "status": "started",
            "message": f"Stream connected: {camera_name or url}",
            "stream_type": manager._stream_type,
            "target_fps": fps,
            "camera_id": camera_id,
            "camera_name": camera_name,
        }
    except ConnectionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stream/stop")
async def stop_stream():
    """Stop the currently running live camera stream."""
    from stream_processor import get_stream_manager
    manager = get_stream_manager()
    if not manager.is_running:
        return {"status": "not_running", "message": "No active stream to stop"}

    manager.stop()
    return {"status": "stopped", "message": "Stream stopped successfully"}


@app.get("/api/stream/status")
async def stream_status():
    """Get the current status of the live camera stream processor."""
    from stream_processor import get_stream_manager
    manager = get_stream_manager()
    return manager.status


# ─────────────────────────────────────────────────────────────────────────────
# MULTI-CAMERA STREAM ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/multi-stream/start")
async def start_multi_stream(payload: dict):
    """
    Start a camera stream in multi-camera mode.

    Body:
        {
            "camera_id": "us-mn-i35w",       // Registry camera ID
            "url": "http://...",               // OR direct URL
            "camera_params": {},               // For template cameras
            "fps": 1.0,
            "name": "Optional display name"
        }
    """
    from stream_processor import get_multi_stream_manager
    from camera_registry import get_camera_registry

    url = payload.get("url", "")
    camera_id = payload.get("camera_id", f"custom-{int(datetime.now().timestamp())}")
    camera_params = payload.get("camera_params", {})
    stream_type = payload.get("type", "auto")
    fps = payload.get("fps", 1.0)
    camera_name = payload.get("name")

    # Resolve from registry
    if payload.get("camera_id") and not url:
        registry = get_camera_registry()
        cam = registry.get(camera_id)
        if not cam:
            raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")
        camera_name = camera_name or cam.get("name", camera_id)
        url = registry.resolve_url(camera_id, camera_params)
        if not url:
            raise HTTPException(status_code=400, detail="Camera requires configuration params")
        cam_stream_type = cam.get("stream_type", "auto")
        if stream_type == "auto":
            stream_type = "snapshot" if cam_stream_type == "api" else cam_stream_type

    if not url:
        raise HTTPException(status_code=400, detail="URL or camera_id required")

    def on_violation(result):
        if result.get("violation_type", "NO_VIOLATION") == "NO_VIOLATION":
            return
        db = None
        try:
            db = next(get_db())
            plate = result.get("plate", "UNKNOWN")
            if plate and plate not in ["UNREADABLE", "NONE", "UNKNOWN"]:
                vehicle = db.query(models.Vehicle).filter_by(plate=plate).first()
                if not vehicle:
                    vehicle = models.Vehicle(plate=plate, type=result.get("vehicle", "Automobile"),
                                             last_seen=datetime.now().strftime("%Y-%m-%d %H:%M"))
                    db.add(vehicle)
                    db.commit()
            ticket_id = f"TKT-{uuid.uuid4().hex[:4].upper()}"
            v = models.Violation(
                id=ticket_id, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
                plate=plate, type=result.get("violation_type"),
                vehicle=result.get("vehicle", "Automobile"),
                risk_score=result.get("risk_score", 0),
                confidence=f"{result.get('ocr_confidence', 0)}%",
                fine=result.get("fine", "$0.00"), status="PENDING_REVIEW"
            )
            db.add(v)
            db.commit()

            # Save evidence with snapshot path
            try:
                evidence = models.Evidence(
                    id=f"EVD-{uuid.uuid4().hex[:4].upper()}",
                    violation_id=v.id,
                    annotated_image_path=result.get("snapshot_path", ""),
                    pdf_path="",
                    metadata_json=json.dumps({
                        "type": v.type, "plate": v.plate,
                        "risk_score": v.risk_score, "timestamp": v.timestamp,
                        "camera_id": result.get("camera_id"),
                    })
                )
                db.add(evidence)
                db.commit()
            except Exception as ev_err:
                logger.error(f"[MultiStream] Evidence save error: {ev_err}")

        except Exception as e:
            logger.error(f"[MultiStream] DB save error: {e}")
            if db is not None:
                db.rollback()
        finally:
            if db is not None:
                db.close()

    msm = get_multi_stream_manager(detector=get_detector(), on_result=on_violation)
    result = msm.start_camera(camera_id, url, stream_type, camera_name, fps)
    return result


@app.post("/api/multi-stream/stop/{camera_id}")
async def stop_multi_stream(camera_id: str):
    """Stop a specific camera in multi-stream mode."""
    from stream_processor import get_multi_stream_manager
    msm = get_multi_stream_manager()
    return msm.stop_camera(camera_id)


@app.post("/api/multi-stream/stop-all")
async def stop_all_streams():
    """Stop all active camera streams."""
    from stream_processor import get_multi_stream_manager
    msm = get_multi_stream_manager()
    msm.stop_all()
    return {"status": "all_stopped"}


@app.get("/api/multi-stream/status")
async def multi_stream_status():
    """Get status of all active camera streams."""
    from stream_processor import get_multi_stream_manager
    msm = get_multi_stream_manager()
    return msm.get_status()


# ─────────────────────────────────────────────────────────────────────────────
# WEBSOCKET ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time violation push notifications.
    Frontend connects here to receive live detection results.
    """
    from stream_processor import get_stream_manager

    await websocket.accept()
    manager = get_stream_manager()

    # Pass the running asyncio event loop to the stream manager so background
    # threads can schedule coroutines (WebSocket sends) safely.
    loop = asyncio.get_running_loop()
    manager.set_event_loop(loop)

    manager.add_ws_client(websocket)
    logger.info("[WebSocket] Client connected for stream results")

    try:
        while True:
            data = await websocket.receive_text()
            if data:
                try:
                    msg = json.loads(data)
                    if msg.get("action") == "ping":
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "stats": manager.status
                        }))
                    elif msg.get("action") == "status":
                        await websocket.send_text(json.dumps({
                            "type": "status",
                            "data": manager.status
                        }))
                except json.JSONDecodeError:
                    pass
    except WebSocketDisconnect:
        manager.remove_ws_client(websocket)
        logger.info("[WebSocket] Client disconnected")
    except Exception as e:
        manager.remove_ws_client(websocket)
        logger.error(f"[WebSocket] Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# LIVE CAMERA PRESETS (expanded with real-world cameras)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/stream/presets")
async def get_stream_presets():
    """Returns preset camera feed configurations for quick connection."""
    return {
        "presets": [
            {
                "name": "Singapore PIE Expressway (Live)",
                "description": "Singapore LTA traffic camera on PIE near Jurong",
                "camera_id": "sg-cam-2705",
                "type": "snapshot",
                "requires_config": False,
                "instructions": ["Click Connect — live Singapore LTA feed via API"]
            },
            {
                "name": "Singapore Marina Coastal (Live)",
                "description": "Singapore LTA camera on Marina Coastal Expressway",
                "camera_id": "sg-cam-1501",
                "type": "snapshot",
                "requires_config": False,
                "instructions": ["Click Connect — live Singapore Marina Bay camera"]
            },
            {
                "name": "Singapore CTE (Live)",
                "description": "Singapore LTA Central Expressway camera",
                "camera_id": "sg-cam-1005",
                "type": "snapshot",
                "requires_config": False,
                "instructions": ["Click Connect — live Singapore CTE camera"]
            },
            {
                "name": "TfL London A2 Old Kent Road (Live)",
                "description": "Transport for London JamCam on A2",
                "camera_id": "uk-tfl-a2-old-kent",
                "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.07400.jpg",
                "type": "snapshot",
                "requires_config": False,
                "instructions": ["Click Connect — live TfL JamCam"]
            },
            {
                "name": "TfL London Park Lane (Live)",
                "description": "TfL JamCam near Marble Arch, Westminster",
                "camera_id": "uk-tfl-park-lane",
                "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.08000.jpg",
                "type": "snapshot",
                "requires_config": False,
                "instructions": ["Click Connect — live London Park Lane camera"]
            },
            {
                "name": "TfL London Brixton Road (Live)",
                "description": "TfL JamCam on Brixton Road, Lambeth",
                "camera_id": "uk-tfl-brixton",
                "url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.02500.jpg",
                "type": "snapshot",
                "requires_config": False,
                "instructions": ["Click Connect — live TfL Brixton camera"]
            },
            {
                "name": "Bangalore Silk Board (Configure)",
                "description": "Connect to Silk Board Junction BTP camera via RTSP",
                "camera_id": "blr-silk-board",
                "type": "rtsp",
                "requires_config": True,
                "instructions": [
                    "Obtain the camera IP from BTP/NHAI control room",
                    "Enter credentials in the camera_params field",
                    "Start stream via /api/stream/start with camera_id"
                ]
            },
            {
                "name": "Phone Camera (IP Webcam)",
                "description": "Use your Android phone as a live traffic camera",
                "url_template": "http://{phone_ip}:8080/video",
                "type": "mjpeg",
                "requires_config": True,
                "instructions": [
                    "Install 'IP Webcam' from Google Play Store",
                    "Open the app and Start Server",
                    "Replace {phone_ip} with your phone's IP"
                ]
            },
            {
                "name": "Hikvision RTSP Camera",
                "description": "Connect to any Hikvision IP camera (used in Indian traffic systems)",
                "camera_id": "tpl-hikvision",
                "type": "rtsp",
                "requires_config": True,
                "instructions": [
                    "Enter the camera IP, username, and password",
                    "Common in BTP and NHAI camera networks"
                ]
            },
            {
                "name": "Laptop Webcam",
                "description": "Use your built-in or USB webcam",
                "url": "0",
                "type": "webcam",
                "requires_config": False,
                "instructions": ["Click Connect to activate your webcam"]
            },
            {
                "name": "Sample Video (Loop)",
                "description": "Test with a local traffic video file",
                "url_template": "/path/to/traffic_video.mp4",
                "type": "file",
                "requires_config": True,
                "instructions": ["Enter the full path to a video file"]
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    logger.info(f"[TrafficEye AI] API Key for mutating requests: {API_KEY}")
    logger.info(f"[TrafficEye AI] CORS origins: {CORS_ORIGINS}")
    uvicorn.run(app, host="127.0.0.1", port=8000)
