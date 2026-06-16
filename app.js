// TrafficEye AI - Core Controller

// --- Mock Scenarios Definitions ---
const SCENARIOS = [
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
    severity: "danger", // high risk
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
    severity: "danger", // high risk
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
    severity: "warning", // medium risk
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
    severity: "info", // low risk
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

// --- Default Seed Violations Database (Configured with Repeat Offender patterns) ---
const SEED_VIOLATIONS = [
  { id: "TKT-6623", timestamp: "2026-06-15 08:32", plate: "MH-12-JN-8832", type: "HELMET_NON_COMPLIANCE", vehicle: "Motorcycle", riskScore: 78, confidence: "96%", fine: "$150.00", status: "PENDING_REVIEW" },
  { id: "TKT-6590", timestamp: "2026-06-15 10:14", plate: "KA-51-MD-9041", type: "RED_LIGHT_VIOLATION", vehicle: "Sedan", riskScore: 92, confidence: "95%", fine: "$300.00", status: "APPROVED" },
  { id: "TKT-6541", timestamp: "2026-06-15 11:45", plate: "DL-03-CB-5512", type: "SEATBELT_NON_COMPLIANCE", vehicle: "SUV", riskScore: 64, confidence: "89%", fine: "$120.00", status: "APPROVED" },
  { id: "TKT-6430", timestamp: "2026-06-15 13:20", plate: "TX-99-ER-0043", type: "ILLEGAL_PARKING", vehicle: "Delivery Van", riskScore: 45, confidence: "94%", fine: "$100.00", status: "DISMISSED" },
  { id: "TKT-6391", timestamp: "2026-06-14 15:40", plate: "MH-12-JN-8832", type: "STOP_LINE_VIOLATION", vehicle: "Motorcycle", riskScore: 62, confidence: "84%", fine: "$80.00", status: "APPROVED" },
  { id: "TKT-6302", timestamp: "2026-06-14 17:15", plate: "DL-01-AA-9999", type: "WRONG_SIDE_DRIVING", vehicle: "SUV", riskScore: 88, confidence: "97%", fine: "$250.00", status: "APPROVED" },
  { id: "TKT-6298", timestamp: "2026-06-14 19:42", plate: "KA-51-MD-9041", type: "TRIPLE_RIDING", vehicle: "Sedan", riskScore: 82, confidence: "93%", fine: "$150.00", status: "APPROVED" },
  { id: "TKT-6112", timestamp: "2026-06-13 21:05", plate: "MH-12-JN-8832", type: "HELMET_NON_COMPLIANCE", vehicle: "Motorcycle", riskScore: 78, confidence: "91%", fine: "$150.00", status: "APPROVED" }
];

// --- Map of Hotspot Locations ---
const HOTSPOTS = [
  { name: "Sector-4 Crossroads", x: 180, y: 140, risk: 88, peak: "18:00 - 20:00", patrol: "3 Patrol Officers" },
  { name: "Gravel Junction", x: 380, y: 80, risk: 91, peak: "08:00 - 10:00", patrol: "4 Patrol Officers" },
  { name: "Expressway Exit 7", x: 550, y: 200, risk: 64, peak: "14:00 - 16:00", patrol: "2 Patrol Officers" },
  { name: "Downtown Boulevard", x: 280, y: 230, risk: 45, peak: "12:00 - 13:00", patrol: "1 Curb Officer" }
];

// --- Application State ---
let violationsList = [];
let currentScenario = SCENARIOS[0];
let preprocessMode = false;
let isAnalysisRunning = false;
let ledgerPage = 1;
const ledgerPageSize = 5;

// --- DOM References ---
const navItems = document.querySelectorAll(".nav-item");
const tabPanes = document.querySelectorAll(".tab-pane");
const scenariosListContainer = document.getElementById("scenarios-list");
const canvas = document.getElementById("image-canvas");
const ctx = canvas.getContext("2d");
const canvasViewport = document.getElementById("canvas-viewport");
const scanLine = document.getElementById("scan-line");
const detectionPopup = document.getElementById("detection-popup");
const btnRunAnalysis = document.getElementById("btn-run-analysis");
const btnTogglePreprocess = document.getElementById("toggle-preprocess");
const plateOcrBox = document.getElementById("plate-ocr-box");
const ocrConfElement = document.getElementById("ocr-conf");

// Evidence Panel
const evidenceSeverity = document.getElementById("violation-severity");
const evidencePreview = document.getElementById("evidence-preview-img");
const plateMagnifier = document.getElementById("plate-magnifier");
const metaTicketId = document.getElementById("meta-ticket-id");
const metaType = document.getElementById("meta-type");
const metaRisk = document.getElementById("meta-risk");
const metaPlate = document.getElementById("meta-plate");
const metaOffenderStatus = document.getElementById("meta-offender-status");
const metaConfidence = document.getElementById("meta-confidence");
const metaVehicleClass = document.getElementById("meta-vehicle-class");
const metaTime = document.getElementById("meta-time");
const metaFine = document.getElementById("meta-fine");
const btnApprove = document.getElementById("btn-approve-violation");
const btnReview = document.getElementById("btn-review-violation");
const btnDismiss = document.getElementById("btn-dismiss-violation");

// Upload Element
const uploadZone = document.getElementById("upload-zone");
const fileUploader = document.getElementById("file-uploader");

// Settings
const rangeVehicleThresh = document.getElementById("range-vehicle-thresh");
const rangeViolationThresh = document.getElementById("range-violation-thresh");
const rangeOcrThresh = document.getElementById("range-ocr-thresh");
const valVehicleThresh = document.getElementById("val-vehicle-thresh");
const valViolationThresh = document.getElementById("val-violation-thresh");
const valOcrThresh = document.getElementById("val-ocr-thresh");
const selectOcrEngine = document.getElementById("select-ocr-engine");
const inputWebhook = document.getElementById("input-webhook");
const btnResetSettings = document.getElementById("btn-reset-settings");
const btnSaveSettings = document.getElementById("btn-save-settings");

// Ledger Elements
const searchPlate = document.getElementById("search-plate");
const filterViolation = document.getElementById("filter-violation");
const filterStatus = document.getElementById("filter-status");
const ledgerTableBody = document.getElementById("ledger-table-body");
const ledgerPaginationInfo = document.getElementById("ledger-pagination-info");
const btnLedgerPrev = document.getElementById("btn-ledger-prev");
const btnLedgerNext = document.getElementById("btn-ledger-next");
const btnExportLedger = document.getElementById("btn-export-ledger");

const API_BASE = "http://127.0.0.1:8000/api";

async function fetchCitations() {
  try {
    const res = await fetch(`${API_BASE}/citations`);
    if (res.ok) {
      const data = await res.json();
      violationsList = data.map(v => ({
        id: v.id,
        timestamp: v.timestamp,
        plate: v.plate,
        type: v.type,
        vehicle: v.vehicle,
        riskScore: v.risk_score,
        confidence: v.confidence,
        fine: v.fine,
        status: v.status
      }));
    }
  } catch (err) {
    console.error("Failed to fetch citations from backend:", err);
    const storedList = localStorage.getItem("atv_violations");
    if (storedList) {
      violationsList = JSON.parse(storedList);
    } else {
      violationsList = [...SEED_VIOLATIONS];
      localStorage.setItem("atv_violations", JSON.stringify(violationsList));
    }
  }
}

async function refreshData() {
  await fetchCitations();
  updateDashboardMetrics();
  renderLedgerTable();
}

// --- Initialization ---
async function init() {
  loadSettingsFromStorage();

  setupNavigation();
  renderScenariosList();
  selectScenario(SCENARIOS[0].id);
  setupUploadZone();
  setupSettingsListeners();
  setupLedgerListeners();
  setupEvidenceActions();
  
  await refreshData();

  window.addEventListener("resize", () => {
    drawScenarioScene(currentScenario, preprocessMode);
  });
}

// --- Navigation Layout ---
function setupNavigation() {
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      navItems.forEach(nav => nav.classList.remove("active"));
      item.classList.add("active");
      
      const tabId = item.getAttribute("data-tab");
      tabPanes.forEach(pane => {
        pane.classList.remove("active");
        if (pane.id === `tab-${tabId}`) {
          pane.classList.add("active");
        }
      });

      if (tabId === "analytics") {
        updateDashboardMetrics();
      } else if (tabId === "ledger") {
        renderLedgerTable();
      }
    });
  });
}

// --- Scenario Selector ---
function renderScenariosList() {
  scenariosListContainer.innerHTML = "";
  SCENARIOS.forEach(sc => {
    const card = document.createElement("div");
    card.className = "scenario-card";
    card.id = `scenario-card-${sc.id}`;
    card.setAttribute("data-id", sc.id);
    
    let badgeClass = "tag-normal";
    if (sc.tag === "low-light") badgeClass = "tag-lowlight";
    else if (sc.tag === "weather") badgeClass = "tag-weather";
    else if (sc.tag === "shadows") badgeClass = "tag-shadows";
    else if (sc.tag === "live") badgeClass = "tag-live";

    card.innerHTML = `
      <div class="scenario-title">${sc.title}</div>
      <div class="scenario-desc">${sc.desc}</div>
      <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.5rem;">
        <span class="scenario-tag ${badgeClass}">${sc.tag}</span>
        <span style="font-size:0.75rem; color:var(--text-secondary); font-weight:600;">Risk Index: ${sc.riskScore}</span>
      </div>
    `;

    card.addEventListener("click", () => selectScenario(sc.id));
    scenariosListContainer.appendChild(card);
  });
}

let webcamStream = null;
let webcamVideo = null;
let webcamInterval = null;
let isWebcamActive = false;
let isWebcamProcessing = false;
let lastAutoIssuedTime = 0;
let lastAutoIssuedPlate = "";
let lastAutoIssuedType = "";

function selectScenario(id) {
  document.querySelectorAll(".scenario-card").forEach(c => c.classList.remove("active"));
  
  const selectedCard = document.getElementById(`scenario-card-${id}`);
  if (selectedCard) selectedCard.classList.add("active");

  // Cleanup existing webcam stream and intervals
  if (webcamStream) {
    webcamStream.getTracks().forEach(track => track.stop());
    webcamStream = null;
  }
  if (webcamVideo) {
    webcamVideo.pause();
    webcamVideo = null;
  }
  if (webcamInterval) {
    clearInterval(webcamInterval);
    webcamInterval = null;
  }
  isWebcamActive = false;

  const scObj = SCENARIOS.find(sc => sc.id === id);
  if (scObj) {
    currentScenario = scObj;
    preprocessMode = false;
    isAnalysisRunning = false;
    
    btnTogglePreprocess.textContent = "Original View";
    btnTogglePreprocess.classList.remove("btn-primary");
    
    document.getElementById("pipeline-status-indicator").textContent = "SYSTEM IDLE";
    document.getElementById("pipeline-status-indicator").className = "severity-badge badge-info";
    
    plateOcrBox.textContent = "-- READY --";
    ocrConfElement.textContent = "0%";
    
    btnRunAnalysis.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run AI Pipeline`;
    
    resetEvidencePanel();
    
    if (id === "live_webcam") {
      isWebcamActive = true;
      navigator.mediaDevices.getUserMedia({ video: { width: 800, height: 380 } })
        .then(stream => {
          webcamStream = stream;
          webcamVideo = document.createElement("video");
          webcamVideo.srcObject = stream;
          webcamVideo.autoplay = true;
          webcamVideo.playsInline = true;
          webcamVideo.onloadedmetadata = () => {
            webcamVideo.play();
            drawWebcamLoop();
          };
        })
        .catch(err => {
          console.error("Webcam access denied:", err);
          showToastNotification("Webcam access denied. Please grant permissions.");
        });
    } else {
      drawScenarioScene(currentScenario, preprocessMode);
    }
  }
}

function drawWebcamLoop() {
  if (!isWebcamActive || !webcamVideo) return;
  drawScenarioScene(currentScenario, preprocessMode);
  requestAnimationFrame(drawWebcamLoop);
}

// --- Dynamic Canvas Drawings ---
function drawScenarioScene(scenario, enhanced = false) {
  canvas.width = 800;
  canvas.height = 380;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  ctx.fillStyle = "#1e293b";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  
  if (scenario.imageType === "webcam" && webcamVideo) {
    ctx.drawImage(webcamVideo, 0, 0, canvas.width, canvas.height);
    if (enhanced) {
      const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imgData.data;
      for (let i = 0; i < data.length; i += 4) {
        data[i] = Math.min(255, data[i] * 1.25 + 10);
        data[i+1] = Math.min(255, data[i+1] * 1.25 + 10);
        data[i+2] = Math.min(255, data[i+2] * 1.25 + 10);
      }
      ctx.putImageData(imgData, 0, 0);
    }
  } else if (scenario.imageElement) {
    ctx.drawImage(scenario.imageElement, 0, 0, canvas.width, canvas.height);
    if (enhanced) {
      const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imgData.data;
      for (let i = 0; i < data.length; i += 4) {
        data[i] = Math.min(255, data[i] * 1.25 + 10);
        data[i+1] = Math.min(255, data[i+1] * 1.25 + 10);
        data[i+2] = Math.min(255, data[i+2] * 1.25 + 10);
      }
      ctx.putImageData(imgData, 0, 0);
    }
  } else if (scenario.imageType === "canvas_draw_helmet") {
    drawHelmetScene(ctx, enhanced);
  } else if (scenario.imageType === "canvas_draw_redlight") {
    drawRedLightScene(ctx, enhanced);
  } else if (scenario.imageType === "canvas_draw_seatbelt") {
    drawSeatbeltScene(ctx, enhanced);
  } else if (scenario.imageType === "canvas_draw_parking") {
    drawParkingScene(ctx, enhanced);
  } else {
    drawCustomImagePlaceholder(ctx, scenario.customName || "Uploaded Camera Stream");
  }

  if (isAnalysisRunning && !preprocessMode) {
    drawBoundingBoxes(scenario.boxes);
  }
}

// Draw Motorcycle scene
function drawHelmetScene(c, enhanced) {
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
    applyCameraGrain(c, 0.45);
    applyColorMutedness(c, 0.7);
  }
}

// Draw Red Light scene
function drawRedLightScene(c, enhanced) {
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
  for (let r = 0; r < rainCount; r++) {
    let rx = Math.random() * 800;
    let ry = Math.random() * 380;
    c.beginPath();
    c.moveTo(rx, ry);
    c.lineTo(rx - 8, ry + 22);
    c.stroke();
  }

  if (!enhanced) {
    applyWaterSplashes(c);
  }
}

// Draw seatbelt scene
function drawSeatbeltScene(c, enhanced) {
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

  if (!enhanced) {
    applyMotionBlur(c);
  }
}

// Draw illegal parking scene
function drawParkingScene(c, enhanced) {
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
}

function drawCustomImagePlaceholder(c, name) {
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
  c.fillText("Custom user uploaded image stream.", 400, 220);
  c.textAlign = "left";
}

function applyCameraGrain(c, opacity) {
  const imgData = c.getImageData(0, 0, 800, 380);
  const data = imgData.data;
  for (let i = 0; i < data.length; i += 4) {
    const noise = (Math.random() - 0.5) * 80 * opacity;
    data[i] = Math.min(255, Math.max(0, data[i] + noise));
    data[i+1] = Math.min(255, Math.max(0, data[i+1] + noise));
    data[i+2] = Math.min(255, Math.max(0, data[i+2] + noise));
  }
  c.putImageData(imgData, 0, 0);
}

function applyColorMutedness(c, factor) {
  c.fillStyle = `rgba(15, 23, 42, ${factor * 0.3})`;
  c.fillRect(0, 0, 800, 380);
}

function applyWaterSplashes(c) {
  c.fillStyle = "rgba(255, 255, 255, 0.08)";
  for(let s = 0; s < 12; s++) {
    c.beginPath();
    c.arc(Math.random()*800, Math.random()*380, Math.random()*25 + 5, 0, Math.PI*2);
    c.fill();
  }
}

function applyMotionBlur(c) {
  c.fillStyle = "rgba(255, 255, 255, 0.12)";
  for(let j=0; j<8; j++) {
    c.fillRect(0, Math.random()*380, 800, Math.random()*15 + 2);
  }
}

function applyShadowGlare(c) {
  c.fillStyle = "rgba(0, 0, 0, 0.25)";
  c.fillRect(0, 180, 800, 200);
}

function drawBoundingBoxes(boxes) {
  if (!boxes) return;
  boxes.forEach(box => {
    const bx = (box.x / 100) * canvas.width;
    const by = (box.y / 100) * canvas.height;
    const bw = (box.w / 100) * canvas.width;
    const bh = (box.h / 100) * canvas.height;

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
}

// Interactive popup boxes
canvas.addEventListener("mousemove", (e) => {
  if (!isAnalysisRunning || preprocessMode) {
    detectionPopup.style.opacity = 0;
    return;
  }
  
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  
  const mouseX = (e.clientX - rect.left) * scaleX;
  const mouseY = (e.clientY - rect.top) * scaleY;

  let hoveredBox = null;
  const boxes = currentScenario.boxes;
  if (!boxes) return;

  for (let k = 0; k < boxes.length; k++) {
    const box = boxes[k];
    const bx = (box.x / 100) * canvas.width;
    const by = (box.y / 100) * canvas.height;
    const bw = (box.w / 100) * canvas.width;
    const bh = (box.h / 100) * canvas.height;

    if (mouseX >= bx && mouseX <= bx + bw && mouseY >= by && mouseY <= by + bh) {
      hoveredBox = box;
      break;
    }
  }

  if (hoveredBox) {
    const popX = (hoveredBox.x + hoveredBox.w/2) / 100 * rect.width;
    const popY = (hoveredBox.y) / 100 * rect.height;
    
    detectionPopup.style.left = `${popX}px`;
    detectionPopup.style.top = `${popY}px`;
    detectionPopup.innerHTML = `
      <div style="font-weight: 700; color: ${hoveredBox.color}">${hoveredBox.label}</div>
      <div style="color: var(--text-secondary); margin-top: 2px;">CV Score: <strong>${hoveredBox.conf}</strong></div>
    `;
    detectionPopup.style.opacity = 1;
  } else {
    detectionPopup.style.opacity = 0;
  }
});

canvas.addEventListener("mouseleave", () => {
  detectionPopup.style.opacity = 0;
});

// --- Upload Zone ---
function setupUploadZone() {
  uploadZone.addEventListener("click", () => {
    fileUploader.click();
  });
  
  fileUploader.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = function(event) {
        const imgEl = new Image();
        imgEl.onload = function() {
          const customName = file.name;
          const customId = "uploaded_" + Date.now();
          const customScenario = {
            id: customId,
            title: "Upload: " + customName.substring(0, 15),
            desc: "User uploaded photo analyzed by live YOLOv11 & OCR.",
            tag: "uploaded",
            imageType: "custom",
            customName: customName,
            rawFile: file,
            imageElement: imgEl,
            vehicleClass: "Automobile",
            violationType: "HELMET_NON_COMPLIANCE",
            severity: "warning",
            riskScore: 68,
            fine: "$150.00",
            plate: "AP-39-AB-1234",
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
          
          currentScenario = customScenario;
          preprocessMode = false;
          isAnalysisRunning = false;
          btnTogglePreprocess.textContent = "Original View";
          btnTogglePreprocess.classList.remove("btn-primary");
          
          document.getElementById("pipeline-status-indicator").textContent = "SYSTEM IDLE";
          document.getElementById("pipeline-status-indicator").className = "severity-badge badge-info";
          
          plateOcrBox.textContent = "-- READY --";
          ocrConfElement.textContent = "0%";
          
          resetEvidencePanel();
          drawScenarioScene(currentScenario, preprocessMode);
        };
        imgEl.src = event.target.result;
      };
      reader.readAsDataURL(file);
    }
  });
}

// Toggle filters
btnTogglePreprocess.addEventListener("click", () => {
  preprocessMode = !preprocessMode;
  btnTogglePreprocess.textContent = preprocessMode ? "Enhanced View" : "Original View";
  if (preprocessMode) {
    btnTogglePreprocess.classList.add("btn-primary");
  } else {
    btnTogglePreprocess.classList.remove("btn-primary");
  }
  drawScenarioScene(currentScenario, preprocessMode);
});

// Run AI Detection Trigger
btnRunAnalysis.addEventListener("click", () => {
  if (currentScenario.id === "live_webcam") {
    if (isAnalysisRunning) {
      isAnalysisRunning = false;
      isWebcamProcessing = false;
      if (webcamInterval) {
        clearInterval(webcamInterval);
        webcamInterval = null;
      }
      canvasViewport.classList.remove("scan-active");
      btnRunAnalysis.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run AI Pipeline`;
      document.getElementById("pipeline-status-indicator").textContent = "SYSTEM IDLE";
      document.getElementById("pipeline-status-indicator").className = "severity-badge badge-info";
      currentScenario.boxes = [];
      resetEvidencePanel();
    } else {
      isAnalysisRunning = true;
      canvasViewport.classList.add("scan-active");
      btnRunAnalysis.innerHTML = "Stop AI Pipeline";
      document.getElementById("pipeline-status-indicator").textContent = "PROCESSING AI";
      document.getElementById("pipeline-status-indicator").className = "severity-badge badge-warning";
      
      captureWebcamFrame();
      webcamInterval = setInterval(captureWebcamFrame, 1500);
    }
    return;
  }

  if (isAnalysisRunning) return;
  
  isAnalysisRunning = true;
  canvasViewport.classList.add("scan-active");
  document.getElementById("pipeline-status-indicator").textContent = "PROCESSING AI";
  document.getElementById("pipeline-status-indicator").className = "severity-badge badge-warning";
  
  preprocessMode = false;
  btnTogglePreprocess.textContent = "Original View";
  btnTogglePreprocess.classList.remove("btn-primary");
  drawScenarioScene(currentScenario, false);

  plateOcrBox.textContent = "DECODING...";
  ocrConfElement.textContent = "---";

  if (currentScenario.rawFile) {
    const formData = new FormData();
    formData.append("file", currentScenario.rawFile);
    sendToBackendAnalyze(formData);
  } else {
    canvas.toBlob((blob) => {
      const formData = new FormData();
      formData.append("file", blob, `${currentScenario.id}.png`);
      sendToBackendAnalyze(formData);
    }, "image/png");
  }
});

async function captureWebcamFrame() {
  if (!isWebcamActive || !isAnalysisRunning || isWebcamProcessing) return;
  
  isWebcamProcessing = true;
  canvas.toBlob((blob) => {
    if (!blob) {
      isWebcamProcessing = false;
      return;
    }
    const formData = new FormData();
    formData.append("file", blob, "webcam_frame.png");
    
    fetch(`${API_BASE}/analyze`, {
      method: "POST",
      body: formData
    })
    .then(res => {
      if (res.ok) return res.json();
      throw new Error("Analysis failed");
    })
    .then(result => {
      isWebcamProcessing = false;
      if (!result || !isAnalysisRunning) return;
      
      currentScenario.plate = result.plate;
      currentScenario.ocrConfidence = result.ocr_confidence;
      currentScenario.violationType = result.violation_type;
      currentScenario.riskScore = result.risk_score;
      currentScenario.confidence = result.detections && result.detections.length > 0 ? result.detections[0].confidence : 90;
      currentScenario.details = result.details;
      currentScenario.vehicleClass = result.vehicle || "Automobile";
      currentScenario.fine = result.fine || "$150.00";
      
      if (result.detections) {
        currentScenario.boxes = result.detections.map(det => {
          const [x1, y1, x2, y2] = det.box;
          const rx = (x1 / canvas.width) * 100;
          const ry = (y1 / canvas.height) * 100;
          const rw = ((x2 - x1) / canvas.width) * 100;
          const rh = ((y2 - y1) / canvas.height) * 100;
          
          let color = "#EF4444";
          if (det.class.toLowerCase().includes("plate")) color = "#F59E0B";
          else if (["car", "suv", "sedan", "vehicle", "motorcycle"].includes(det.class.toLowerCase())) color = "#10B981";
          
          return {
            x: rx, y: ry, w: rw, h: rh,
            label: det.class,
            conf: `${det.confidence}%`,
            color: color
          };
        });
      }
      
      const isRealViolation = result.violation_type && result.violation_type !== "NO_VIOLATION" && result.violation_type !== "NONE";
      
      if (isRealViolation) {
        document.getElementById("pipeline-status-indicator").textContent = "VIOLATION CAPTURED";
        document.getElementById("pipeline-status-indicator").className = "severity-badge badge-danger";
      } else {
        document.getElementById("pipeline-status-indicator").textContent = "MONITORING SECURE";
        document.getElementById("pipeline-status-indicator").className = "severity-badge badge-success";
      }
      
      plateOcrBox.textContent = result.plate;
      ocrConfElement.textContent = result.ocr_confidence + "%";
      
      populateEvidencePanel(currentScenario);
      
      // Auto-issue citation logic with duplicate and time throttling
      if (isRealViolation) {
        const now = Date.now();
        const isDuplicate = (result.plate === lastAutoIssuedPlate && result.violation_type === lastAutoIssuedType);
        const elapsed = now - lastAutoIssuedTime;
        
        if (!isDuplicate || elapsed > 15000) {
          lastAutoIssuedTime = now;
          lastAutoIssuedPlate = result.plate;
          lastAutoIssuedType = result.violation_type;
          
          const citationData = {
            timestamp: result.timestamp || new Date().toISOString().slice(0, 19).replace('T', ' '),
            plate: result.plate,
            type: result.violation_type,
            vehicle: result.vehicle || "Automobile",
            risk_score: result.risk_score,
            confidence: (result.ocr_confidence || 90) + "%",
            fine: result.fine || "$150.00",
            status: "APPROVED"
          };
          
          fetch(`${API_BASE}/citations`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify(citationData)
          })
          .then(cRes => {
            if (cRes.ok) {
              showToastNotification(`Auto-issued Citation for ${result.violation_type.replace(/_/g, ' ')}`);
              refreshData();
            }
          })
          .catch(cErr => console.error("Auto-issue citation request failed:", cErr));
        }
      }
    })
    .catch(err => {
      isWebcamProcessing = false;
      console.error("Webcam frame analysis error:", err);
    });
  }, "image/png");
}

async function sendToBackendAnalyze(formData) {
  try {
    const res = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      body: formData
    });
    
    if (!res.ok) throw new Error("Backend analysis failed");
    const result = await res.json();
    
    canvasViewport.classList.remove("scan-active");
    
    const isRealViolation = result.violation_type && result.violation_type !== "NO_VIOLATION" && result.violation_type !== "NONE";
    if (isRealViolation) {
      document.getElementById("pipeline-status-indicator").textContent = "VIOLATION CAPTURED";
      document.getElementById("pipeline-status-indicator").className = "severity-badge badge-danger";
    } else {
      document.getElementById("pipeline-status-indicator").textContent = "MONITORING SECURE";
      document.getElementById("pipeline-status-indicator").className = "severity-badge badge-success";
    }
    
    currentScenario.plate = result.plate;
    currentScenario.ocrConfidence = result.ocr_confidence;
    currentScenario.violationType = result.violation_type;
    currentScenario.riskScore = result.risk_score;
    currentScenario.confidence = result.detections && result.detections.length > 0 ? result.detections[0].confidence : 90;
    currentScenario.details = result.details;
    currentScenario.vehicleClass = result.vehicle || "Automobile";
    currentScenario.fine = result.fine || "$150.00";
    
    if (result.detections) {
      const imgWidth = currentScenario.imageElement ? currentScenario.imageElement.naturalWidth : 800;
      const imgHeight = currentScenario.imageElement ? currentScenario.imageElement.naturalHeight : 380;
      
      currentScenario.boxes = result.detections.map(det => {
        const [x1, y1, x2, y2] = det.box;
        const rx = (x1 / imgWidth) * 100;
        const ry = (y1 / imgHeight) * 100;
        const rw = ((x2 - x1) / imgWidth) * 100;
        const rh = ((y2 - y1) / imgHeight) * 100;
        
        let color = "#EF4444";
        if (det.class.toLowerCase().includes("plate")) color = "#F59E0B";
        else if (["car", "suv", "sedan", "vehicle", "motorcycle"].includes(det.class.toLowerCase())) color = "#10B981";
        
        return {
          x: rx,
          y: ry,
          w: rw,
          h: rh,
          label: det.class,
          conf: `${det.confidence}%`,
          color: color
        };
      });
    }
    
    drawScenarioScene(currentScenario, false);
    animateOCR(result.plate, result.ocr_confidence);
    populateEvidencePanel(currentScenario);
    
  } catch (err) {
    console.error(err);
    showToastNotification("Backend analysis failed. Using simulated fallback.");
    
    setTimeout(() => {
      canvasViewport.classList.remove("scan-active");
      document.getElementById("pipeline-status-indicator").textContent = "VIOLATION CAPTURED";
      document.getElementById("pipeline-status-indicator").className = "severity-badge badge-danger";
      
      animateOCR(currentScenario.plate, currentScenario.ocrConfidence);
      populateEvidencePanel(currentScenario);
    }, 500);
  } finally {
    isAnalysisRunning = false;
  }
}

function animateOCR(plateText, targetConf) {
  let steps = 0;
  plateOcrBox.textContent = "";
  const interval = setInterval(() => {
    if (steps < plateText.length) {
      plateOcrBox.textContent += plateText[steps];
      steps++;
    } else {
      clearInterval(interval);
      plateOcrBox.textContent = plateText;
      ocrConfElement.textContent = targetConf + "%";
    }
  }, 120);
}

// --- Offender and Risk Calculations ---
function getOffenderStatus(plate) {
  const matchCount = violationsList.filter(v => v.plate === plate).length;
  if (matchCount >= 2) {
    return `Repeat Offender (${matchCount + 1} Violations)`;
  }
  return "First-time Offender";
}

function getRiskLevelClass(score) {
  if (score >= 75) return "risk-high";
  if (score >= 50) return "risk-medium";
  return "risk-low";
}

// --- Populate Evidence Panel ---
function populateEvidencePanel(sc) {
  evidenceSeverity.textContent = sc.riskScore >= 75 ? "CRITICAL" : "ALERT";
  evidenceSeverity.className = `severity-badge ${sc.riskScore >= 75 ? 'badge-danger' : 'badge-warning'}`;
  
  evidencePreview.style.backgroundImage = "none";
  let colorTheme = "#1e293b";
  if (sc.id === "helmet_violation") colorTheme = "#8b5cf6";
  else if (sc.id === "redlight_violation") colorTheme = "#dc2626";
  else if (sc.id === "seatbelt_violation") colorTheme = "#0284c7";
  else if (sc.id === "illegal_parking") colorTheme = "#f8fafc";
  
  evidencePreview.style.backgroundColor = colorTheme;

  const uniqueTicketId = "TKT-" + Math.floor(1000 + Math.random()*9000);
  metaTicketId.textContent = uniqueTicketId;
  metaType.textContent = sc.violationType.replace(/_/g, " ");
  
  const riskClass = getRiskLevelClass(sc.riskScore);
  metaRisk.innerHTML = `<span class="risk-badge ${riskClass}">${sc.riskScore}/100 - ${sc.riskScore >= 75 ? 'HIGH' : sc.riskScore >= 50 ? 'MEDIUM' : 'LOW'}</span>`;
  
  metaPlate.textContent = sc.plate;
  
  const status = getOffenderStatus(sc.plate);
  const isRepeat = status.includes("Repeat");
  metaOffenderStatus.innerHTML = `<span class="${isRepeat ? 'offender-repeat-badge' : 'offender-first-badge'}">${status}</span>`;
  
  metaConfidence.textContent = sc.confidence + "%";
  metaVehicleClass.textContent = sc.vehicleClass;
  
  const now = new Date();
  const dateStr = now.toISOString().slice(0, 10) + " " + now.toTimeString().slice(0, 5);
  metaTime.textContent = dateStr;
  metaFine.textContent = sc.fine;
  
  plateMagnifier.style.display = "block";
  plateMagnifier.style.backgroundColor = "#fbbf24";
  plateMagnifier.innerHTML = `<span style="color: #000; font-family: 'Share Tech Mono'; font-weight: 700; font-size: 0.75rem;">${sc.plate}</span>`;
  plateMagnifier.style.display = "flex";
  plateMagnifier.style.alignItems = "center";
  plateMagnifier.style.justifyContent = "center";
}

function resetEvidencePanel() {
  evidenceSeverity.textContent = "--";
  evidenceSeverity.className = "severity-badge badge-info";
  evidencePreview.style.backgroundImage = "none";
  evidencePreview.style.backgroundColor = "transparent";
  plateMagnifier.style.display = "none";
  
  metaTicketId.textContent = "--";
  metaType.textContent = "--";
  metaRisk.textContent = "--";
  metaPlate.textContent = "--";
  metaOffenderStatus.textContent = "--";
  metaConfidence.textContent = "0%";
  metaVehicleClass.textContent = "--";
  metaTime.textContent = "--";
  metaFine.textContent = "--";
}

function setupEvidenceActions() {
  btnApprove.addEventListener("click", () => {
    if (metaTicketId.textContent === "--") return;
    saveEventToLedger("APPROVED");
  });
  
  btnReview.addEventListener("click", () => {
    if (metaTicketId.textContent === "--") return;
    saveEventToLedger("PENDING_REVIEW");
  });
  
  btnDismiss.addEventListener("click", () => {
    if (metaTicketId.textContent === "--") return;
    saveEventToLedger("DISMISSED");
  });
}

async function saveEventToLedger(status) {
  const ticketObj = {
    id: metaTicketId.textContent,
    timestamp: metaTime.textContent,
    plate: metaPlate.textContent,
    type: currentScenario.violationType,
    vehicle: metaVehicleClass.textContent,
    riskScore: currentScenario.riskScore,
    confidence: metaConfidence.textContent.replace("%", "") + "%",
    fine: metaFine.textContent,
    status: status
  };

  try {
    const existing = violationsList.find(t => t.id === ticketObj.id);
    let res;
    if (existing) {
      res = await fetch(`${API_BASE}/citations/${ticketObj.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: status })
      });
    } else {
      res = await fetch(`${API_BASE}/citations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          timestamp: ticketObj.timestamp,
          plate: ticketObj.plate,
          type: ticketObj.type,
          vehicle: ticketObj.vehicle,
          risk_score: ticketObj.riskScore,
          confidence: ticketObj.confidence,
          fine: ticketObj.fine,
          status: ticketObj.status
        })
      });
    }
    
    if (!res.ok) throw new Error("Failed to sync citation status with backend");
    showToastNotification(`Ticket ${ticketObj.id} status synced with database as ${status}!`);
    
  } catch (err) {
    console.error(err);
    showToastNotification("Backend sync failed. Saving locally.");
    
    const existingIndex = violationsList.findIndex(t => t.id === ticketObj.id);
    if (existingIndex > -1) {
      violationsList[existingIndex].status = status;
    } else {
      violationsList.unshift(ticketObj);
    }
    localStorage.setItem("atv_violations", JSON.stringify(violationsList));
  }

  resetEvidencePanel();
  selectScenario(currentScenario.id);
  await refreshData();
}

function showToastNotification(message) {
  const toast = document.createElement("div");
  toast.style.position = "fixed";
  toast.style.bottom = "2rem";
  toast.style.right = "2rem";
  toast.style.background = "rgba(11, 17, 30, 0.95)";
  toast.style.border = "1px solid var(--accent-color)";
  toast.style.color = "var(--text-primary)";
  toast.style.padding = "0.75rem 1.5rem";
  toast.style.borderRadius = "8px";
  toast.style.boxShadow = "0 8px 30px rgba(0,0,0,0.5)";
  toast.style.zIndex = "1000";
  toast.style.fontSize = "0.9rem";
  toast.style.animation = "fadeIn 0.3s ease-out";
  toast.textContent = message;
  
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 2500);
}

// --- TAB 2: Dynamic SVGs & Dashboard Metrics ---
function updateDashboardMetrics() {
  const totalCount = violationsList.length;
  document.getElementById("kpi-total-violations").textContent = totalCount;
  
  // Fines revenue
  let revenue = 0;
  violationsList.forEach(v => {
    if (v.status === "APPROVED") {
      const numericFine = parseFloat(v.fine.replace(/[$,]/g, ''));
      if (!isNaN(numericFine)) revenue += numericFine;
    }
  });
  document.getElementById("kpi-total-revenue").textContent = "$" + revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  
  // Calculate active repeat offenders (plates with count >= 2 in database)
  const plateCounts = {};
  violationsList.forEach(v => {
    plateCounts[v.plate] = (plateCounts[v.plate] || 0) + 1;
  });
  const repeatOffenders = Object.keys(plateCounts).filter(p => plateCounts[p] >= 2).length;
  document.getElementById("kpi-repeat-offenders").textContent = repeatOffenders;
  
  // Performance indicators
  syncPerformanceGauges();
  
  // Rendering Widgets
  drawCategoryBarChart();
  drawTrendLineChart();
  drawHotspotHeatmap();
  renderPatrolRecommendations();
  renderRepeatOffendersRegister();
}

function syncPerformanceGauges() {
  const total = violationsList.length;
  const approved = violationsList.filter(v => v.status === "APPROVED").length;
  const dismissed = violationsList.filter(v => v.status === "DISMISSED").length;
  
  let pRatio = 95.4;
  let rRatio = 93.1;
  
  if (total > 0) {
    pRatio = Math.min(99.9, Math.max(75.0, 95.4 + (approved - dismissed) * 0.2)).toFixed(1);
    rRatio = Math.min(99.9, Math.max(75.0, 93.1 + (approved - dismissed) * 0.1)).toFixed(1);
  }
  const fRatio = (2 * (pRatio * rRatio) / (parseFloat(pRatio) + parseFloat(rRatio))).toFixed(1);

  document.getElementById("gauge-val-precision").textContent = pRatio + "%";
  document.getElementById("gauge-val-recall").textContent = rRatio + "%";
  document.getElementById("gauge-val-f1").textContent = fRatio + "%";

  setGaugeCircleStrokeOffset("gauge-precision", pRatio);
  setGaugeCircleStrokeOffset("gauge-recall", rRatio);
  setGaugeCircleStrokeOffset("gauge-f1", fRatio);
}

function setGaugeCircleStrokeOffset(elementId, value) {
  const el = document.getElementById(elementId);
  if (el) {
    const circumference = 2 * Math.PI * 40;
    const offset = circumference * (1 - value / 100);
    el.style.strokeDashoffset = offset;
  }
}

// Draw Category Bar Chart
function drawCategoryBarChart() {
  const container = document.getElementById("category-chart-container");
  if (!container) return;
  
  const counts = {
    "HELMET": 0,
    "SEATBELT": 0,
    "RED LIGHT": 0,
    "PARKING": 0,
    "OTHER": 0
  };
  
  violationsList.forEach(v => {
    if (v.type.includes("HELMET")) counts["HELMET"]++;
    else if (v.type.includes("SEATBELT")) counts["SEATBELT"]++;
    else if (v.type.includes("RED_LIGHT")) counts["RED LIGHT"]++;
    else if (v.type.includes("PARKING")) counts["PARKING"]++;
    else counts["OTHER"]++;
  });

  const categories = Object.keys(counts);
  const data = Object.values(counts);
  const maxVal = Math.max(...data, 4);

  let barsHTML = "";
  const width = 500;
  const height = 220;
  const paddingLeft = 80;
  const paddingBottom = 40;
  const chartHeight = height - paddingBottom;
  const chartWidth = width - paddingLeft;
  
  for (let grid = 0; grid <= 4; grid++) {
    const gy = chartHeight - (grid / 4) * (chartHeight - 20);
    const labelVal = Math.round((grid / 4) * maxVal);
    barsHTML += `
      <line x1="${paddingLeft}" y1="${gy}" x2="${width - 20}" y2="${gy}" class="chart-grid-line" />
      <text x="${paddingLeft - 15}" y="${gy + 4}" fill="var(--text-secondary)" font-size="10" text-anchor="end">${labelVal}</text>
    `;
  }

  const barWidth = 35;
  const spacing = (chartWidth - 20) / categories.length;

  categories.forEach((cat, idx) => {
    const val = counts[cat];
    const barHeight = (val / maxVal) * (chartHeight - 20);
    const bx = paddingLeft + idx * spacing + (spacing - barWidth) / 2;
    const by = chartHeight - barHeight;

    barsHTML += `
      <g>
        <rect x="${bx}" y="${by}" width="${barWidth}" height="${barHeight}" rx="4" fill="url(#bar-gradient-cyan)" opacity="0.85">
          <title>${cat}: ${val} violations</title>
        </rect>
        <text x="${bx + barWidth/2}" y="${chartHeight + 18}" fill="var(--text-secondary)" font-size="10" text-anchor="middle">${cat}</text>
      </g>
    `;
  });

  container.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" class="svg-chart">
      <defs>
        <linearGradient id="bar-gradient-cyan" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#06B6D4" />
          <stop offset="100%" stop-color="#3B82F6" />
        </linearGradient>
      </defs>
      ${barsHTML}
    </svg>
  `;
}

// Draw Trend Line Chart
function drawTrendLineChart() {
  const container = document.getElementById("trend-chart-container");
  if (!container) return;

  const hoursLabels = ["08:00", "11:00", "14:00", "17:00", "20:00", "23:00"];
  const hourCounts = [2, 4, 1, 3, 5, 2];

  violationsList.forEach(v => {
    const hour = parseInt(v.timestamp.substring(11, 13));
    if (isNaN(hour)) return;
    if (hour >= 8 && hour < 11) hourCounts[0]++;
    else if (hour >= 11 && hour < 14) hourCounts[1]++;
    else if (hour >= 14 && hour < 17) hourCounts[2]++;
    else if (hour >= 17 && hour < 20) hourCounts[3]++;
    else if (hour >= 20 && hour < 23) hourCounts[4]++;
    else hourCounts[5]++;
  });

  const maxVal = Math.max(...hourCounts, 5);
  const width = 800;
  const height = 220;
  const paddingLeft = 50;
  const paddingBottom = 40;
  const chartHeight = height - paddingBottom;
  const chartWidth = width - paddingLeft - 20;

  let lineHTML = "";
  
  for (let grid = 0; grid <= 4; grid++) {
    const gy = chartHeight - (grid / 4) * (chartHeight - 20);
    const labelVal = Math.round((grid / 4) * maxVal);
    lineHTML += `
      <line x1="${paddingLeft}" y1="${gy}" x2="${width - 20}" y2="${gy}" class="chart-grid-line" />
      <text x="${paddingLeft - 10}" y="${gy + 4}" fill="var(--text-secondary)" font-size="10" text-anchor="end">${labelVal}</text>
    `;
  }

  const spacing = chartWidth / (hoursLabels.length - 1);
  let pointsStr = "";
  let areaPointsStr = `${paddingLeft},${chartHeight} `;

  hourCounts.forEach((cnt, idx) => {
    const px = paddingLeft + idx * spacing;
    const py = chartHeight - (cnt / maxVal) * (chartHeight - 20);
    pointsStr += `${px},${py} `;
    areaPointsStr += `${px},${py} `;
    
    lineHTML += `
      <circle cx="${px}" cy="${py}" r="5" class="chart-point">
        <title>Time: ${hoursLabels[idx]} | Vol: ${cnt}</title>
      </circle>
      <text x="${px}" y="${chartHeight + 18}" fill="var(--text-secondary)" font-size="10" text-anchor="middle">${hoursLabels[idx]}</text>
    `;
  });
  areaPointsStr += `${paddingLeft + (hoursLabels.length - 1) * spacing},${chartHeight}`;

  container.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" class="svg-chart">
      <defs>
        <linearGradient id="chart-gradient-violet" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="#6366F1" />
          <stop offset="100%" stop-color="#8B5CF6" />
        </linearGradient>
        <linearGradient id="area-gradient-violet" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#6366F1" stop-opacity="0.4" />
          <stop offset="100%" stop-color="#6366F1" stop-opacity="0" />
        </linearGradient>
      </defs>
      ${lineHTML}
      <polyline points="${pointsStr}" class="chart-line" />
      <polygon points="${areaPointsStr}" class="chart-area" />
    </svg>
  `;
}

// Draw Hotspot Heatmap SVG Grid (Predictive Traffic Intelligence)
function drawHotspotHeatmap() {
  const container = document.getElementById("heatmap-container");
  if (!container) return;

  const width = 600;
  const height = 280;
  let nodesHTML = "";

  // Grid background lanes representing streets
  nodesHTML += `
    <line x1="0" y1="80" x2="600" y2="80" stroke="rgba(255,255,255,0.06)" stroke-width="24" />
    <line x1="0" y1="200" x2="600" y2="200" stroke="rgba(255,255,255,0.06)" stroke-width="24" />
    <line x1="180" y1="0" x2="180" y2="280" stroke="rgba(255,255,255,0.06)" stroke-width="24" />
    <line x1="380" y1="0" x2="380" y2="280" stroke="rgba(255,255,255,0.06)" stroke-width="24" />
    <line x1="530" y1="0" x2="530" y2="280" stroke="rgba(255,255,255,0.06)" stroke-width="24" />
  `;

  HOTSPOTS.forEach(spot => {
    let color = "#10B981"; // low
    if (spot.risk >= 80) color = "#EF4444"; // high
    else if (spot.risk >= 55) color = "#F59E0B"; // med
    
    nodesHTML += `
      <g class="heatmap-node">
        <circle cx="${spot.x}" cy="${spot.y}" r="14" fill="${color}" opacity="0.12" class="heatmap-pulse" />
        <circle cx="${spot.x}" cy="${spot.y}" r="6" fill="${color}" />
        <text x="${spot.x + 10}" y="${spot.y - 10}" fill="#fff" font-size="9" font-weight="600">${spot.name}</text>
        <title>${spot.name}\nPredictive Risk: ${spot.risk}%\nPeak Hours: ${spot.peak}\nPatrol: ${spot.patrol}</title>
      </g>
    `;
  });

  container.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" style="width:100%; height:100%; display:block;">
      ${nodesHTML}
    </svg>
  `;
}

// Render patrol deployment recommendations table
function renderPatrolRecommendations() {
  const body = document.getElementById("patrol-recommendations-body");
  if (!body) return;

  body.innerHTML = "";
  HOTSPOTS.forEach(spot => {
    let riskBadge = `<span class="risk-badge risk-low">${spot.risk}% - LOW</span>`;
    if (spot.risk >= 80) riskBadge = `<span class="risk-badge risk-high">${spot.risk}% - HIGH</span>`;
    else if (spot.risk >= 55) riskBadge = `<span class="risk-badge risk-medium">${spot.risk}% - MEDIUM</span>`;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-weight:600;">${spot.name}</td>
      <td>${riskBadge}</td>
      <td style="font-family:var(--font-mono);">${spot.peak}</td>
      <td style="color:var(--accent-cyan); font-weight:600;">${spot.patrol}</td>
    `;
    body.appendChild(tr);
  });
}

// Render Repeat Offenders register widget
async function renderRepeatOffendersRegister() {
  const body = document.getElementById("repeat-offenders-body");
  if (!body) return;

  let sorted = [];
  try {
    const res = await fetch(`${API_BASE}/repeat-offenders`);
    if (res.ok) {
      const data = await res.json();
      sorted = data.map(o => ({
        plate: o.plate,
        count: o.violations_count,
        vehicle: o.vehicle,
        avgRisk: o.avg_risk
      }));
    }
  } catch (err) {
    console.error("Failed to fetch repeat offenders:", err);
    const plateGroups = {};
    violationsList.forEach(v => {
      if (!plateGroups[v.plate]) {
        plateGroups[v.plate] = { plate: v.plate, count: 0, vehicle: v.vehicle, totalRisk: 0 };
      }
      plateGroups[v.plate].count++;
      plateGroups[v.plate].totalRisk += (v.riskScore || 50);
    });
    sorted = Object.values(plateGroups)
      .filter(g => g.count >= 2)
      .map(g => ({
        plate: g.plate,
        count: g.count,
        vehicle: g.vehicle,
        avgRisk: Math.round(g.totalRisk / g.count)
      }))
      .sort((a,b) => b.count - a.count);
  }

  body.innerHTML = "";
  if (sorted.length === 0) {
    body.innerHTML = `
      <tr>
        <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No active repeat offenders identified.</td>
      </tr>
    `;
  } else {
    sorted.forEach(g => {
      const avgRisk = g.avgRisk;
      const riskClass = getRiskLevelClass(avgRisk);
      
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><span class="plate-cell">${g.plate}</span></td>
        <td style="font-weight: 700; color: #EF4444; font-size:0.9rem;">${g.count} Offenses</td>
        <td>${g.vehicle}</td>
        <td><span class="risk-badge ${riskClass}">${avgRisk}/100</span></td>
        <td><span class="offender-repeat-badge" style="font-size:0.7rem;">CRITICAL TIGHT TRACKING</span></td>
      `;
      body.appendChild(tr);
    });
  }
}

// --- TAB 3: Violations Ledger Table ---
function renderLedgerTable() {
  const query = searchPlate.value.trim().toUpperCase();
  const typeFilter = filterViolation.value;
  const statusFilter = filterStatus.value;

  const filtered = violationsList.filter(item => {
    const matchesPlate = query === "" || item.plate.toUpperCase().includes(query);
    const matchesType = typeFilter === "ALL" || item.type === typeFilter;
    const matchesStatus = statusFilter === "ALL" || item.status === statusFilter;
    return matchesPlate && matchesType && matchesStatus;
  });

  const startIdx = (ledgerPage - 1) * ledgerPageSize;
  const endIdx = startIdx + ledgerPageSize;
  const pageItems = filtered.slice(startIdx, endIdx);

  ledgerTableBody.innerHTML = "";
  if (pageItems.length === 0) {
    ledgerTableBody.innerHTML = `
      <tr>
        <td colspan="10" style="text-align: center; color: var(--text-muted); padding: 2rem;">No matching violation logs found.</td>
      </tr>
    `;
  } else {
    pageItems.forEach(item => {
      let badgeStyle = "status-review";
      if (item.status === "APPROVED") badgeStyle = "status-approved";
      else if (item.status === "DISMISSED") badgeStyle = "status-dismissed";
      
      const score = item.riskScore || 50;
      const riskClass = getRiskLevelClass(score);
      const riskBadge = `<span class="risk-badge ${riskClass}">${score}/100</span>`;
      
      // Determine Offender alert
      // count matches
      const matchCount = violationsList.filter(v => v.plate === item.plate).length;
      const offenderTag = matchCount >= 2 
        ? `<span class="offender-repeat-badge">Repeat (${matchCount})</span>`
        : `<span class="offender-first-badge">First-Time</span>`;

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-family: var(--font-mono); font-weight:600; color: var(--accent-cyan);">${item.id}</td>
        <td>${item.timestamp}</td>
        <td><span class="plate-cell">${item.plate}</span></td>
        <td>${item.type.replace(/_/g, " ")}</td>
        <td>${item.vehicle}</td>
        <td>${riskBadge}</td>
        <td>${offenderTag}</td>
        <td style="font-weight: 700; color:#fff;">${item.fine}</td>
        <td><span class="status-badge ${badgeStyle}">${item.status}</span></td>
        <td>
          <div class="ledger-actions-btn-group">
            <button class="btn-icon" onclick="escalateLedgerItem('${item.id}')" title="Review">
              <svg viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </button>
            <button class="btn-icon btn-icon-danger" onclick="deleteLedgerItem('${item.id}')" title="Delete record">
              <svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
            </button>
          </div>
        </td>
      `;
      ledgerTableBody.appendChild(tr);
    });
  }

  const total = filtered.length;
  const currentStart = total === 0 ? 0 : startIdx + 1;
  const currentEnd = Math.min(endIdx, total);
  ledgerPaginationInfo.textContent = `Showing ${currentStart}-${currentEnd} of ${total} entries`;

  btnLedgerPrev.disabled = ledgerPage <= 1;
  btnLedgerNext.disabled = endIdx >= total;
}

function setupLedgerListeners() {
  searchPlate.addEventListener("input", () => {
    ledgerPage = 1;
    renderLedgerTable();
  });
  filterViolation.addEventListener("change", () => {
    ledgerPage = 1;
    renderLedgerTable();
  });
  filterStatus.addEventListener("change", () => {
    ledgerPage = 1;
    renderLedgerTable();
  });

  btnLedgerPrev.addEventListener("click", () => {
    if (ledgerPage > 1) {
      ledgerPage--;
      renderLedgerTable();
    }
  });

  btnLedgerNext.addEventListener("click", () => {
    ledgerPage++;
    renderLedgerTable();
  });

  btnExportLedger.addEventListener("click", () => {
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Ticket ID,Timestamp,License Plate,Violation Type,Vehicle,Risk Score,Confidence,Fine,Status\n";
    violationsList.forEach(v => {
      csvContent += `${v.id},${v.timestamp},${v.plate},${v.type},${v.vehicle},${v.riskScore},${v.confidence},${v.fine},${v.status}\n`;
    });
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `TrafficEye_AI_Report_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });
}

window.deleteLedgerItem = async function(id) {
  try {
    const res = await fetch(`${API_BASE}/citations/${id}`, {
      method: "DELETE"
    });
    if (!res.ok) throw new Error("Failed to delete citation");
    showToastNotification(`Record ${id} permanently deleted from database.`);
  } catch (err) {
    console.error(err);
    violationsList = violationsList.filter(item => item.id !== id);
    localStorage.setItem("atv_violations", JSON.stringify(violationsList));
    showToastNotification(`Record ${id} deleted locally.`);
  }
  await refreshData();
};

window.escalateLedgerItem = async function(id) {
  try {
    const res = await fetch(`${API_BASE}/citations/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "PENDING_REVIEW" })
    });
    if (!res.ok) throw new Error("Failed to escalate citation status");
    showToastNotification(`Record ${id} status updated to PENDING_REVIEW.`);
  } catch (err) {
    console.error(err);
    const item = violationsList.find(t => t.id === id);
    if (item) {
      item.status = "PENDING_REVIEW";
      localStorage.setItem("atv_violations", JSON.stringify(violationsList));
    }
    showToastNotification(`Record ${id} escalated locally.`);
  }
  await refreshData();
};

// --- Settings Controller ---
function setupSettingsListeners() {
  rangeVehicleThresh.addEventListener("input", (e) => {
    valVehicleThresh.textContent = e.target.value + "%";
  });
  rangeViolationThresh.addEventListener("input", (e) => {
    valViolationThresh.textContent = e.target.value + "%";
  });
  rangeOcrThresh.addEventListener("input", (e) => {
    valOcrThresh.textContent = e.target.value + "%";
  });

  btnSaveSettings.addEventListener("click", () => {
    const config = {
      vehicleThresh: rangeVehicleThresh.value,
      violationThresh: rangeViolationThresh.value,
      ocrThresh: rangeOcrThresh.value,
      ocrEngine: selectOcrEngine.value,
      webhookUrl: inputWebhook.value
    };
    localStorage.setItem("atv_settings", JSON.stringify(config));
    
    const randomShift = (parseFloat(config.vehicleThresh) + parseFloat(config.violationThresh)) / 2;
    const sysAcc = (80 + randomShift * 0.18).toFixed(1);
    document.getElementById("kpi-map-accuracy").textContent = sysAcc + "%";

    showToastNotification("Core AI Configurations saved successfully!");
  });

  btnResetSettings.addEventListener("click", () => {
    rangeVehicleThresh.value = 75;
    rangeViolationThresh.value = 80;
    rangeOcrThresh.value = 70;
    selectOcrEngine.value = "easyocr";
    inputWebhook.value = "https://api.trafficeye-ai.gov/v1/citations";
    
    valVehicleThresh.textContent = "75%";
    valViolationThresh.textContent = "80%";
    valOcrThresh.textContent = "70%";
    
    localStorage.removeItem("atv_settings");
    showToastNotification("Configurations reset to default.");
  });
}

function loadSettingsFromStorage() {
  const stored = localStorage.getItem("atv_settings");
  if (stored) {
    const config = JSON.parse(stored);
    rangeVehicleThresh.value = config.vehicleThresh || 75;
    rangeViolationThresh.value = config.violationThresh || 80;
    rangeOcrThresh.value = config.ocrThresh || 70;
    selectOcrEngine.value = config.ocrEngine || "easyocr";
    inputWebhook.value = config.webhookUrl || "https://api.trafficeye-ai.gov/v1/citations";

    valVehicleThresh.textContent = rangeVehicleThresh.value + "%";
    valViolationThresh.textContent = rangeViolationThresh.value + "%";
    valOcrThresh.textContent = rangeOcrThresh.value + "%";
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// LIVE CAMERA STREAM — CONNECTION & WEBSOCKET
// ═══════════════════════════════════════════════════════════════════════════

const API_BASE = "http://127.0.0.1:8000";
let streamWS = null;
let streamStatusInterval = null;
let toastTimeout = null;

function initLiveCameraPanel() {
  // FPS slider
  const fpsSlider = document.getElementById("stream-fps-slider");
  const fpsLabel = document.getElementById("stream-fps-label");
  if (fpsSlider && fpsLabel) {
    fpsSlider.addEventListener("input", () => {
      fpsLabel.textContent = parseFloat(fpsSlider.value).toFixed(1);
    });
  }

  // Preset buttons
  document.querySelectorAll(".preset-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const urlInput = document.getElementById("stream-url-input");
      const typeSelect = document.getElementById("stream-type-select");
      if (urlInput) urlInput.value = btn.dataset.url;
      if (typeSelect) typeSelect.value = btn.dataset.type;
    });
  });
}

async function connectLiveStream() {
  const urlInput = document.getElementById("stream-url-input");
  const typeSelect = document.getElementById("stream-type-select");
  const fpsSlider = document.getElementById("stream-fps-slider");

  const streamUrl = urlInput ? urlInput.value.trim() : "";
  const streamType = typeSelect ? typeSelect.value : "auto";
  const fps = fpsSlider ? parseFloat(fpsSlider.value) : 2.0;

  if (!streamUrl) {
    showToast("Please enter a stream URL", "warning");
    return;
  }

  // Update UI to connecting state
  const connectBtn = document.getElementById("btn-connect-stream");
  const disconnectBtn = document.getElementById("btn-disconnect-stream");
  if (connectBtn) {
    connectBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg> Connecting...`;
    connectBtn.disabled = true;
  }

  try {
    // Call backend API to start the stream
    const response = await fetch(`${API_BASE}/api/stream/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: streamUrl, type: streamType, fps: fps })
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Failed to connect");
    }

    const data = await response.json();
    console.log("[LiveStream] Connected:", data);

    // Connect WebSocket for real-time results
    connectWebSocket();

    // Update UI
    if (connectBtn) connectBtn.style.display = "none";
    if (disconnectBtn) disconnectBtn.style.display = "flex";

    const liveBadge = document.getElementById("live-badge");
    if (liveBadge) liveBadge.style.display = "inline";

    const streamStats = document.getElementById("stream-stats");
    if (streamStats) streamStats.style.display = "grid";

    // Update pipeline status
    const statusIndicator = document.getElementById("pipeline-status-indicator");
    if (statusIndicator) {
      statusIndicator.textContent = "🔴 LIVE STREAM";
      statusIndicator.className = "severity-badge badge-danger";
    }

    // Start polling stream stats
    startStatsPolling();

    showToast(`Connected to ${data.stream_type} stream`, "success");

  } catch (err) {
    console.error("[LiveStream] Connection error:", err);
    showToast(`Connection failed: ${err.message}`, "error");

    // Reset connect button
    if (connectBtn) {
      connectBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Connect`;
      connectBtn.disabled = false;
    }
  }
}

async function disconnectLiveStream() {
  try {
    await fetch(`${API_BASE}/api/stream/stop`, { method: "POST" });
  } catch (e) {
    console.warn("[LiveStream] Stop request failed:", e);
  }

  // Close WebSocket
  if (streamWS) {
    streamWS.close();
    streamWS = null;
  }

  // Stop stats polling
  if (streamStatusInterval) {
    clearInterval(streamStatusInterval);
    streamStatusInterval = null;
  }

  // Reset UI
  const connectBtn = document.getElementById("btn-connect-stream");
  const disconnectBtn = document.getElementById("btn-disconnect-stream");
  if (connectBtn) {
    connectBtn.style.display = "flex";
    connectBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Connect`;
    connectBtn.disabled = false;
  }
  if (disconnectBtn) disconnectBtn.style.display = "none";

  const liveBadge = document.getElementById("live-badge");
  if (liveBadge) liveBadge.style.display = "none";

  const streamStats = document.getElementById("stream-stats");
  if (streamStats) streamStats.style.display = "none";

  const statusIndicator = document.getElementById("pipeline-status-indicator");
  if (statusIndicator) {
    statusIndicator.textContent = "SYSTEM IDLE";
    statusIndicator.className = "severity-badge badge-info";
  }

  showToast("Stream disconnected", "info");
}

function connectWebSocket() {
  if (streamWS) {
    streamWS.close();
  }

  const wsUrl = `ws://127.0.0.1:8000/ws/stream`;
  streamWS = new WebSocket(wsUrl);

  streamWS.onopen = () => {
    console.log("[WebSocket] Connected to /ws/stream");
  };

  streamWS.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);

      // Update stats from every message
      if (msg.stats) {
        updateStreamStats(msg.stats);
      }

      // Show violation toast for new violations
      if (msg.type === "violation_detected" && msg.data) {
        showViolationToast(msg.data);
      }
    } catch (e) {
      console.warn("[WebSocket] Parse error:", e);
    }
  };

  streamWS.onclose = () => {
    console.log("[WebSocket] Disconnected");
  };

  streamWS.onerror = (err) => {
    console.error("[WebSocket] Error:", err);
  };
}

function updateStreamStats(stats) {
  const frames = document.getElementById("stat-frames");
  const violations = document.getElementById("stat-violations");
  const inferenceMs = document.getElementById("stat-inference-ms");
  const fpsActual = document.getElementById("stat-fps-actual");

  if (frames) frames.textContent = stats.frames_processed || 0;
  if (violations) violations.textContent = stats.violations_detected || 0;
  if (inferenceMs) inferenceMs.textContent = stats.avg_inference_ms || 0;
  if (fpsActual) fpsActual.textContent = stats.fps_actual || 0;
}

function startStatsPolling() {
  if (streamStatusInterval) clearInterval(streamStatusInterval);

  streamStatusInterval = setInterval(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/stream/status`);
      if (response.ok) {
        const status = await response.json();
        updateStreamStats(status);

        // If stream stopped externally, reset UI
        if (!status.running) {
          disconnectLiveStream();
        }
      }
    } catch (e) {
      // Silently handle — backend might be down
    }
  }, 3000);
}

function showViolationToast(violation) {
  // Remove existing toast
  const existing = document.querySelector(".violation-toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.className = "violation-toast";
  toast.innerHTML = `
    <div class="toast-type">⚠️ ${violation.violation_type || "VIOLATION DETECTED"}</div>
    <div class="toast-plate">${violation.plate || "UNKNOWN"}</div>
    <div style="font-size: 0.75rem; opacity: 0.8; margin-top: 0.25rem;">
      Risk: ${violation.risk_score || 0} · ${violation.severity || "MEDIUM"} · ${violation.fine || "$0.00"}
    </div>
  `;
  document.body.appendChild(toast);

  // Auto-remove after 5 seconds
  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    toast.style.animation = "toastSlideIn 0.3s ease-out reverse";
    setTimeout(() => toast.remove(), 300);
  }, 5000);
}

function showToast(message, type = "info") {
  const existing = document.querySelector(".violation-toast");
  if (existing) existing.remove();

  const colors = {
    success: "linear-gradient(135deg, rgba(16, 185, 129, 0.95), rgba(5, 150, 105, 0.95))",
    error: "linear-gradient(135deg, rgba(239, 68, 68, 0.95), rgba(185, 28, 28, 0.95))",
    warning: "linear-gradient(135deg, rgba(245, 158, 11, 0.95), rgba(217, 119, 6, 0.95))",
    info: "linear-gradient(135deg, rgba(99, 102, 241, 0.95), rgba(139, 92, 246, 0.95))"
  };

  const toast = document.createElement("div");
  toast.className = "violation-toast";
  toast.style.background = colors[type] || colors.info;
  toast.innerHTML = `<div>${message}</div>`;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = "toastSlideIn 0.3s ease-out reverse";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Initialize live camera panel when page loads
const _origInit = typeof init === "function" ? init : null;
window.onload = function() {
  if (_origInit) _origInit();
  initLiveCameraPanel();
};
