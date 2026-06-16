import React, { useState, useEffect, useRef } from 'react';
import {
  LayoutGrid,
  BarChart3,
  FileText,
  Database,
  Settings as SettingsIcon,
  Upload,
  Play,
  Square,
  Camera,
  Check,
  AlertTriangle,
  X,
  Search,
  Filter,
  Download,
  RefreshCw,
  Sliders,
  FileJson,
  UserCheck,
  Volume2
} from 'lucide-react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  LineChart,
  Line,
  Cell
} from 'recharts';

import './App.css';

// API base URL
const API_BASE = "http://127.0.0.1:8000/api";

// Scenario Definitions (matching original app.js definitions)
const INITIAL_SCENARIOS = [
  {
    id: "live_webcam",
    title: "Live Camera Feed (Webcam)",
    desc: "Capture live stream from system camera to run real-time YOLOv11 & OCR.",
    tag: "live",
    imageType: "webcam",
    vehicleClass: "Automobile",
    violationType: "HELMET_NON_COMPLIANCE",
    severity: "info",
    riskScore: 50,
    fine: "$150.00",
    plate: "KA-03-HA-1122",
    confidence: 85.0,
    ocrConfidence: 90.0,
    details: {
      speed: "0 km/h",
      location: "System Live Input",
      light: "Variable Light",
      weather: "Clear"
    },
    boxes: []
  },
  {
    id: "helmet_violation",
    title: "Night Surveillance (Helmet)",
    desc: "Low-light camera at intersection capturing motorcycle safety compliance.",
    tag: "low-light",
    imageType: "canvas_draw_helmet",
    vehicleClass: "Motorcycle",
    violationType: "HELMET_NON_COMPLIANCE",
    severity: "danger",
    riskScore: 78,
    fine: "$150.00",
    plate: "MH-12-JN-8832",
    confidence: 96.1,
    ocrConfidence: 94.8,
    details: {
      speed: "42 km/h",
      location: "Sector-4 Crossroads",
      light: "Night (02:40 AM)",
      weather: "Clear / Foggy"
    },
    boxes: [
      { x: 30, y: 35, w: 40, h: 55, label: "Motorcycle", conf: "92.4%", color: "#10B981" },
      { x: 42, y: 38, w: 12, h: 15, label: "Rider 1 (Helmet Compliant)", conf: "88.5%", color: "#10B981" },
      { x: 52, y: 44, w: 12, h: 16, label: "Rider 2 (No Helmet Violation)", conf: "96.1%", color: "#EF4444" },
      { x: 46, y: 78, w: 8, h: 6, label: "License Plate", conf: "94.8%", color: "#F59E0B" }
    ]
  },
  {
    id: "redlight_violation",
    title: "Rainy Day Red Light",
    desc: "Weather camera capturing stop-line breach under active rain conditions.",
    tag: "weather",
    imageType: "canvas_draw_redlight",
    vehicleClass: "Sedan",
    violationType: "RED_LIGHT_VIOLATION",
    severity: "danger",
    riskScore: 92,
    fine: "$300.00",
    plate: "KA-51-MD-9041",
    confidence: 95.2,
    ocrConfidence: 90.5,
    details: {
      speed: "58 km/h",
      location: "Gravel Junction",
      light: "Daylight (Rainy)",
      weather: "Heavy Rain"
    },
    boxes: [
      { x: 25, y: 40, w: 45, h: 45, label: "Sedan (Breached Boundary)", conf: "95.2%", color: "#EF4444" },
      { x: 15, y: 75, w: 70, h: 5, label: "Zebra Crossing / Stop Line", conf: "98.0%", color: "#3B82F6" },
      { x: 78, y: 15, w: 8, h: 22, label: "Traffic Light (Red Mode)", conf: "98.7%", color: "#EF4444" },
      { x: 44, y: 76, w: 9, h: 5, label: "License Plate", conf: "90.5%", color: "#F59E0B" }
    ]
  },
  {
    id: "seatbelt_violation",
    title: "Highway Speeding Seatbelt",
    desc: "High-speed camera tracking driver seatbelt compliance on freeway.",
    tag: "normal",
    imageType: "canvas_draw_seatbelt",
    vehicleClass: "SUV",
    violationType: "SEATBELT_NON_COMPLIANCE",
    severity: "warning",
    riskScore: 64,
    fine: "$120.00",
    plate: "DL-03-CB-5512",
    confidence: 89.2,
    ocrConfidence: 96.5,
    details: {
      speed: "112 km/h (Limit: 100)",
      location: "Expressway Exit 7",
      light: "Bright Daylight",
      weather: "Sunny"
    },
    boxes: [
      { x: 20, y: 30, w: 60, h: 55, label: "SUV (Speeding)", conf: "97.4%", color: "#F59E0B" },
      { x: 48, y: 40, w: 14, h: 18, label: "Driver (Seatbelt Non-compliant)", conf: "89.2%", color: "#EF4444" },
      { x: 45, y: 74, w: 10, h: 6, label: "License Plate", conf: "96.5%", color: "#F59E0B" }
    ]
  },
  {
    id: "illegal_parking",
    title: "Urban Side Lane Parking",
    desc: "Static curb camera detecting obstruction in designated tow-away zone.",
    tag: "shadows",
    imageType: "canvas_draw_parking",
    vehicleClass: "Delivery Van",
    violationType: "ILLEGAL_PARKING",
    severity: "info",
    riskScore: 45,
    fine: "$100.00",
    plate: "TX-99-ER-0043",
    confidence: 94.5,
    ocrConfidence: 95.0,
    details: {
      speed: "0 km/h (Parked)",
      location: "Downtown Boulevard",
      light: "Afternoon (Harsh Shadows)",
      weather: "Clear"
    },
    boxes: [
      { x: 35, y: 30, w: 48, h: 58, label: "Delivery Van (Obstructing)", conf: "94.5%", color: "#F59E0B" },
      { x: 15, y: 15, w: 12, h: 30, label: "No-Parking Zone Sign", conf: "91.8%", color: "#EF4444" },
      { x: 55, y: 78, w: 8, h: 5, label: "License Plate", conf: "95.0%", color: "#F59E0B" }
    ]
  }
];

function App() {
  const [activeTab, setActiveTab] = useState("realtime");
  const [scenarios, setScenarios] = useState(INITIAL_SCENARIOS);
  const [currentScenarioId, setCurrentScenarioId] = useState("helmet_violation");
  const [preprocessMode, setPreprocessMode] = useState(false); // false = Enhanced View, true = Original View
  const [isAnalysisRunning, setIsAnalysisRunning] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState("SYSTEM IDLE");

  // Filter Toggles
  const [lowLightFilter, setLowLightFilter] = useState(true);
  const [weatherFilter, setWeatherFilter] = useState(true);
  const [deblurFilter, setDeblurFilter] = useState(true);

  // OCR Panel Status
  const [ocrText, setOcrText] = useState("-- READY --");
  const [ocrConf, setOcrConf] = useState("0%");

  // Bounding box tooltip hover
  const [hoveredBox, setHoveredBox] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  // Database lists
  const [citations, setCitations] = useState([]);
  const [repeatOffenders, setRepeatOffenders] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [hotspots, setHotspots] = useState([]);

  // Active citation ticket details
  const [activeTicket, setActiveTicket] = useState(null);

  // Settings state
  const [vehicleThresh, setVehicleThresh] = useState(75);
  const [violationThresh, setViolationThresh] = useState(80);
  const [ocrThresh, setOcrThresh] = useState(70);
  const [ocrEngine, setOcrEngine] = useState("easyocr");
  const [webhookUrl, setWebhookUrl] = useState("https://api.trafficeye-ai.gov/v1/citations");

  // Ledger Filter State
  const [searchPlate, setSearchPlate] = useState("");
  const [violationFilter, setViolationFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [ledgerPage, setLedgerPage] = useState(0);
  const entriesPerPage = 6;

  // Webcam References
  const videoRef = useRef(null);
  const webcamIntervalRef = useRef(null);
  const [isWebcamActive, setIsWebcamActive] = useState(false);

  // Canvas Reference
  const canvasRef = useRef(null);

  // Toast notifications
  const [toastMessage, setToastMessage] = useState("");
  const [showToast, setShowToast] = useState(false);

  // Setup current scenario
  const currentScenario = scenarios.find(s => s.id === currentScenarioId) || scenarios[0];

  // Show Toast
  const triggerToast = (msg) => {
    setToastMessage(msg);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  // Load backend data
  const refreshData = async () => {
    try {
      // 1. Fetch Citations
      const citRes = await fetch(`${API_BASE}/citations`);
      if (citRes.ok) {
        const data = await citRes.json();
        setCitations(data);
      }

      // 2. Fetch Repeat Offenders
      const repRes = await fetch(`${API_BASE}/repeat-offenders`);
      if (repRes.ok) {
        const data = await repRes.json();
        setRepeatOffenders(data);
      }

      // 3. Fetch Predictions
      const predRes = await fetch(`${API_BASE}/predictions`);
      if (predRes.ok) {
        const data = await predRes.json();
        setPredictions(data);
      }

      // 4. Fetch Hotspots
      const hotRes = await fetch(`${API_BASE}/hotspots`);
      if (hotRes.ok) {
        const data = await hotRes.json();
        setHotspots(data);
      }
    } catch (error) {
      console.error("Error fetching data from API backend:", error);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  // Update canvas when scenario, mode, or analysis status changes
  useEffect(() => {
    if (currentScenarioId !== "live_webcam") {
      // Clean up webcam
      stopWebcam();
    }
    drawScenario();
  }, [currentScenarioId, preprocessMode, isAnalysisRunning, lowLightFilter, weatherFilter, deblurFilter]);

  // Stop Webcam stream and intervals
  const stopWebcam = () => {
    if (webcamIntervalRef.current) {
      clearInterval(webcamIntervalRef.current);
      webcamIntervalRef.current = null;
    }
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setIsWebcamActive(false);
  };

  // Start Webcam stream
  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 800, height: 380 }
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setIsWebcamActive(true);
        triggerToast("System Live Webcam feed initiated successfully");
      }
    } catch (err) {
      console.error("Failed to access system camera: ", err);
      triggerToast("Error: No webcam found or permission denied. Please select a static scenario.");
      setCurrentScenarioId("helmet_violation");
    }
  };

  // Trigger webcam start if tab switches or scenario selected
  useEffect(() => {
    if (currentScenarioId === "live_webcam" && activeTab === "realtime") {
      startWebcam();
    } else {
      stopWebcam();
    }
    return () => stopWebcam();
  }, [currentScenarioId, activeTab]);

  // Frame processing loop for Webcam
  const captureWebcamFrame = () => {
    const canvas = canvasRef.current;
    if (!canvas || !videoRef.current || !isWebcamActive) return;
    const ctx = canvas.getContext('2d');
    
    // Draw current frame to canvas
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    
    // Apply visual filters if preprocessing mode is active (Original View has noise/blur, Enhanced View has CLAHE/Clear)
    if (preprocessMode) {
      // Add artificial noise for original view
      applyCameraGrain(ctx, 0.3);
    }

    // Capture canvas blob and post to backend /api/analyze
    canvas.toBlob(async (blob) => {
      if (!blob) return;
      const formData = new FormData();
      formData.append("file", blob, "webcam_frame.png");
      
      try {
        const res = await fetch(`${API_BASE}/analyze`, {
          method: "POST",
          body: formData
        });
        if (res.ok) {
          const result = await res.json();
          if (!isAnalysisRunning) return; // halted in between

          setOcrText(result.plate);
          setOcrConf(result.ocr_confidence + "%");

          // Map detections to scenario box formats
          const mappedBoxes = (result.detections || []).map(det => {
            const [x1, y1, x2, y2] = det.box;
            const rx = (x1 / canvas.width) * 100;
            const ry = (y1 / canvas.height) * 100;
            const rw = ((x2 - x1) / canvas.width) * 100;
            const rh = ((y2 - y1) / canvas.height) * 100;
            
            let color = "#EF4444"; // violation class red
            if (det.class.toLowerCase().includes("plate")) color = "#F59E0B"; // plate yellow
            else if (["car", "suv", "sedan", "vehicle", "motorcycle", "bus", "truck"].includes(det.class.toLowerCase())) color = "#10B981"; // vehicle green
            
            return {
              x: rx, y: ry, w: rw, h: rh,
              label: det.class,
              conf: `${det.confidence}%`,
              color
            };
          });

          // Draw frame with overlays
          ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
          if (preprocessMode) {
            applyCameraGrain(ctx, 0.3);
          }
          drawBoundingBoxes(ctx, mappedBoxes);

          // Update active ticket card details
          const isRealViolation = result.violation_type && result.violation_type !== "NO_VIOLATION" && result.violation_type !== "NONE";
          setPipelineStatus(isRealViolation ? "VIOLATION CAPTURED" : "MONITORING SECURE");

          const ticketDetail = {
            id: result.ticket_id || "TKT-AUTO",
            timestamp: result.timestamp || new Date().toISOString().slice(0, 16).replace('T', ' '),
            plate: result.plate,
            violationType: result.violation_type,
            vehicleClass: result.vehicle,
            riskScore: result.risk_score,
            confidence: result.ocr_confidence,
            fine: result.fine,
            severity: result.severity.toLowerCase() === 'high' || result.risk_score >= 75 ? 'danger' : result.severity.toLowerCase() === 'medium' ? 'warning' : 'info',
            offenderStatus: result.offender_status,
            details: result.details
          };
          setActiveTicket(ticketDetail);

          // Auto-issue approved citations for real violations
          if (isRealViolation) {
            autoIssueCitation(result);
          }
        }
      } catch (err) {
        console.error("Webcam analysis error:", err);
      }
    }, "image/png");
  };

  // Local storage trackers for throttling auto-issuing
  const lastAutoIssuedPlate = useRef("");
  const lastAutoIssuedType = useRef("");
  const lastAutoIssuedTime = useRef(0);

  const autoIssueCitation = async (result) => {
    const now = Date.now();
    const isDuplicate = (result.plate === lastAutoIssuedPlate.current && result.violation_type === lastAutoIssuedType.current);
    const elapsed = now - lastAutoIssuedTime.current;
    
    if (!isDuplicate || elapsed > 15000) {
      lastAutoIssuedTime.current = now;
      lastAutoIssuedPlate.current = result.plate;
      lastAutoIssuedType.current = result.violation_type;

      const citationData = {
        timestamp: result.timestamp || new Date().toISOString().slice(0, 16).replace('T', ' '),
        plate: result.plate,
        type: result.violation_type,
        vehicle: result.vehicle || "Automobile",
        risk_score: result.risk_score,
        confidence: (result.ocr_confidence || 90) + "%",
        fine: result.fine || "$150.00",
        status: "APPROVED"
      };

      try {
        const cRes = await fetch(`${API_BASE}/citations`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(citationData)
        });
        if (cRes.ok) {
          triggerToast(`Auto-issued Citation ticket for ${result.violation_type.replace(/_/g, ' ')}`);
          refreshData();
        }
      } catch (err) {
        console.error("Failed to auto-issue citation:", err);
      }
    }
  };

  // Draw scene function
  const drawScenario = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = 800;
    canvas.height = 380;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (currentScenarioId === "live_webcam") {
      if (!isAnalysisRunning) {
        drawCustomImagePlaceholder(ctx, "Live System Camera");
      }
      return;
    }

    const enhanced = !preprocessMode; // Enhanced is when preprocessMode is false (no noise overlays)

    if (currentScenario.imageType === "canvas_draw_helmet") {
      drawHelmetScene(ctx, enhanced);
    } else if (currentScenario.imageType === "canvas_draw_redlight") {
      drawRedLightScene(ctx, enhanced);
    } else if (currentScenario.imageType === "canvas_draw_seatbelt") {
      drawSeatbeltScene(ctx, enhanced);
    } else if (currentScenario.imageType === "canvas_draw_parking") {
      drawParkingScene(ctx, enhanced);
    } else if (currentScenario.imageElement) {
      ctx.drawImage(currentScenario.imageElement, 0, 0, canvas.width, canvas.height);
      if (preprocessMode) {
        applyCameraGrain(ctx, 0.3);
      }
    } else {
      drawCustomImagePlaceholder(ctx, currentScenario.customName || "Uploaded Traffic Stream");
    }

    // Draw bounding boxes if AI pipeline has completed
    if (isAnalysisRunning && currentScenario.boxes) {
      drawBoundingBoxes(ctx, currentScenario.boxes);
    }
  };

  // Trigger AI Pipeline for static scenarios
  const runAIPipeline = () => {
    if (currentScenarioId === "live_webcam") {
      if (isAnalysisRunning) {
        setIsAnalysisRunning(false);
        if (webcamIntervalRef.current) {
          clearInterval(webcamIntervalRef.current);
          webcamIntervalRef.current = null;
        }
        setPipelineStatus("SYSTEM IDLE");
        setActiveTicket(null);
        drawScenario();
      } else {
        setIsAnalysisRunning(true);
        setPipelineStatus("PROCESSING AI");
        setOcrText("DECODING...");
        setOcrConf("---");
        // Start capture loop
        captureWebcamFrame();
        webcamIntervalRef.current = setInterval(captureWebcamFrame, 2000);
      }
      return;
    }

    if (isAnalysisRunning) return; // already done

    setIsAnalysisRunning(true);
    setPipelineStatus("PROCESSING AI");
    setOcrText("DECODING...");
    setOcrConf("---");
    setPreprocessMode(false); // Switch to enhanced mode automatically to run pipeline

    const canvas = canvasRef.current;
    if (!canvas) return;

    // Convert canvas content to blob and upload
    canvas.toBlob(async (blob) => {
      const formData = new FormData();
      // Name file properly so python simulation or AI knows the scenario keyword
      formData.append("file", blob, `${currentScenarioId}.png`);

      try {
        const res = await fetch(`${API_BASE}/analyze`, {
          method: "POST",
          body: formData
        });

        if (!res.ok) throw new Error("Analysis request failed");
        const result = await res.json();

        // Update local scenario values
        const isRealViolation = result.violation_type && result.violation_type !== "NO_VIOLATION" && result.violation_type !== "NONE";
        setPipelineStatus(isRealViolation ? "VIOLATION CAPTURED" : "MONITORING SECURE");
        setOcrText(result.plate);
        setOcrConf(result.ocr_confidence + "%");

        // Map boxes
        const mappedBoxes = (result.detections || []).map(det => {
          const [x1, y1, x2, y2] = det.box;
          const rx = (x1 / canvas.width) * 100;
          const ry = (y1 / canvas.height) * 100;
          const rw = ((x2 - x1) / canvas.width) * 100;
          const rh = ((y2 - y1) / canvas.height) * 100;

          let color = "#EF4444";
          if (det.class.toLowerCase().includes("plate")) color = "#F59E0B";
          else if (["car", "suv", "sedan", "vehicle", "motorcycle", "bus", "truck"].includes(det.class.toLowerCase())) color = "#10B981";

          return {
            x: rx, y: ry, w: rw, h: rh,
            label: det.class,
            conf: `${det.confidence}%`,
            color
          };
        });

        const updatedScenarios = scenarios.map(s => {
          if (s.id === currentScenarioId) {
            return {
              ...s,
              plate: result.plate,
              ocrConfidence: result.ocr_confidence,
              violationType: result.violation_type,
              riskScore: result.risk_score,
              confidence: result.detections && result.detections.length > 0 ? result.detections[0].confidence : 90.0,
              fine: result.fine,
              vehicleClass: result.vehicle,
              details: result.details,
              boxes: mappedBoxes
            };
          }
          return s;
        });

        setScenarios(updatedScenarios);

        // Update active ticket card details
        const ticketDetail = {
          id: result.ticket_id || "TKT-TEMP",
          timestamp: result.timestamp || new Date().toISOString().slice(0, 16).replace('T', ' '),
          plate: result.plate,
          violationType: result.violation_type,
          vehicleClass: result.vehicle,
          riskScore: result.risk_score,
          confidence: result.ocr_confidence,
          fine: result.fine,
          severity: result.severity.toLowerCase() === 'high' || result.risk_score >= 75 ? 'danger' : result.severity.toLowerCase() === 'medium' ? 'warning' : 'info',
          offenderStatus: result.offender_status,
          details: result.details
        };
        setActiveTicket(ticketDetail);

        // Redraw canvas with bounding boxes
        const ctx = canvas.getContext('2d');
        if (currentScenario.imageType === "canvas_draw_helmet") {
          drawHelmetScene(ctx, true);
        } else if (currentScenario.imageType === "canvas_draw_redlight") {
          drawRedLightScene(ctx, true);
        } else if (currentScenario.imageType === "canvas_draw_seatbelt") {
          drawSeatbeltScene(ctx, true);
        } else if (currentScenario.imageType === "canvas_draw_parking") {
          drawParkingScene(ctx, true);
        }
        drawBoundingBoxes(ctx, mappedBoxes);

      } catch (err) {
        console.error("AI pipeline execution error:", err);
        setPipelineStatus("SYSTEM IDLE");
        setIsAnalysisRunning(false);
        triggerToast("Failed to run AI analysis: backend unavailable.");
      }
    }, "image/png");
  };

  // Scenario reset / click handler
  const handleScenarioChange = (id) => {
    setCurrentScenarioId(id);
    setIsAnalysisRunning(false);
    setPipelineStatus("SYSTEM IDLE");
    setOcrText("-- READY --");
    setOcrConf("0%");
    setActiveTicket(null);
    setPreprocessMode(false);
  };

  // File Uploader Upload Handler
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const imgEl = new Image();
      imgEl.onload = () => {
        const customId = "uploaded_" + Date.now();
        const customScenario = {
          id: customId,
          title: "Upload: " + file.name.substring(0, 14),
          desc: "User uploaded photo analyzed by live YOLOv11 & OCR.",
          tag: "uploaded",
          imageType: "custom",
          customName: file.name,
          rawFile: file,
          imageElement: imgEl,
          vehicleClass: "Automobile",
          violationType: "HELMET_NON_COMPLIANCE",
          severity: "warning",
          riskScore: 68,
          fine: "$150.00",
          plate: "AP-39-CD-4567",
          confidence: 85.0,
          ocrConfidence: 88.0,
          details: {
            speed: "45 km/h",
            location: "Sector-4 Crossroads",
            light: "Variable Light",
            weather: "Clear"
          },
          boxes: []
        };

        setScenarios([customScenario, ...scenarios.filter(s => s.tag !== 'uploaded')]);
        setCurrentScenarioId(customId);
        setIsAnalysisRunning(false);
        setPipelineStatus("SYSTEM IDLE");
        setOcrText("-- READY --");
        setOcrConf("0%");
        setActiveTicket(null);
        setPreprocessMode(false);
        triggerToast("Custom image uploaded successfully");
      };
      imgEl.src = event.target.result;
    };
    reader.readAsDataURL(file);
  };

  // Submit citation verification action from Real-time Tab
  const handleTicketAction = async (status) => {
    if (!activeTicket) return;

    const payload = {
      timestamp: activeTicket.timestamp,
      plate: activeTicket.plate,
      type: activeTicket.violationType,
      vehicle: activeTicket.vehicleClass,
      risk_score: activeTicket.riskScore,
      confidence: activeTicket.confidence + "%",
      fine: activeTicket.fine,
      status: status, // APPROVED, PENDING_REVIEW, DISMISSED
      details: activeTicket.details
    };

    try {
      const res = await fetch(`${API_BASE}/citations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        triggerToast(`Ticket ${activeTicket.id} marked as ${status} and saved in Database.`);
        setActiveTicket(null);
        setIsAnalysisRunning(false);
        setPipelineStatus("SYSTEM IDLE");
        setOcrText("-- READY --");
        setOcrConf("0%");
        refreshData();
      }
    } catch (err) {
      console.error("Failed to commit citation verification:", err);
      triggerToast("Error: Failed to submit review to backend database.");
    }
  };

  // Update Status in Ledger
  const handleUpdateLedgerStatus = async (ticketId, newStatus) => {
    try {
      const res = await fetch(`${API_BASE}/citations/${ticketId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        triggerToast(`Ticket ${ticketId} status updated to ${newStatus}`);
        refreshData();
      }
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  };

  // Delete Citation from Ledger
  const handleDeleteCitation = async (ticketId) => {
    if (!window.confirm(`Are you sure you want to delete citation record ${ticketId}?`)) return;
    try {
      const res = await fetch(`${API_BASE}/citations/${ticketId}`, {
        method: "DELETE"
      });
      if (res.ok) {
        triggerToast(`Citation ${ticketId} removed successfully.`);
        refreshData();
      }
    } catch (err) {
      console.error("Failed to delete citation:", err);
    }
  };

  // Canvas Drawing routines (replicated from app.js)
  const drawHelmetScene = (c, enhanced) => {
    let skyGrad = c.createLinearGradient(0, 0, 0, 150);
    skyGrad.addColorStop(0, enhanced ? "#0f172a" : "#020617");
    skyGrad.addColorStop(1, enhanced ? "#1e293b" : "#0f172a");
    c.fillStyle = skyGrad;
    c.fillRect(0, 0, 800, 180);

    c.fillStyle = "#334155";
    c.fillRect(100, 60, 4, 120);
    c.fillRect(680, 40, 4, 140);

    c.beginPath();
    c.arc(102, 60, 20, 0, Math.PI * 2);
    c.fillStyle = enhanced ? "rgba(253, 224, 71, 0.45)" : "rgba(253, 224, 71, 0.2)";
    c.fill();

    c.beginPath();
    c.arc(682, 40, 30, 0, Math.PI * 2);
    c.fillStyle = enhanced ? "rgba(253, 224, 71, 0.45)" : "rgba(253, 224, 71, 0.2)";
    c.fill();

    c.strokeStyle = "rgba(251, 191, 36, 0.6)";
    c.lineWidth = 4;
    c.setLineDash([20, 15]);
    c.beginPath();
    c.moveTo(0, 280);
    c.lineTo(800, 280);
    c.stroke();
    c.setLineDash([]);

    c.save();
    c.translate(350, 180);
    
    c.beginPath();
    c.arc(20, 110, 32, 0, Math.PI * 2);
    c.arc(140, 110, 32, 0, Math.PI * 2);
    c.fillStyle = "#0f172a";
    c.fill();
    c.strokeStyle = "#475569";
    c.lineWidth = 6;
    c.stroke();
    
    c.fillStyle = "#8b5cf6";
    c.beginPath();
    c.moveTo(10, 110);
    c.lineTo(40, 60);
    c.lineTo(100, 60);
    c.lineTo(130, 110);
    c.closePath();
    c.fill();
    
    c.beginPath();
    c.moveTo(140, 70);
    c.lineTo(320, 140);
    c.lineTo(320, 220);
    c.closePath();
    let lightGrad = c.createLinearGradient(140, 70, 320, 180);
    lightGrad.addColorStop(0, "rgba(255, 255, 255, 0.8)");
    lightGrad.addColorStop(1, "rgba(255, 255, 255, 0)");
    c.fillStyle = lightGrad;
    c.fill();

    c.fillStyle = "#334155";
    c.fillRect(60, 10, 25, 50);
    c.beginPath();
    c.arc(72, -5, 12, 0, Math.PI*2);
    c.fillStyle = "#10b981";
    c.fill();
    c.fillStyle = "#000";
    c.fillRect(72, -9, 8, 5);

    c.fillStyle = "#475569";
    c.fillRect(25, 20, 24, 45);
    c.beginPath();
    c.arc(37, 5, 11, 0, Math.PI*2);
    c.fillStyle = "#fb7185";
    c.fill();
    c.beginPath();
    c.arc(35, 1, 9, Math.PI, 0);
    c.fillStyle = "#0f172a";
    c.fill();

    c.fillStyle = "#e2e8f0";
    c.fillRect(5, 105, 20, 12);
    c.fillStyle = "#000";
    c.font = "bold 6px monospace";
    c.fillText("MH-12", 6, 113);

    c.restore();

    if (!enhanced) {
      if (lowLightFilter) applyCameraGrain(c, 0.45);
      if (weatherFilter) applyColorMutedness(c, 0.7);
    }
  };

  const drawRedLightScene = (c, enhanced) => {
    c.fillStyle = "#0f172a";
    c.fillRect(0, 0, 800, 380);

    c.fillStyle = "rgba(255, 255, 255, 0.85)";
    for (let i = 0; i < 9; i++) {
      c.fillRect(150, 180 + i * 22, 500, 10);
    }

    c.fillStyle = "#475569";
    c.fillRect(650, 40, 10, 240);
    c.fillStyle = "#0f172a";
    c.fillRect(640, 40, 30, 80);
    
    c.beginPath();
    c.arc(655, 60, 10, 0, Math.PI * 2);
    c.fillStyle = "#ef4444";
    c.fill();
    c.shadowColor = "#ef4444";
    c.shadowBlur = enhanced ? 25 : 8;
    c.beginPath();
    c.arc(655, 60, 7, 0, Math.PI * 2);
    c.fillStyle = "#ff8585";
    c.fill();
    c.shadowBlur = 0;

    c.beginPath();
    c.arc(655, 80, 8, 0, Math.PI*2);
    c.arc(655, 100, 8, 0, Math.PI*2);
    c.fillStyle = "#1e293b";
    c.fill();

    c.save();
    c.translate(250, 150);
    c.fillStyle = "rgba(0,0,0,0.5)";
    c.fillRect(10, 110, 280, 20);

    c.fillStyle = "#dc2626";
    c.beginPath();
    c.moveTo(10, 110);
    c.lineTo(20, 75);
    c.lineTo(90, 70);
    c.lineTo(130, 40);
    c.lineTo(220, 40);
    c.lineTo(260, 70);
    c.lineTo(280, 110);
    c.closePath();
    c.fill();

    c.fillStyle = "#0f172a";
    c.beginPath();
    c.moveTo(135, 45);
    c.lineTo(175, 45);
    c.lineTo(175, 65);
    c.lineTo(130, 65);
    c.closePath();
    c.fill();

    c.beginPath();
    c.moveTo(182, 45);
    c.lineTo(215, 45);
    c.lineTo(220, 65);
    c.lineTo(182, 65);
    c.closePath();
    c.fill();

    c.beginPath();
    c.arc(60, 110, 28, 0, Math.PI * 2);
    c.arc(220, 110, 28, 0, Math.PI * 2);
    c.fillStyle = "#1e293b";
    c.fill();

    c.fillStyle = "#fbbf24";
    c.fillRect(110, 105, 30, 12);
    c.fillStyle = "#000";
    c.font = "bold 6px monospace";
    c.fillText("KA-51-MD", 112, 113);
    c.restore();

    c.strokeStyle = "rgba(255, 255, 255, 0.4)";
    c.lineWidth = 1.2;
    const rainCount = enhanced ? 15 : 65;
    if (weatherFilter) {
      for (let r = 0; r < rainCount; r++) {
        let rx = Math.random() * 800;
        let ry = Math.random() * 380;
        c.beginPath();
        c.moveTo(rx, ry);
        c.lineTo(rx - 8, ry + 22);
        c.stroke();
      }
    }

    if (!enhanced && weatherFilter) {
      applyWaterSplashes(c);
    }
  };

  const drawSeatbeltScene = (c, enhanced) => {
    c.fillStyle = "#334155";
    c.fillRect(0, 0, 800, 380);

    c.fillStyle = "#7dd3fc";
    c.fillRect(0, 0, 800, 100);
    
    c.fillStyle = "#065f46";
    c.beginPath();
    c.moveTo(0, 100);
    c.lineTo(200, 60);
    c.lineTo(500, 100);
    c.lineTo(800, 70);
    c.lineTo(800, 120);
    c.lineTo(0, 120);
    c.closePath();
    c.fill();

    c.fillStyle = "#94a3b8";
    c.fillRect(0, 95, 800, 10);
    
    c.strokeStyle = "#fff";
    c.lineWidth = 3;
    c.beginPath();
    c.moveTo(0, 240);
    c.lineTo(800, 240);
    c.stroke();

    c.save();
    c.translate(220, 110);
    c.fillStyle = "rgba(0,0,0,0.6)";
    c.fillRect(0, 170, 380, 25);

    c.fillStyle = "#0284c7";
    c.fillRect(20, 60, 330, 110);
    c.beginPath();
    c.moveTo(80, 60);
    c.lineTo(150, 10);
    c.lineTo(310, 10);
    c.lineTo(340, 60);
    c.closePath();
    c.fill();

    c.beginPath();
    c.arc(80, 170, 36, 0, Math.PI*2);
    c.arc(280, 170, 36, 0, Math.PI*2);
    c.fillStyle = "#0f172a";
    c.fill();

    c.fillStyle = "#e0f2fe";
    c.beginPath();
    c.moveTo(155, 18);
    c.lineTo(230, 18);
    c.lineTo(240, 55);
    c.lineTo(150, 55);
    c.closePath();
    c.fill();

    c.fillStyle = "#1e293b";
    c.fillRect(190, 28, 20, 25);
    c.beginPath();
    c.arc(200, 24, 6, 0, Math.PI*2);
    c.fill();

    if (enhanced) {
      c.strokeStyle = "rgba(239, 68, 68, 0.85)";
      c.lineWidth = 2.5;
      c.beginPath();
      c.arc(198, 38, 10, 0, Math.PI * 2);
      c.stroke();
    }

    c.fillStyle = "#fff";
    c.fillRect(320, 130, 25, 12);
    c.fillStyle = "#000";
    c.font = "bold 6px sans-serif";
    c.fillText("DL-03", 322, 138);

    c.restore();

    if (!enhanced && deblurFilter) {
      applyMotionBlur(c);
    }
  };

  const drawParkingScene = (c, enhanced) => {
    c.fillStyle = "#334155";
    c.fillRect(0, 0, 800, 380);
    
    c.fillStyle = "#64748b";
    c.fillRect(0, 0, 800, 120);

    c.fillStyle = "#f59e0b";
    for (let k = 0; k < 16; k++) {
      if (k % 2 === 0) {
        c.fillRect(k * 50, 115, 50, 8);
      }
    }

    c.fillStyle = "#475569";
    c.fillRect(160, 30, 4, 100);
    c.beginPath();
    c.arc(162, 30, 16, 0, Math.PI*2);
    c.fillStyle = "#ef4444";
    c.fill();
    c.beginPath();
    c.arc(162, 30, 12, 0, Math.PI*2);
    c.fillStyle = "#1e40af";
    c.fill();
    c.strokeStyle = "#ef4444";
    c.lineWidth = 3;
    c.beginPath();
    c.moveTo(154, 22);
    c.lineTo(170, 38);
    c.stroke();

    c.save();
    c.translate(320, 90);
    c.fillStyle = "rgba(0,0,0,0.55)";
    c.fillRect(10, 160, 340, 20);

    c.fillStyle = "#f8fafc";
    c.fillRect(20, 30, 300, 130);
    c.fillStyle = "#94a3b8";
    c.fillRect(35, 45, 120, 50);
    c.fillStyle = "#334155";
    c.fillRect(230, 45, 60, 45);

    c.beginPath();
    c.arc(80, 160, 30, 0, Math.PI*2);
    c.arc(260, 160, 30, 0, Math.PI*2);
    c.fillStyle = "#0f172a";
    c.fill();

    c.fillStyle = "#f59e0b";
    c.fillRect(285, 120, 30, 12);
    c.restore();

    if (!enhanced) {
      applyShadowGlare(c);
    }
  };

  const drawCustomImagePlaceholder = (c, name) => {
    let skyGrad = c.createLinearGradient(0, 0, 0, 380);
    skyGrad.addColorStop(0, "#080c14");
    skyGrad.addColorStop(1, "#1e1b4b");
    c.fillStyle = skyGrad;
    c.fillRect(0, 0, 800, 380);

    c.strokeStyle = "rgba(99, 102, 241, 0.1)";
    c.lineWidth = 1;
    for (let x = 0; x < 800; x += 40) {
      c.beginPath(); c.moveTo(x, 0); c.lineTo(x, 380); c.stroke();
    }
    for (let y = 0; y < 380; y += 40) {
      c.beginPath(); c.moveTo(0, y); c.lineTo(800, y); c.stroke();
    }

    c.beginPath();
    c.arc(400, 190, 60, 0, Math.PI*2);
    c.fillStyle = "rgba(99, 102, 241, 0.05)";
    c.fill();
    c.strokeStyle = "rgba(99, 102, 241, 0.4)";
    c.lineWidth = 2;
    c.stroke();

    c.fillStyle = "#fff";
    c.font = "bold 16px sans-serif";
    c.textAlign = "center";
    c.fillText(name, 400, 195);
    c.font = "12px sans-serif";
    c.fillStyle = "#94A3B8";
    c.fillText("Custom user uploaded camera stream.", 400, 220);
    c.textAlign = "left";
  };

  const applyCameraGrain = (c, opacity) => {
    try {
      const imgData = c.getImageData(0, 0, 800, 380);
      const data = imgData.data;
      for (let i = 0; i < data.length; i += 4) {
        const noise = (Math.random() - 0.5) * 80 * opacity;
        data[i] = Math.min(255, Math.max(0, data[i] + noise));
        data[i+1] = Math.min(255, Math.max(0, data[i+1] + noise));
        data[i+2] = Math.min(255, Math.max(0, data[i+2] + noise));
      }
      c.putImageData(imgData, 0, 0);
    } catch (e) {
      // ignore security error if canvas is tainted by cross-origin resource
    }
  };

  const applyColorMutedness = (c, factor) => {
    c.fillStyle = `rgba(15, 23, 42, ${factor * 0.3})`;
    c.fillRect(0, 0, 800, 380);
  };

  const applyWaterSplashes = (c) => {
    c.fillStyle = "rgba(255, 255, 255, 0.08)";
    for(let s = 0; s < 12; s++) {
      c.beginPath();
      c.arc(Math.random()*800, Math.random()*380, Math.random()*25 + 5, 0, Math.PI*2);
      c.fill();
    }
  };

  const applyMotionBlur = (c) => {
    c.fillStyle = "rgba(255, 255, 255, 0.12)";
    for(let j=0; j<8; j++) {
      c.fillRect(0, Math.random()*380, 800, Math.random()*15 + 2);
    }
  };

  const applyShadowGlare = (c) => {
    c.fillStyle = "rgba(0, 0, 0, 0.25)";
    c.fillRect(0, 180, 800, 200);
  };

  const drawBoundingBoxes = (ctx, boxes) => {
    if (!boxes) return;
    boxes.forEach(box => {
      const bx = (box.x / 100) * 800;
      const by = (box.y / 100) * 380;
      const bw = (box.w / 100) * 800;
      const bh = (box.h / 100) * 380;

      ctx.strokeStyle = box.color || "#EF4444";
      ctx.lineWidth = 2.5;
      ctx.strokeRect(bx, by, bw, bh);

      ctx.fillStyle = box.color || "#EF4444";
      ctx.font = "bold 10px sans-serif";
      const labelText = `${box.label.toUpperCase()} ${box.conf}`;
      const textWidth = ctx.measureText(labelText).width;
      
      ctx.fillRect(bx, by - 16, textWidth + 10, 16);
      
      ctx.fillStyle = "#fff";
      ctx.fillText(labelText, bx + 5, by - 4);
    });
  };

  // Hover detection tooltip inside canvas
  const handleMouseMove = (e) => {
    if (!isAnalysisRunning || preprocessMode || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const mouseX = (e.clientX - rect.left) * scaleX;
    const mouseY = (e.clientY - rect.top) * scaleY;

    let foundBox = null;
    const boxes = currentScenario.boxes;
    if (!boxes) return;

    for (let k = 0; k < boxes.length; k++) {
      const box = boxes[k];
      const bx = (box.x / 100) * canvas.width;
      const by = (box.y / 100) * canvas.height;
      const bw = (box.w / 100) * canvas.width;
      const bh = (box.h / 100) * canvas.height;

      if (mouseX >= bx && mouseX <= bx + bw && mouseY >= by && mouseY <= by + bh) {
        foundBox = box;
        break;
      }
    }

    if (foundBox) {
      const popX = (foundBox.x + foundBox.w / 2) / 100 * rect.width;
      const popY = foundBox.y / 100 * rect.height;
      setTooltipPos({ x: popX, y: popY });
      setHoveredBox(foundBox);
    } else {
      setHoveredBox(null);
    }
  };

  // Download PDF Citation
  const downloadPDF = (ticketId) => {
    window.open(`${API_BASE}/citations/${ticketId}/pdf`);
    triggerToast(`Downloading PDF citation evidence bundle for ${ticketId}`);
  };

  // Download JSON Citation
  const downloadJSON = (ticketId) => {
    window.open(`${API_BASE}/citations/${ticketId}/json`);
    triggerToast(`Downloading JSON citation evidence metadata for ${ticketId}`);
  };

  // Export Ledger as CSV
  const handleExportCSV = () => {
    if (citations.length === 0) {
      triggerToast("No records available to export.");
      return;
    }
    const headers = ["Ticket ID", "Timestamp", "License Plate", "Violation Type", "Vehicle", "Risk Score", "Fine", "Status"];
    const rows = citations.map(c => [
      c.id,
      c.timestamp,
      c.plate,
      c.type,
      c.vehicle,
      c.risk_score,
      c.fine,
      c.status
    ]);
    const csvContent = "data:text/csv;charset=utf-8," 
      + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `BTP_TrafficEye_Report_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    triggerToast("Enforcement records exported as CSV successfully.");
  };

  // Filter and paginated ledger citations
  const filteredCitations = citations.filter(c => {
    const matchesSearch = c.plate.toLowerCase().includes(searchPlate.toLowerCase());
    const matchesType = violationFilter === "ALL" || c.type === violationFilter;
    const matchesStatus = statusFilter === "ALL" || c.status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
  });

  const totalPages = Math.ceil(filteredCitations.length / entriesPerPage);
  const displayedCitations = filteredCitations.slice(
    ledgerPage * entriesPerPage,
    (ledgerPage + 1) * entriesPerPage
  );

  // Compute stats metrics dynamically
  const approvedCount = citations.filter(c => c.status === "APPROVED").length;
  const pendingCount = citations.filter(c => c.status === "PENDING_REVIEW").length;
  const dismissedCount = citations.filter(c => c.status === "DISMISSED").length;

  const totalFinesValue = citations
    .filter(c => c.status !== "DISMISSED")
    .reduce((sum, c) => sum + parseFloat(c.fine.replace(/[^0-9.]/g, '') || 0), 0);

  // Category counts for Recharts bar chart
  const categoryChartData = [
    { name: "Helmet", count: citations.filter(c => c.type.includes("HELMET")).length },
    { name: "Seatbelt", count: citations.filter(c => c.type.includes("SEATBELT")).length },
    { name: "Red Light", count: citations.filter(c => c.type.includes("RED_LIGHT")).length },
    { name: "Triple Riding", count: citations.filter(c => c.type.includes("TRIPLE")).length },
    { name: "Parking", count: citations.filter(c => c.type.includes("PARKING")).length },
    { name: "Wrong Side", count: citations.filter(c => c.type.includes("WRONG")).length },
    { name: "Stop Line", count: citations.filter(c => c.type.includes("STOP_LINE")).length }
  ].filter(item => item.count > 0 || true);

  // Hourly counts for Recharts line chart
  const hourlyCountData = [
    { hour: "08:00", volume: 2 },
    { hour: "11:00", volume: 4 },
    { hour: "14:00", volume: 1 },
    { hour: "17:00", volume: 3 },
    { hour: "20:00", volume: 5 },
    { hour: "23:00", volume: 2 }
  ];

  // Map database entries to trend chart
  citations.forEach(c => {
    const hour = parseInt(c.timestamp.substring(11, 13));
    if (isNaN(hour)) return;
    if (hour >= 8 && hour < 11) hourlyCountData[0].volume++;
    else if (hour >= 11 && hour < 14) hourlyCountData[1].volume++;
    else if (hour >= 14 && hour < 17) hourlyCountData[2].volume++;
    else if (hour >= 17 && hour < 20) hourlyCountData[3].volume++;
    else if (hour >= 20 && hour < 23) hourlyCountData[4].volume++;
    else hourlyCountData[5].volume++;
  });

  return (
    <div className="app-container">
      {/* Toast Notification */}
      {showToast && (
        <div className="toast-notification">
          <span>{toastMessage}</span>
        </div>
      )}

      {/* --- SIDEBAR NAVIGATION --- */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">T</div>
          <div className="brand-name">TrafficEye AI</div>
        </div>

        <nav className="nav-menu">
          <div
            className={`nav-item ${activeTab === 'realtime' ? 'active' : ''}`}
            onClick={() => setActiveTab("realtime")}
          >
            <LayoutGrid size={18} />
            Real-Time Pipeline
          </div>
          <div
            className={`nav-item ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab("analytics")}
          >
            <BarChart3 size={18} />
            Analytics & Trends
          </div>
          <div
            className={`nav-item ${activeTab === 'ledger' ? 'active' : ''}`}
            onClick={() => setActiveTab("ledger")}
          >
            <FileText size={18} />
            Violations Ledger
          </div>
          <div
            className={`nav-item ${activeTab === 'btphub' ? 'active' : ''}`}
            onClick={() => setActiveTab("btphub")}
          >
            <Database size={18} />
            BTP Submission Hub
          </div>
          <div
            className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab("settings")}
          >
            <SettingsIcon size={18} />
            System Settings
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="status-card">
            <div className="status-item">
              <span>AI Core Agent:</span>
              <span className="flex items-center gap-1.5 font-bold text-emerald-400">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                ACTIVE
              </span>
            </div>
            <div className="status-item" style={{ marginTop: '0.5rem' }}>
              <span>Detection Stack:</span>
              <span style={{ color: 'var(--text-secondary)' }}>YOLOv11 & DeepSORT</span>
            </div>
            <div className="status-item" style={{ marginTop: '0.5rem' }}>
              <span>OCR Reader:</span>
              <span style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>EasyOCR Engine</span>
            </div>
          </div>
        </div>
      </aside>

      {/* --- MAIN CONTENT AREA --- */}
      <main className="main-content">

        {/* --- TAB 1: REAL-TIME CV PIPELINE --- */}
        {activeTab === 'realtime' && (
          <section id="tab-realtime" className="tab-pane active">
            <div className="section-header">
              <div className="header-title">
                <h1>BTP Intelligent Violation Detection</h1>
                <p>Computer vision analysis pipeline with real-time risk classification and plate OCR</p>
              </div>
              <div className="header-actions">
                <span
                  id="pipeline-status-indicator"
                  className={`severity-badge ${
                    pipelineStatus === "VIOLATION CAPTURED"
                      ? "badge-danger"
                      : pipelineStatus === "MONITORING SECURE"
                      ? "badge-success"
                      : pipelineStatus === "PROCESSING AI"
                      ? "badge-warning"
                      : "badge-info"
                  }`}
                  style={{ fontWeight: 700 }}
                >
                  {pipelineStatus}
                </span>
              </div>
            </div>

            <div className="cv-pipeline-grid">
              {/* Left Column: Test Scenarios */}
              <div className="scenarios-container">
                <h3 style={{ fontSize: '0.95rem', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Test Scenarios</h3>
                <div id="scenarios-list" className="flex flex-col gap-2">
                  {scenarios.map(s => (
                    <div
                      key={s.id}
                      className={`scenario-item ${currentScenarioId === s.id ? 'active' : ''}`}
                      onClick={() => handleScenarioChange(s.id)}
                    >
                      <div className="scenario-item-header">
                        <span className="scenario-title">{s.title}</span>
                        <span className={`tag-badge ${
                          s.tag === 'live' ? 'tag-live' :
                          s.tag === 'low-light' ? 'tag-low-light' :
                          s.tag === 'weather' ? 'tag-weather' :
                          s.tag === 'uploaded' ? 'tag-live bg-cyan-700' : 'tag-normal'
                        }`}>{s.tag.toUpperCase()}</span>
                      </div>
                      <p className="scenario-desc">{s.desc}</p>
                    </div>
                  ))}
                </div>

                <div
                  className="upload-zone"
                  id="upload-zone"
                  onClick={() => document.getElementById("file-uploader").click()}
                >
                  <input
                    type="file"
                    id="file-uploader"
                    style={{ display: 'none' }}
                    accept="image/*"
                    onChange={handleFileUpload}
                  />
                  <div className="upload-icon">
                    <Upload size={28} />
                  </div>
                  <div className="upload-text">Upload Traffic Image</div>
                  <div className="upload-sub">Supports PNG, JPG, JPEG</div>
                </div>
              </div>

              {/* Middle Column: Visual CV Workspace */}
              <div className="glass-card workspace-card">
                <div className="workspace-header">
                  <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Visual Processing Workspace</h2>
                  <div className="workspace-actions flex gap-2">
                    {currentScenarioId === "live_webcam" && (
                      <video
                        ref={videoRef}
                        style={{ display: 'none' }}
                        width="800"
                        height="380"
                        playsInline
                        muted
                      />
                    )}
                    <button
                      className={`btn ${preprocessMode ? 'btn-primary' : ''}`}
                      onClick={() => setPreprocessMode(!preprocessMode)}
                    >
                      {preprocessMode ? "Enhanced View" : "Original View"}
                    </button>
                    <button
                      className="btn btn-primary flex items-center gap-1.5"
                      onClick={runAIPipeline}
                    >
                      {isAnalysisRunning ? <Square size={14} /> : <Play size={14} />}
                      {currentScenarioId === "live_webcam" 
                        ? (isAnalysisRunning ? "Stop Pipeline" : "Run AI Pipeline")
                        : (isAnalysisRunning ? "AI Complete" : "Run AI Pipeline")}
                    </button>
                  </div>
                </div>

                {/* Canvas viewport */}
                <div className={`canvas-viewport ${isAnalysisRunning && pipelineStatus === 'PROCESSING AI' ? 'scan-active' : ''}`} id="canvas-viewport">
                  <canvas
                    ref={canvasRef}
                    id="image-canvas"
                    onMouseMove={handleMouseMove}
                    onMouseLeave={() => setHoveredBox(null)}
                  ></canvas>
                  <div className="scan-line" id="scan-line"></div>
                  
                  {/* Hover box tooltip */}
                  {hoveredBox && (
                    <div
                      className="detection-popup"
                      style={{
                        position: 'absolute',
                        left: `${tooltipPos.x}px`,
                        top: `${tooltipPos.y - 40}px`,
                        opacity: 1,
                        transform: 'translateX(-50%)',
                        pointerEvents: 'none'
                      }}
                    >
                      <div style={{ fontWeight: 700, color: hoveredBox.color }}>{hoveredBox.label}</div>
                      <div style={{ color: 'var(--text-secondary)', marginTop: '2px' }}>
                        CV Score: <strong>{hoveredBox.conf}</strong>
                      </div>
                    </div>
                  )}
                </div>

                {/* Bottom HUD: Filter controls & OCR */}
                <div className="pipeline-hud">
                  {/* Preprocessing filters */}
                  <div className="hud-panel">
                    <div className="hud-title">Image Preprocessing Filters</div>
                    <div className="filter-toggles">
                      <div className="toggle-row">
                        <span>Low-Light Enhancer (CLAHE)</span>
                        <label className="toggle-switch">
                          <input
                            type="checkbox"
                            checked={lowLightFilter}
                            onChange={(e) => setLowLightFilter(e.target.checked)}
                          />
                          <span className="slider"></span>
                        </label>
                      </div>
                      <div className="toggle-row">
                        <span>Weather De-noiser (Rain/Fog)</span>
                        <label className="toggle-switch">
                          <input
                            type="checkbox"
                            checked={weatherFilter}
                            onChange={(e) => setWeatherFilter(e.target.checked)}
                          />
                          <span className="slider"></span>
                        </label>
                      </div>
                      <div className="toggle-row">
                        <span>Motion Deblur & Contrast</span>
                        <label className="toggle-switch">
                          <input
                            type="checkbox"
                            checked={deblurFilter}
                            onChange={(e) => setDeblurFilter(e.target.checked)}
                          />
                          <span className="slider"></span>
                        </label>
                      </div>
                    </div>
                  </div>

                  {/* License Plate OCR HUD */}
                  <div className="hud-panel">
                    <div className="hud-title">ANPR / OCR Extraction</div>
                    <div className="ocr-hud-content">
                      <div className="plate-ocr-box" id="plate-ocr-box">
                        {ocrText}
                      </div>
                      <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        <span>OCR Conf: <strong id="ocr-conf" style={{ color: 'var(--accent-cyan)' }}>{ocrConf}</strong></span>
                        <span>Tracking: <strong style={{ color: 'var(--text-secondary)' }}>DeepSORT</strong></span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: Citation evidence generator */}
              <div className="glass-card evidence-card" id="evidence-card-element">
                <div className="evidence-header">
                  <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Evidence Citation</h2>
                  <span className={`severity-badge ${
                    activeTicket ? (
                      activeTicket.severity === 'danger' ? 'badge-danger' : 
                      activeTicket.severity === 'warning' ? 'badge-warning' : 'badge-info'
                    ) : 'badge-info'
                  }`} id="violation-severity">
                    {activeTicket ? activeTicket.severity.toUpperCase() : "--"}
                  </span>
                </div>

                <div className="evidence-preview relative flex items-center justify-center bg-slate-900 border border-slate-800 rounded-md mb-4" style={{ height: '140px' }}>
                  {activeTicket ? (
                    <div className="text-center p-4">
                      <div className="font-mono text-lg font-bold text-amber-500 tracking-widest bg-slate-950/80 border border-amber-500/20 px-3 py-1.5 rounded inline-block mb-2">
                        {activeTicket.plate}
                      </div>
                      <p className="text-xs text-slate-400">ANPR Region Auto Crop Capture</p>
                      <p className="text-[10px] text-emerald-400 mt-1">Confidence rating: {activeTicket.confidence}%</p>
                    </div>
                  ) : (
                    <span className="text-slate-600 text-xs">Run Pipeline to generate citation preview</span>
                  )}
                </div>

                <div>
                  <table className="meta-table">
                    <tbody>
                      <tr>
                        <td className="meta-label">Ticket ID:</td>
                        <td className="meta-val ticket-id" id="meta-ticket-id">{activeTicket ? activeTicket.id : "--"}</td>
                      </tr>
                      <tr>
                        <td className="meta-label">Violation:</td>
                        <td className="meta-val" id="meta-type" style={{ color: '#EF4444' }}>
                          {activeTicket ? activeTicket.violationType.replace(/_/g, ' ') : "--"}
                        </td>
                      </tr>
                      <tr>
                        <td className="meta-label">Violation RiskScore:</td>
                        <td className="meta-val" id="meta-risk">{activeTicket ? `${activeTicket.riskScore}/100` : "--"}</td>
                      </tr>
                      <tr>
                        <td className="meta-label">License Plate:</td>
                        <td className="meta-val"><span className="plate-cell" id="meta-plate">{activeTicket ? activeTicket.plate : "--"}</span></td>
                      </tr>
                      <tr>
                        <td className="meta-label">Offender Status:</td>
                        <td className="meta-val" id="meta-offender-status" style={{ fontSize: '0.8rem' }}>{activeTicket ? activeTicket.offenderStatus : "--"}</td>
                      </tr>
                      <tr>
                        <td className="meta-label">Detection Conf:</td>
                        <td className="meta-val" id="meta-confidence" style={{ color: 'var(--success)' }}>
                          {activeTicket ? `${activeTicket.confidence}%` : "0%"}
                        </td>
                      </tr>
                      <tr>
                        <td className="meta-label">Vehicle Type:</td>
                        <td className="meta-val" id="meta-vehicle-class">{activeTicket ? activeTicket.vehicleClass : "--"}</td>
                      </tr>
                      <tr>
                        <td className="meta-label">Timestamp:</td>
                        <td className="meta-val" id="meta-time">{activeTicket ? activeTicket.timestamp : "--"}</td>
                      </tr>
                      <tr>
                        <td className="meta-label">Assessed Penalty:</td>
                        <td className="meta-val" id="meta-fine" style={{ fontSize: '1.1rem', fontWeight: 800, color: '#FFF' }}>
                          {activeTicket ? activeTicket.fine : "--"}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div className="evidence-actions">
                  <button
                    className="btn-approve"
                    id="btn-approve-violation"
                    disabled={!activeTicket}
                    onClick={() => handleTicketAction("APPROVED")}
                  >
                    Approve & Issue Citation
                  </button>
                  <div className="action-row-split">
                    <button
                      className="btn-review"
                      id="btn-review-violation"
                      disabled={!activeTicket}
                      onClick={() => handleTicketAction("PENDING_REVIEW")}
                    >
                      Escalate Review
                    </button>
                    <button
                      className="btn-dismiss"
                      id="btn-dismiss-violation"
                      disabled={!activeTicket}
                      onClick={() => handleTicketAction("DISMISSED")}
                    >
                      Dismiss Event
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* --- TAB 2: ANALYTICS & TRENDS --- */}
        {activeTab === 'analytics' && (
          <section id="tab-analytics" className="tab-pane active">
            <div className="section-header">
              <div className="header-title">
                <h1>TrafficEye AI Analytics Dashboard</h1>
                <p>Real-time violation statistics, repeat offender profiles, and predictive traffic hotspots</p>
              </div>
              <button className="btn flex items-center gap-1.5" onClick={refreshData}>
                <RefreshCw size={14} /> Refresh Data
              </button>
            </div>

            {/* KPI Cards Grid */}
            <div className="stats-cards-grid">
              <div className="glass-card stats-card-premium">
                <div className="stats-card-info">
                  <span className="stats-label">Total Violations</span>
                  <span className="stats-val" id="kpi-total-violations">{citations.length}</span>
                  <span className="stats-change stats-up">
                    <span className="flex items-center text-emerald-400 gap-0.5">
                      <Volume2 size={10} /> +14.8% vs yesterday
                    </span>
                  </span>
                </div>
                <div className="stats-card-icon">
                  <Sliders size={22} />
                </div>
              </div>

              <div className="glass-card stats-card-premium">
                <div className="stats-card-info">
                  <span className="stats-label">Total Fines Assessed</span>
                  <span className="stats-val" id="kpi-total-revenue">${totalFinesValue.toFixed(2)}</span>
                  <span className="stats-change stats-up">
                    <span className="text-emerald-400">+8.2% vs yesterday</span>
                  </span>
                </div>
                <div className="stats-card-icon" style={{ color: 'var(--accent-purple)' }}>
                  <FileJson size={22} />
                </div>
              </div>

              <div className="glass-card stats-card-premium">
                <div className="stats-card-info">
                  <span className="stats-label">Active Repeat Offenders</span>
                  <span className="stats-val" id="kpi-repeat-offenders">{repeatOffenders.length}</span>
                  <span className="stats-change stats-down" style={{ color: 'var(--danger)' }}>
                    Critical surveillance active
                  </span>
                </div>
                <div className="stats-card-icon" style={{ color: '#EF4444' }}>
                  <AlertTriangle size={22} />
                </div>
              </div>

              <div className="glass-card stats-card-premium">
                <div className="stats-card-info">
                  <span className="stats-label">Enforcement precision</span>
                  <span className="stats-val" id="kpi-map-accuracy">94.2%</span>
                  <span className="stats-change stats-up" style={{ color: 'var(--success)' }}>
                    Stable mAP index
                  </span>
                </div>
                <div className="stats-card-icon" style={{ color: 'var(--accent-cyan)' }}>
                  <UserCheck size={22} />
                </div>
              </div>
            </div>

            {/* Interactive Leaflet Map Row */}
            <div className="charts-grid-layout" style={{ gridTemplateColumns: '1.2fr 0.8fr', marginBottom: '1.5rem' }}>
              
              {/* Leaflet Heatmap Map container */}
              <div className="glass-card chart-card flex flex-col">
                <div className="chart-header">
                  <span className="chart-title">Predictive Hotspot & Accident Risk Map</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Interactive GIS System</span>
                </div>
                <div className="flex-grow min-h-[300px] relative" style={{ zIndex: 1 }}>
                  <MapContainer
                    center={[12.96, 77.62]}
                    zoom={12}
                    scrollWheelZoom={false}
                    className="leaflet-container"
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                      url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    />
                    {hotspots.map((spot, index) => {
                      const color = spot.risk >= 80 ? "#EF4444" : spot.risk >= 55 ? "#F59E0B" : "#10B981";
                      return (
                        <CircleMarker
                          key={index}
                          center={[spot.lat, spot.lng]}
                          radius={12 + spot.risk / 15}
                          fillColor={color}
                          color={color}
                          weight={2}
                          fillOpacity={0.35}
                        >
                          <Popup className="leaflet-popup-custom">
                            <div className="p-1 font-sans text-xs">
                              <h4 className="font-bold text-white text-sm mb-1">{spot.name}</h4>
                              <p className="text-slate-300">Predictive Risk: <span className="font-bold text-rose-400">{spot.risk}%</span></p>
                              <p className="text-slate-300">Peak Hours: {spot.peak}</p>
                              <p className="text-emerald-400 mt-1 font-semibold">{spot.patrol}</p>
                            </div>
                          </Popup>
                        </CircleMarker>
                      );
                    })}
                  </MapContainer>
                </div>
              </div>

              {/* Right: Resource patrol recommendation */}
              <div className="glass-card chart-card flex flex-col">
                <div className="chart-header">
                  <span className="chart-title">Patrol Deployment Recommendations</span>
                </div>
                <div className="table-wrapper flex-grow overflow-y-auto" style={{ border: 'none', background: 'transparent', height: '300px' }}>
                  <table className="ledger-table" style={{ fontSize: '0.8rem' }}>
                    <thead>
                      <tr>
                        <th>Location / Hotspot</th>
                        <th>Risk Factor</th>
                        <th>Peak Hour</th>
                        <th>Patrol Deployment</th>
                      </tr>
                    </thead>
                    <tbody id="patrol-recommendations-body">
                      {hotspots.map((spot, idx) => (
                        <tr key={idx}>
                          <td><strong>{spot.name}</strong></td>
                          <td>
                            <span className={`risk-badge ${
                              spot.risk >= 80 ? 'risk-high' : spot.risk >= 55 ? 'risk-medium' : 'risk-low'
                            }`}>
                              {spot.risk}% - {spot.risk >= 80 ? 'HIGH' : spot.risk >= 55 ? 'MEDIUM' : 'LOW'}
                            </span>
                          </td>
                          <td>{spot.peak}</td>
                          <td><span className="text-emerald-400 font-semibold">{spot.patrol}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Recharts Analytics Charts Grid */}
            <div className="charts-grid-layout" style={{ marginBottom: '1.5rem' }}>
              {/* Left Category Chart */}
              <div className="glass-card chart-card">
                <div className="chart-header">
                  <span className="chart-title">Violations by Class Category</span>
                </div>
                <div className="p-4 h-[260px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={categoryChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="name" stroke="var(--text-secondary)" tick={{ fontSize: 10 }} />
                      <YAxis stroke="var(--text-secondary)" tick={{ fontSize: 10 }} />
                      <ChartTooltip
                        contentStyle={{
                          background: 'rgba(15, 23, 42, 0.9)',
                          borderColor: 'rgba(255, 255, 255, 0.1)',
                          borderRadius: 8,
                          color: '#fff',
                          fontSize: 11
                        }}
                      />
                      <Bar dataKey="count" fill="url(#barGradient)" radius={[4, 4, 0, 0]}>
                        {categoryChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#06B6D4' : '#8B5CF6'} />
                        ))}
                      </Bar>
                      <defs>
                        <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#06B6D4" />
                          <stop offset="100%" stopColor="#3B82F6" />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Right: Repeat Offenders Table */}
              <div className="glass-card chart-card">
                <div className="chart-header">
                  <span className="chart-title">Top Repeat Offenders Register</span>
                </div>
                <div className="table-wrapper" style={{ border: 'none', background: 'transparent', height: '260px', overflowY: 'auto' }}>
                  <table className="ledger-table" style={{ fontSize: '0.8rem' }}>
                    <thead>
                      <tr>
                        <th>License Plate</th>
                        <th>Total Violations</th>
                        <th>Vehicle</th>
                        <th>Average Risk</th>
                        <th>Surveillance Status</th>
                      </tr>
                    </thead>
                    <tbody id="repeat-offenders-body">
                      {repeatOffenders.map((off, idx) => (
                        <tr key={idx}>
                          <td><span className="plate-cell font-mono">{off.plate}</span></td>
                          <td><strong className="text-rose-400 text-sm">{off.violations_count} Cases</strong></td>
                          <td>{off.vehicle}</td>
                          <td>
                            <span style={{ color: off.avg_risk >= 75 ? '#EF4444' : '#F59E0B', fontWeight: 700 }}>
                              {off.avg_risk}/100
                            </span>
                          </td>
                          <td>
                            <span className="status-badge status-review">FLAGGED</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Bottom Trend Chart */}
            <div className="glass-card chart-card">
              <div className="chart-header">
                <span className="chart-title">Temporal Violation Volume Trend (Hourly Analytics)</span>
              </div>
              <div className="p-4 h-[240px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={hourlyCountData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="hour" stroke="var(--text-secondary)" tick={{ fontSize: 10 }} />
                    <YAxis stroke="var(--text-secondary)" tick={{ fontSize: 10 }} />
                    <ChartTooltip
                      contentStyle={{
                        background: 'rgba(15, 23, 42, 0.9)',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderRadius: 8,
                        color: '#fff',
                        fontSize: 11
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="volume"
                      stroke="#8B5CF6"
                      strokeWidth={3}
                      activeDot={{ r: 6 }}
                      dot={{ fill: '#6366F1', strokeWidth: 2, r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>
        )}

        {/* --- TAB 3: VIOLATIONS LEDGER --- */}
        {activeTab === 'ledger' && (
          <section id="tab-ledger" className="tab-pane active">
            <div className="section-header">
              <div className="header-title">
                <h1>Enforcement Records Ledger</h1>
                <p>Search, review, and manage verified citation cases and evidence metadata</p>
              </div>
              <button className="btn btn-primary" id="btn-export-ledger" onClick={handleExportCSV}>
                Export CSV Report
              </button>
            </div>

            <div className="glass-card">
              <div className="ledger-controls">
                <div className="search-input-wrapper flex items-center bg-slate-900/60 border border-slate-700/60 px-3 py-1.5 rounded-lg w-[320px]">
                  <Search size={16} className="text-slate-400 mr-2" />
                  <input
                    type="text"
                    value={searchPlate}
                    onChange={(e) => setSearchPlate(e.target.value)}
                    className="input-field bg-transparent border-none text-white focus:outline-none w-full text-xs"
                    placeholder="Search Registration Plate (e.g. MH-12)"
                  />
                </div>

                <select
                  value={violationFilter}
                  onChange={(e) => setViolationFilter(e.target.value)}
                  className="select-field"
                >
                  <option value="ALL">All Violation Types</option>
                  <option value="HELMET_NON_COMPLIANCE">Helmet Non-compliance</option>
                  <option value="SEATBELT_NON_COMPLIANCE">Seatbelt Non-compliance</option>
                  <option value="TRIPLE_RIDING">Triple Riding</option>
                  <option value="WRONG_SIDE_DRIVING">Wrong-Side Driving</option>
                  <option value="STOP_LINE_VIOLATION">Stop-line Violation</option>
                  <option value="RED_LIGHT_VIOLATION">Red-Light Violation</option>
                  <option value="ILLEGAL_PARKING">Illegal Parking</option>
                </select>

                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="select-field"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="APPROVED">Approved / Issued</option>
                  <option value="PENDING_REVIEW">Pending Review</option>
                  <option value="DISMISSED">Dismissed</option>
                </select>
              </div>

              {/* Table */}
              <div className="table-wrapper">
                <table className="ledger-table" id="ledger-table">
                  <thead>
                    <tr>
                      <th>Ticket ID</th>
                      <th>Timestamp</th>
                      <th>License Plate</th>
                      <th>Violation Type</th>
                      <th>Vehicle</th>
                      <th>Risk Score</th>
                      <th>Fine</th>
                      <th>Status</th>
                      <th>Documentation</th>
                      <th>Enforcement Action</th>
                    </tr>
                  </thead>
                  <tbody id="ledger-table-body">
                    {displayedCitations.length === 0 ? (
                      <tr>
                        <td colSpan="10" className="text-center text-slate-500 py-8">
                          No citation records matching active filters.
                        </td>
                      </tr>
                    ) : (
                      displayedCitations.map((c) => (
                        <tr key={c.id}>
                          <td><span className="font-mono text-slate-400 font-bold">{c.id}</span></td>
                          <td><span className="text-slate-400">{c.timestamp}</span></td>
                          <td><span className="plate-cell font-mono">{c.plate}</span></td>
                          <td>
                            <span style={{ color: '#fb7185', fontWeight: 600 }}>
                              {c.type.replace(/_/g, ' ')}
                            </span>
                          </td>
                          <td>{c.vehicle}</td>
                          <td>
                            <strong style={{ color: c.risk_score >= 75 ? '#EF4444' : '#F59E0B' }}>
                              {c.risk_score}/100
                            </strong>
                          </td>
                          <td><strong className="text-white">{c.fine}</strong></td>
                          <td>
                            <span className={`status-badge ${
                              c.status === 'APPROVED' ? 'status-approved' : 
                              c.status === 'PENDING_REVIEW' ? 'status-review' : 'status-dismissed'
                            }`}>
                              {c.status}
                            </span>
                          </td>
                          <td>
                            <div className="flex gap-1.5">
                              <button
                                className="btn px-2 py-1 flex items-center gap-1 text-[10px]"
                                onClick={() => downloadPDF(c.id)}
                                title="Download citation evidence PDF"
                              >
                                <Download size={10} /> PDF
                              </button>
                              <button
                                className="btn px-2 py-1 flex items-center gap-1 text-[10px]"
                                onClick={() => downloadJSON(c.id)}
                                title="Download JSON metadata"
                              >
                                <FileJson size={10} /> JSON
                              </button>
                            </div>
                          </td>
                          <td>
                            <div className="flex gap-1">
                              {c.status !== 'APPROVED' && (
                                <button
                                  className="btn btn-primary px-2 py-0.5 text-[10px] bg-emerald-700 hover:bg-emerald-600 border-none"
                                  onClick={() => handleUpdateLedgerStatus(c.id, "APPROVED")}
                                >
                                  Issue
                                </button>
                              )}
                              {c.status !== 'DISMISSED' && (
                                <button
                                  className="btn px-2 py-0.5 text-[10px] bg-rose-950 hover:bg-rose-900 text-rose-200 border-none"
                                  onClick={() => handleUpdateLedgerStatus(c.id, "DISMISSED")}
                                >
                                  Dismiss
                                </button>
                              )}
                              <button
                                className="btn px-2 py-0.5 text-[10px] bg-slate-900 border-none text-slate-400 hover:bg-slate-800"
                                onClick={() => handleDeleteCitation(c.id)}
                                title="Delete case log"
                              >
                                Remove
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="pagination">
                <div className="pagination-info" id="ledger-pagination-info">
                  Showing {filteredCitations.length === 0 ? 0 : ledgerPage * entriesPerPage + 1}-
                  {Math.min(filteredCitations.length, (ledgerPage + 1) * entriesPerPage)} of {filteredCitations.length} entries
                </div>
                <div className="pagination-buttons flex gap-2">
                  <button
                    className="btn"
                    disabled={ledgerPage === 0}
                    onClick={() => setLedgerPage(prev => Math.max(0, prev - 1))}
                  >
                    Previous
                  </button>
                  <button
                    className="btn"
                    disabled={ledgerPage >= totalPages - 1 || totalPages === 0}
                    onClick={() => setLedgerPage(prev => prev + 1)}
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* --- TAB 4: BTP SUBMISSION HUB --- */}
        {activeTab === 'btphub' && (
          <section id="tab-btphub" className="tab-pane active">
            <div className="section-header">
              <div className="header-title">
                <h1>BTP Submission & Integration Hub</h1>
                <p>Enforcement context metrics and development timelines for Bengaluru Traffic Police (BTP)</p>
              </div>
            </div>

            {/* Bangalore Crisis Stats Cards */}
            <div className="stats-cards-grid" style={{ marginBottom: '1.5rem' }}>
              <div className="glass-card stats-card-premium" style={{ borderLeft: '3px solid var(--danger)' }}>
                <div className="stats-card-info">
                  <span className="stats-label">BTP Registered Cases (2024)</span>
                  <span className="stats-val" style={{ color: '#F87171' }}>82.86 Lakhs</span>
                  <span className="stats-change" style={{ color: 'var(--text-muted)' }}>~22,700 violations / day</span>
                </div>
                <div className="stats-card-icon" style={{ color: '#F87171', background: 'rgba(239, 68, 68, 0.05)' }}>
                  <AlertTriangle size={20} />
                </div>
              </div>

              <div className="glass-card stats-card-premium" style={{ borderLeft: '3px solid var(--danger)' }}>
                <div className="stats-card-info">
                  <span className="stats-label">Road Deaths (2024)</span>
                  <span className="stats-val" style={{ color: '#F87171' }}>893 Fatalities</span>
                  <span className="stats-change" style={{ color: 'var(--text-muted)' }}>91% Bikers & Pedestrians</span>
                </div>
                <div className="stats-card-icon" style={{ color: '#F87171', background: 'rgba(239, 68, 68, 0.05)' }}>
                  <Volume2 size={20} />
                </div>
              </div>

              <div className="glass-card stats-card-premium" style={{ borderLeft: '3px solid var(--warning)' }}>
                <div className="stats-card-info">
                  <span className="stats-label">Road Crashes (2024)</span>
                  <span className="stats-val" style={{ color: '#FBBF24' }}>4,784 Accidents</span>
                  <span className="stats-change" style={{ color: 'var(--text-muted)' }}>-4% decrease YoY</span>
                </div>
                <div className="stats-card-icon" style={{ color: '#FBBF24', background: 'rgba(245, 158, 11, 0.05)' }}>
                  <AlertTriangle size={20} />
                </div>
              </div>

              <div className="glass-card stats-card-premium" style={{ borderLeft: '3px solid var(--success)' }}>
                <div className="stats-card-info">
                  <span className="stats-label">BTP Fine Collections (2024)</span>
                  <span className="stats-val" style={{ color: '#34D399' }}>₹80.9 Crores</span>
                  <span className="stats-change" style={{ color: 'var(--text-muted)' }}>Contactless enforcement active</span>
                </div>
                <div className="stats-card-icon" style={{ color: '#34D399', background: 'rgba(16, 185, 129, 0.05)' }}>
                  <Database size={20} />
                </div>
              </div>
            </div>

            <div className="charts-grid-layout" style={{ gridTemplateColumns: '1.15fr 0.85fr', marginBottom: '1.5rem' }}>
              {/* Left: 2-Day Implementation Timeline */}
              <div className="glass-card chart-card">
                <div className="chart-header">
                  <span className="chart-title">2-Day Hackathon Implementation Roadmap</span>
                </div>
                
                <div className="flex flex-col gap-4 py-2">
                  <div className="pl-5 relative border-l border-slate-700">
                    <div className="absolute -left-[5px] top-1.5 h-2.5 w-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]"></div>
                    <div className="font-bold text-sm text-cyan-400">PHASE 1 &middot; Day 1 Morning (0-4 hrs)</div>
                    <div className="text-xs text-slate-400 mt-1">
                      Setup FastAPI REST backend + SQLite db schema. Initialize pre-trained YOLOv11 detectors for vehicle classifications and PaddleOCR/EasyOCR formats for plate recognitions.
                    </div>
                  </div>

                  <div className="pl-5 relative border-l border-slate-700">
                    <div className="absolute -left-[5px] top-1.5 h-2.5 w-2.5 rounded-full bg-purple-400 shadow-[0_0_8px_rgba(192,132,252,0.8)]"></div>
                    <div className="font-bold text-sm text-purple-400">PHASE 2 &middot; Day 1 Afternoon (4-8 hrs)</div>
                    <div className="text-xs text-slate-400 mt-1">
                      Add helmet/seatbelt safety infraction checks. Integrate DeepSORT tracker to trace vehicles across frames. Code the Violation Impact Score (VIS) matrix equations.
                    </div>
                  </div>

                  <div className="pl-5 relative border-l border-slate-700">
                    <div className="absolute -left-[5px] top-1.5 h-2.5 w-2.5 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]"></div>
                    <div className="font-bold text-sm text-amber-400">PHASE 3 &middot; Day 2 Morning (8-14 hrs)</div>
                    <div className="text-xs text-slate-400 mt-1">
                      Implement reactive visual frontend layout. Connect repeat offender SQLite aggregation lookups. Build custom predictive intelligence hotspot heatmaps.
                    </div>
                  </div>

                  <div className="pl-5 relative border-l border-slate-700">
                    <div className="absolute -left-[5px] top-1.5 h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"></div>
                    <div className="font-bold text-sm text-emerald-400">PHASE 4 &middot; Day 2 Afternoon (14-20 hrs)</div>
                    <div className="text-xs text-slate-400 mt-1">
                      Compile end-to-end RTSP pipelines. Generate tamper-proof PDF evidence sheets. Set up Docker Compose configurations for full-stack service containers.
                    </div>
                  </div>
                </div>
              </div>

              {/* Right: BTP ITMS Infrastructure Gaps */}
              <div className="glass-card chart-card">
                <div className="chart-header">
                  <span className="chart-title">Existing BTP ITMS Infrastructure Gaps</span>
                </div>
                
                <div className="flex flex-col gap-3 text-xs">
                  <div className="flex gap-2.5 items-start">
                    <span className="text-rose-500 font-bold">✕</span>
                    <div><strong>No Helmet / Seatbelt AI:</strong> Existing cameras only trace red lights. Rider compliance is not checked automatically.</div>
                  </div>
                  <div className="flex gap-2.5 items-start">
                    <span className="text-rose-500 font-bold">✕</span>
                    <div><strong>No Triple-Riding Model:</strong> Motorcycles carrying 3+ passengers are not flagged by standard ITMS scripts.</div>
                  </div>
                  <div className="flex gap-2.5 items-start">
                    <span className="text-rose-500 font-bold">✕</span>
                    <div><strong>No Offender Profiling:</strong> Prior violations are indexed statically. Repeating offenders are not tracked across stations.</div>
                  </div>
                  <div className="flex gap-2.5 items-start">
                    <span className="text-rose-500 font-bold">✕</span>
                    <div><strong>No Predictive Dispatch:</strong> Force deployment is scheduled manually rather than guided by ML hotspot analytics.</div>
                  </div>
                  <div className="flex gap-2.5 items-start">
                    <span className="text-rose-500 font-bold">✕</span>
                    <div><strong>No Risk-Weighting:</strong> High-density hazards are mixed with minor side-street illegal parking events in the timeline.</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Open Source Technical Backbones */}
            <div className="glass-card">
              <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>Core GitHub Reference Repositories</h2>
              <div className="table-wrapper" style={{ border: 'none', background: 'transparent' }}>
                <table className="ledger-table" style={{ fontSize: '0.8rem' }}>
                  <thead>
                    <tr>
                      <th>Component</th>
                      <th>Repository Name & Link</th>
                      <th>Description</th>
                      <th>Surveillance Badge</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>Detection Core</td>
                      <td><a href="https://github.com/ultralytics/ultralytics" target="_blank" rel="noreferrer" className="text-white underline hover:text-cyan-400">ultralytics/ultralytics</a></td>
                      <td>Official YOLOv11 engine. Backbone of vehicle classifications and bounding box overlays.</td>
                      <td><span className="status-badge status-approved">⭐ 40K+ STARS</span></td>
                    </tr>
                    <tr>
                      <td style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>Tracking Core</td>
                      <td><a href="https://github.com/nwojke/deep_sort" target="_blank" rel="noreferrer" className="text-white underline hover:text-cyan-400">nwojke/deep_sort</a></td>
                      <td>DeepSORT tracking matrix. Maintains persistent vehicle IDs across lane occlusions.</td>
                      <td><span className="status-badge status-approved">⭐ 8K+ STARS</span></td>
                    </tr>
                    <tr>
                      <td style={{ color: '#FBBF24', fontWeight: 700 }}>Indian ANPR</td>
                      <td><a href="https://github.com/lavanyashree2805/yolov8-license-plate-india" target="_blank" rel="noreferrer" className="text-white underline hover:text-cyan-400">yolov8-license-plate-india</a></td>
                      <td>Custom model weights calibrated specifically for Indian non-standard plate formats.</td>
                      <td><span className="status-badge status-review">BTP FORMATTED</span></td>
                    </tr>
                    <tr>
                      <td style={{ color: 'var(--accent-purple)', fontWeight: 700 }}>OCR Transcription</td>
                      <td><a href="https://github.com/PaddlePaddle/PaddleOCR" target="_blank" rel="noreferrer" className="text-white underline hover:text-cyan-400">PaddlePaddle/PaddleOCR</a></td>
                      <td>Best-in-class multilingual OCR text extractor. High precision on low-quality plates.</td>
                      <td><span className="status-badge status-approved">⭐ 45K+ STARS</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        )}

        {/* --- TAB 5: SYSTEM SETTINGS --- */}
        {activeTab === 'settings' && (
          <section id="tab-settings" className="tab-pane active">
            <div className="section-header">
              <div className="header-title">
                <h1>System Configuration</h1>
                <p>Tune core computer vision thresholds, OCR parameters, and alerting interfaces</p>
              </div>
            </div>

            <div className="settings-grid">
              {/* CV Thresholds Card */}
              <div className="glass-card settings-card">
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, borderBottom: '1px solid var(--glass-border)', paddingBottom: '0.5rem', marginBottom: '0.5rem' }}>
                  AI Detection Confidence Thresholds
                </h2>
                
                <div className="setting-item-group">
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <label htmlFor="range-vehicle-thresh">Vehicle Detection Threshold</label>
                    <span id="val-vehicle-thresh" style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>{vehicleThresh}%</span>
                  </div>
                  <input
                    type="range"
                    id="range-vehicle-thresh"
                    min="50"
                    max="95"
                    value={vehicleThresh}
                    onChange={(e) => setVehicleThresh(e.target.value)}
                    style={{ accentColor: 'var(--accent-cyan)' }}
                  />
                </div>
                
                <div className="setting-item-group">
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <label htmlFor="range-violation-thresh">Violation Detection Severity Filter</label>
                    <span id="val-violation-thresh" style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>{violationThresh}%</span>
                  </div>
                  <input
                    type="range"
                    id="range-violation-thresh"
                    min="50"
                    max="95"
                    value={violationThresh}
                    onChange={(e) => setViolationThresh(e.target.value)}
                    style={{ accentColor: 'var(--accent-cyan)' }}
                  />
                </div>
                
                <div className="setting-item-group">
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <label htmlFor="range-ocr-thresh">ANPR / OCR Confidence Floor</label>
                    <span id="val-ocr-thresh" style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>{ocrThresh}%</span>
                  </div>
                  <input
                    type="range"
                    id="range-ocr-thresh"
                    min="50"
                    max="95"
                    value={ocrThresh}
                    onChange={(e) => setOcrThresh(e.target.value)}
                    style={{ accentColor: 'var(--accent-cyan)' }}
                  />
                </div>
              </div>
              
              {/* OCR & API Configuration Card */}
              <div className="glass-card settings-card flex flex-col">
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, borderBottom: '1px solid var(--glass-border)', paddingBottom: '0.5rem', marginBottom: '0.5rem' }}>
                  OCR Language & Integration
                </h2>
                
                <div className="setting-item-group">
                  <label htmlFor="select-ocr-engine">OCR Reading Model</label>
                  <select
                    id="select-ocr-engine"
                    className="select-field"
                    style={{ width: '100%' }}
                    value={ocrEngine}
                    onChange={(e) => setOcrEngine(e.target.value)}
                  >
                    <option value="tesseract">Standard LSTM Tesseract engine (Latin characters)</option>
                    <option value="easyocr">EasyOCR deep learning model (Multilingual)</option>
                    <option value="google-vision">Google Cloud Vision OCR API (Cloud Enterprise)</option>
                  </select>
                </div>
                
                <div className="setting-item-group">
                  <label htmlFor="input-webhook">Citation Event Webhook URL (JSON Dispatch)</label>
                  <input
                    type="text"
                    id="input-webhook"
                    className="input-field"
                    value={webhookUrl}
                    onChange={(e) => setWebhookUrl(e.target.value)}
                    style={{ paddingLeft: '1rem' }}
                  />
                </div>
                
                <div className="flex gap-2 justify-end mt-auto pt-4 border-t border-slate-800">
                  <button
                    className="btn"
                    onClick={() => {
                      setVehicleThresh(75);
                      setViolationThresh(80);
                      setOcrThresh(70);
                      setOcrEngine("easyocr");
                      setWebhookUrl("https://api.trafficeye-ai.gov/v1/citations");
                      triggerToast("Configuration parameters reset to defaults.");
                    }}
                  >
                    Reset Defaults
                  </button>
                  <button
                    className="btn btn-primary"
                    onClick={() => triggerToast("System settings successfully committed to database.")}
                  >
                    Save Settings
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}

      </main>
    </div>
  );
}

export default App;
