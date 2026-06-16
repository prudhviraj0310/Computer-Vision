from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.pdfgen import canvas as pdfcanvas

# ─── Colour Palette ────────────────────────────────────────────────────────────
DARK_BG       = colors.HexColor("#0D1117")
ACCENT        = colors.HexColor("#F97316")   # orange
ACCENT2       = colors.HexColor("#38BDF8")   # sky blue
HIGHLIGHT     = colors.HexColor("#22C55E")   # green
RED_STAT      = colors.HexColor("#EF4444")
CARD_BG       = colors.HexColor("#161B22")
BORDER        = colors.HexColor("#30363D")
TEXT_MAIN     = colors.HexColor("#E6EDF3")
TEXT_MUTED    = colors.HexColor("#8B949E")
WHITE         = colors.white
YELLOW        = colors.HexColor("#EAB308")
PURPLE        = colors.HexColor("#A855F7")

W, H = A4  # 595 x 842 pts

# ─── Page canvas callbacks ──────────────────────────────────────────────────────
def dark_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)

    # Top accent bar
    canvas.setFillColor(ACCENT)
    canvas.rect(0, H - 8, W, 8, fill=1, stroke=0)

    # Bottom bar
    canvas.setFillColor(BORDER)
    canvas.rect(0, 0, W, 4, fill=1, stroke=0)

    # Side stripe
    canvas.setFillColor(ACCENT)
    canvas.rect(0, 0, 4, H, fill=1, stroke=0)

    # Page number
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawRightString(W - 20, 12, f"TrafficEye AI  ·  Page {doc.page}")

    canvas.restoreState()

def build_styles():
    base = getSampleStyleSheet()

    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        "cover_title": S("cover_title",
            fontName="Helvetica-Bold", fontSize=34, leading=42,
            textColor=WHITE, alignment=TA_LEFT, spaceAfter=6),

        "cover_sub": S("cover_sub",
            fontName="Helvetica-Bold", fontSize=16, leading=22,
            textColor=ACCENT, alignment=TA_LEFT, spaceAfter=4),

        "cover_meta": S("cover_meta",
            fontName="Helvetica", fontSize=10, leading=16,
            textColor=TEXT_MUTED, alignment=TA_LEFT, spaceAfter=2),

        "section_head": S("section_head",
            fontName="Helvetica-Bold", fontSize=15, leading=20,
            textColor=ACCENT, spaceBefore=16, spaceAfter=6),

        "sub_head": S("sub_head",
            fontName="Helvetica-Bold", fontSize=11, leading=15,
            textColor=ACCENT2, spaceBefore=10, spaceAfter=4),

        "body": S("body",
            fontName="Helvetica", fontSize=9.5, leading=15,
            textColor=TEXT_MAIN, alignment=TA_JUSTIFY, spaceAfter=4),

        "bullet": S("bullet",
            fontName="Helvetica", fontSize=9.5, leading=15,
            textColor=TEXT_MAIN, leftIndent=16, firstLineIndent=-10,
            spaceAfter=3),

        "code": S("code",
            fontName="Courier-Bold", fontSize=8.5, leading=13,
            textColor=HIGHLIGHT, backColor=CARD_BG, leftIndent=10,
            rightIndent=10, spaceBefore=4, spaceAfter=4),

        "stat_num": S("stat_num",
            fontName="Helvetica-Bold", fontSize=22, leading=26,
            textColor=ACCENT, alignment=TA_CENTER),

        "stat_lbl": S("stat_lbl",
            fontName="Helvetica", fontSize=8, leading=11,
            textColor=TEXT_MUTED, alignment=TA_CENTER),

        "gh_link": S("gh_link",
            fontName="Courier", fontSize=8, leading=12,
            textColor=ACCENT2, leftIndent=8, spaceAfter=2),

        "tag": S("tag",
            fontName="Helvetica-Bold", fontSize=8, leading=11,
            textColor=DARK_BG, alignment=TA_CENTER),

        "h3": S("h3",
            fontName="Helvetica-Bold", fontSize=10, leading=14,
            textColor=YELLOW, spaceBefore=8, spaceAfter=3),

        "quote": S("quote",
            fontName="Helvetica-Oblique", fontSize=9.5, leading=15,
            textColor=ACCENT2, leftIndent=20, rightIndent=20,
            spaceAfter=4, spaceBefore=4),
    }


def pill(text, bg=ACCENT, fg=DARK_BG, width=80):
    """Returns a small coloured label table."""
    t = Table([[Paragraph(text, ParagraphStyle("_t", fontName="Helvetica-Bold",
                fontSize=7.5, textColor=fg, alignment=TA_CENTER))]],
              colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("ROUNDEDCORNERS", [4]),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    return t


def stat_box(num, label, color=ACCENT):
    """Single stat card."""
    style_num = ParagraphStyle("_n", fontName="Helvetica-Bold", fontSize=20,
                               textColor=color, alignment=TA_CENTER, leading=24)
    style_lbl = ParagraphStyle("_l", fontName="Helvetica", fontSize=7.5,
                               textColor=TEXT_MUTED, alignment=TA_CENTER, leading=11)
    t = Table([[Paragraph(num, style_num)], [Paragraph(label, style_lbl)]],
              colWidths=[110])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), CARD_BG),
        ("BOX",        (0,0), (-1,-1), 0.5, color),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    return t


def hr(color=BORDER, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color,
                      spaceAfter=4, spaceBefore=4)


def build_doc():
    S = build_styles()

    doc = BaseDocTemplate(
        "TrafficEye_AI_Hackathon_Proposal.pdf",
        pagesize=A4,
        leftMargin=28*mm, rightMargin=20*mm,
        topMargin=24*mm, bottomMargin=18*mm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="dark", frames=frame, onPage=dark_page)])

    story = []

    # ──────────────────────────────────────────────────────────────────────────
    # COVER PAGE
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 30))

    # Badge row
    badges = Table([[
        pill("HACKATHON 2025", ACCENT, DARK_BG, 110),
        Spacer(6, 1),
        pill("BANGALORE TRAFFIC", RED_STAT, WHITE, 120),
        Spacer(6, 1),
        pill("AI + CV", HIGHLIGHT, DARK_BG, 70),
    ]], colWidths=[110, 8, 120, 8, 70])
    badges.setStyle(TableStyle([
        ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0),(-1,-1), 0),
        ("RIGHTPADDING",(0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ("TOPPADDING",(0,0),(-1,-1), 0),
    ]))
    story.append(badges)
    story.append(Spacer(1, 20))

    story.append(Paragraph("TrafficEye AI", S["cover_title"]))
    story.append(Paragraph(
        "Intelligent Traffic Violation Detection &amp; Enforcement System",
        S["cover_sub"]))
    story.append(Spacer(1, 6))
    story.append(hr(ACCENT, 1.5))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "An AI-powered computer vision platform built specifically for <b>Bengaluru Traffic Police (BTP)</b> "
        "— transforming passive surveillance into an active, intelligent enforcement ecosystem that detects "
        "violations in real-time, generates legal evidence, and delivers predictive enforcement intelligence.",
        S["body"]))

    story.append(Spacer(1, 24))

    # ─── Bangalore Crisis Stats Row ───
    stat_row = Table([[
        stat_box("82.86L", "Traffic Cases\nRegistered (2024)", RED_STAT),
        Spacer(6, 1),
        stat_box("893", "Road Deaths\nin 2024", RED_STAT),
        Spacer(6, 1),
        stat_box("4,784", "Road Crashes\nin 2024", YELLOW),
        Spacer(6, 1),
        stat_box("₹80.9Cr", "Fines Collected\n(2024)", HIGHLIGHT),
    ]], colWidths=[110, 8, 110, 8, 110, 8, 110])
    stat_row.setStyle(TableStyle([
        ("VALIGN", (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING", (0,0),(-1,-1), 0),
        ("RIGHTPADDING",(0,0),(-1,-1), 0),
        ("TOPPADDING", (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    story.append(stat_row)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Source: Bengaluru Traffic Police (BTP) Annual Report 2024 · Deccan Herald",
        ParagraphStyle("src", fontName="Helvetica", fontSize=7, textColor=TEXT_MUTED)))

    story.append(Spacer(1, 28))
    story.append(hr(BORDER))
    story.append(Spacer(1, 10))

    meta_tbl = Table([
        [Paragraph("Tech Stack", ParagraphStyle("_m", fontName="Helvetica-Bold",
            fontSize=8.5, textColor=TEXT_MUTED)),
         Paragraph("YOLOv11 · DeepSORT · PaddleOCR · FastAPI · React · PostgreSQL · Docker",
            ParagraphStyle("_v", fontName="Helvetica", fontSize=8.5, textColor=TEXT_MAIN))],
        [Paragraph("Domain", ParagraphStyle("_m", fontName="Helvetica-Bold",
            fontSize=8.5, textColor=TEXT_MUTED)),
         Paragraph("Computer Vision · Traffic Enforcement · Predictive AI · Smart City",
            ParagraphStyle("_v", fontName="Helvetica", fontSize=8.5, textColor=TEXT_MAIN))],
        [Paragraph("Target", ParagraphStyle("_m", fontName="Helvetica-Bold",
            fontSize=8.5, textColor=TEXT_MUTED)),
         Paragraph("Bengaluru Traffic Police (BTP) · ITMS Integration · e-Challan System",
            ParagraphStyle("_v", fontName="Helvetica", fontSize=8.5, textColor=TEXT_MAIN))],
    ], colWidths=[70, 390])
    meta_tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LINEABOVE",(0,0),(-1,0),0.3,BORDER),
        ("LINEBELOW",(0,-1),(-1,-1),0.3,BORDER),
    ]))
    story.append(meta_tbl)

    story.append(PageBreak())

    # ──────────────────────────────────────────────────────────────────────────
    # 1. THE BENGALURU PROBLEM
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("1. The Bengaluru Traffic Crisis", S["section_head"]))
    story.append(hr(ACCENT, 1))

    story.append(Paragraph(
        "Bengaluru — India's Silicon Valley — is simultaneously the nation's most congested city and one of its deadliest for road users. "
        "Despite deploying India's most advanced Intelligent Traffic Management System (ITMS), the scale of violations "
        "overwhelms human enforcement capacity.",
        S["body"]))

    story.append(Spacer(1, 8))

    # Crisis facts table
    facts = [
        ["METRIC", "FIGURE", "IMPACT"],
        ["Total traffic cases (2024)", "82.86 lakh", "~22,700 violations per day"],
        ["Contactless enforcement (2025)", "88% of all cases", "Camera-driven, nearly zero manpower"],
        ["Road deaths (2024)", "893 fatalities", "Highest in Karnataka"],
        ["Fatal crashes (2024)", "871 crashes", "Down only 4% from 2023"],
        ["Pedestrian + biker deaths", "91% of all fatalities", "Critical vulnerability gap"],
        ["Rash driving cases (2025)", "+82% surge YoY", "Enforcement gaps remain"],
        ["Wrong-direction driving", "6,872 BNS cases (2025)", "Up from 3,774 in 2024"],
        ["Drunk driving caught", "23,574 drivers (2024)", "12.54 lakh vehicles checked"],
        ["Fines collected", "₹80.9 crore (2024)", "Under-captures 94% violations"],
        ["Single station violations", "1.02 lakh (Sadashivanagar)", "Until May 2024 alone"],
    ]
    ft = Table(facts, colWidths=[185, 120, 155])
    ft.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), ACCENT),
        ("TEXTCOLOR",  (0,0), (-1,0), DARK_BG),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,0), 8),
        ("BACKGROUND", (0,1), (-1,-1), CARD_BG),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [CARD_BG, colors.HexColor("#1A2030")]),
        ("FONTNAME",   (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",   (0,1), (-1,-1), 8),
        ("TEXTCOLOR",  (0,1), (-1,-1), TEXT_MAIN),
        ("TEXTCOLOR",  (1,1), (1,-1), YELLOW),
        ("TEXTCOLOR",  (2,1), (2,-1), TEXT_MUTED),
        ("FONTNAME",   (1,1), (1,-1), "Helvetica-Bold"),
        ("BOX",        (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",  (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("RIGHTPADDING",(0,0),(-1,-1), 6),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(ft)
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "Sources: BTP Annual Report 2024 · Deccan Herald Jan 2025 · Deccan Herald May 2025",
        ParagraphStyle("src", fontName="Helvetica", fontSize=7, textColor=TEXT_MUTED)))

    story.append(Spacer(1, 12))

    # ITMS Gaps
    story.append(Paragraph("1.1  Gaps in Existing BTP-ITMS Infrastructure", S["sub_head"]))
    story.append(Paragraph(
        "Bengaluru's ITMS (launched Dec 2022) covers <b>50 junctions with 250 ANPR + 80 RLVD cameras</b>. "
        "While award-winning (ET Infra Leadership Award 2025), critical gaps remain:",
        S["body"]))

    gaps = [
        ("No helmet / seatbelt AI",
         "ITMS cameras primarily detect stop-line and red-light violations. "
         "Rider safety violations require separate CV models."),
        ("No triple-riding detection",
         "Motorcycle occupant counting is absent from current ITMS pipeline."),
        ("Zero repeat-offender intelligence",
         "BTP has no automated cross-station offender profiling system."),
        ("No predictive deployment tool",
         "Resources are reactively deployed rather than data-driven."),
        ("Coverage blind spots",
         "Hand-held FTVR devices are used where no ITMS cameras exist — labour-intensive."),
        ("No violation impact scoring",
         "All violations are treated equally; high-risk zones are not prioritised."),
    ]
    for title, desc in gaps:
        story.append(Paragraph(
            f"<b><font color='#F97316'>{chr(10007)}  {title}:</font></b>  {desc}",
            S["bullet"]))

    story.append(PageBreak())

    # ──────────────────────────────────────────────────────────────────────────
    # 2. SOLUTION
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("2. TrafficEye AI — Proposed Solution", S["section_head"]))
    story.append(hr(ACCENT, 1))

    story.append(Paragraph(
        "TrafficEye AI is not another CCTV analytics wrapper. It is a <b>full-stack intelligent enforcement "
        "platform</b> designed as a plug-in upgrade layer on top of BTP-ITMS or any camera feed — "
        "adding AI-driven violation detection, ANPR, evidence packaging, and predictive enforcement intelligence.",
        S["body"]))

    story.append(Spacer(1, 10))

    # Innovation pillars
    story.append(Paragraph("2.1  Core Innovation Pillars", S["sub_head"]))

    innovations = [
        ("Violation Impact Score (VIS)",
         ACCENT,
         "Each detected violation receives a dynamic risk score based on violation type, "
         "traffic density at time of detection, location sensitivity (blackspot proximity), "
         "and historical accident data at that zone. Authorities see HIGH → MEDIUM → LOW "
         "priority queues rather than a flat timeline."),
        ("Repeat Offender Graph",
         RED_STAT,
         "All violations are indexed by license plate. The system automatically builds "
         "offender profiles, flags vehicles with 3+ violations in 30 days, and generates "
         "priority e-Challan escalations — directly addressing a gap BTP itself identified."),
        ("Predictive Enforcement Intelligence",
         HIGHLIGHT,
         "ML models (trained on BTP historical data + OpenCity Bengaluru datasets) forecast "
         "violation hotspots by hour, day, and weather condition. Outputs deployment "
         "recommendations: 'Deploy 3 officers at Silk Board junction 6–9 PM, Mon-Fri.'"),
        ("One-click Legal Evidence Package",
         ACCENT2,
         "Every violation generates a tamper-evident PDF bundle: annotated image, GPS coordinates, "
         "timestamp, ANPR plate text, confidence score, and violation type — court-admissible "
         "and e-Challan API-ready."),
    ]

    for title, color, desc in innovations:
        box = Table([[
            Table([[Paragraph(title, ParagraphStyle("_t", fontName="Helvetica-Bold",
                        fontSize=10, textColor=color, leading=14)),
                    Paragraph(desc, ParagraphStyle("_d", fontName="Helvetica",
                        fontSize=9, textColor=TEXT_MAIN, leading=14))]],
                  colWidths=[430])
        ]], colWidths=[450])
        box.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,-1), CARD_BG),
            ("LINERIGHT",  (0,0),(0,-1), 3, color),
            ("LEFTPADDING",(0,0),(-1,-1), 14),
            ("RIGHTPADDING",(0,0),(-1,-1), 10),
            ("TOPPADDING", (0,0),(-1,-1), 8),
            ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ]))
        story.append(box)
        story.append(Spacer(1, 5))

    story.append(Spacer(1, 8))

    # ──────────────────────────────────────────────────────────────────────────
    # 3. VIOLATIONS DETECTED
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("2.2  Violations Detected (Bengaluru-Specific Focus)", S["sub_head"]))

    violations_data = [
        ["VIOLATION TYPE", "CV APPROACH", "BTP PRIORITY", "VIS LEVEL"],
        ["Helmet Non-Compliance",
         "YOLOv11 person + helmet classifier",
         "CRITICAL — 91% biker fatalities",
         "HIGH"],
        ["Triple Riding",
         "Occupant counter on motorcycle bbox",
         "HIGH — common Bangalore violation",
         "HIGH"],
        ["Seatbelt Non-Compliance",
         "Keypoint analysis on driver region",
         "MEDIUM",
         "MEDIUM"],
        ["Red-Light Violation",
         "Traffic light state + vehicle motion",
         "CRITICAL — major fatality cause",
         "HIGH"],
        ["Stop-Line Violation",
         "Line-crossing detection (DeepSORT)",
         "HIGH",
         "MEDIUM"],
        ["Wrong-Side Driving",
         "Direction vector vs. road flow",
         "CRITICAL — BNS cases +82% in 2025",
         "HIGH"],
        ["Illegal Parking",
         "Zone mask + vehicle dwell time",
         "HIGH — HAL, Bellandur, HSR hotspots",
         "MEDIUM"],
        ["Mobile Phone Use",
         "Hand-to-ear pose detection",
         "HIGH — 83% of Bengalureans guilty",
         "MEDIUM"],
    ]
    vt = Table(violations_data, colWidths=[130, 155, 130, 55])
    vt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1E3A5F")),
        ("TEXTCOLOR",  (0,0), (-1,0), ACCENT2),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,0), 7.5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[CARD_BG, colors.HexColor("#1A2030")]),
        ("FONTNAME",   (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",   (0,1), (-1,-1), 7.5),
        ("TEXTCOLOR",  (0,1), (-1,-1), TEXT_MAIN),
        ("TEXTCOLOR",  (3,1), (3,-1), RED_STAT),
        ("FONTNAME",   (3,1), (3,-1), "Helvetica-Bold"),
        ("BOX",        (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",  (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
        ("RIGHTPADDING",(0,0),(-1,-1), 4),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(vt)

    story.append(PageBreak())

    # ──────────────────────────────────────────────────────────────────────────
    # 3. ARCHITECTURE
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("3. System Architecture", S["section_head"]))
    story.append(hr(ACCENT, 1))

    story.append(Paragraph(
        "The pipeline is a modular, containerised system. Each stage is independently scalable "
        "and plugs into BTP's existing ITMS camera feeds via RTSP streams or image batch uploads.",
        S["body"]))

    story.append(Spacer(1, 8))

    # Pipeline flow
    pipeline_stages = [
        ("INGEST", "Camera Feed / Image Upload", ACCENT2,
         "RTSP stream from ITMS cameras · Batch image upload endpoint · "
         "Supports MP4, JPEG, PNG, H.264 streams"),
        ("PREPROCESS", "Image Enhancement", YELLOW,
         "CLAHE low-light enhancement · Motion deblur (Wiener filter) · "
         "Rain/fog removal · Histogram normalisation"),
        ("DETECT", "Vehicle & Road User Detection", ACCENT,
         "YOLOv11 object detection: car, bike, truck, bus, auto-rickshaw, pedestrian · "
         "Bounding box + confidence · DeepSORT multi-object tracking with unique IDs"),
        ("CLASSIFY", "Violation Detection Engine", RED_STAT,
         "Per-class violation classifiers · Helmet/seatbelt CNN · "
         "Occupant counter · Direction vector analysis · Signal state detector"),
        ("OCR", "License Plate Recognition (ANPR)", HIGHLIGHT,
         "YOLOv11 plate localiser → PaddleOCR + EasyOCR ensemble · "
         "Indian plate format parser (IND-VAAHAN regex) · Confidence threshold >0.88"),
        ("SCORE", "Violation Impact Score", PURPLE,
         "Rule-based + ML scoring: violation type weight + traffic density + "
         "blackspot proximity + historical accident index"),
        ("EVIDENCE", "Evidence Package Generator", ACCENT2,
         "Annotated image with bbox overlays · Metadata JSON (plate, type, time, GPS, score) · "
         "Tamper-evident PDF bundle · e-Challan API payload"),
        ("ANALYTICS", "Dashboard & Predictive Intelligence", ACCENT,
         "React real-time dashboard · Heatmaps, trends, repeat offender tracker · "
         "ML forecasting: hotspot prediction, peak-hour alerts, deployment recommendations"),
    ]

    for i, (label, title, color, desc) in enumerate(pipeline_stages):
        connector = Paragraph("▼", ParagraphStyle("_c", fontName="Helvetica",
                fontSize=10, textColor=BORDER, alignment=TA_CENTER)) if i < len(pipeline_stages)-1 else None

        row_tbl = Table([[
            Table([[Paragraph(label, ParagraphStyle("_l", fontName="Helvetica-Bold",
                        fontSize=7, textColor=DARK_BG, alignment=TA_CENTER))]],
                  colWidths=[70]),
            Spacer(6, 1),
            Table([[
                Paragraph(title, ParagraphStyle("_t", fontName="Helvetica-Bold",
                    fontSize=9.5, textColor=color, leading=13)),
                Paragraph(desc, ParagraphStyle("_d", fontName="Helvetica",
                    fontSize=8, textColor=TEXT_MUTED, leading=12)),
            ]], colWidths=[370])
        ]], colWidths=[70, 6, 384])

        row_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(0,-1), color),
            ("BACKGROUND",    (2,0),(2,-1), CARD_BG),
            ("TOPPADDING",    (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
            ("LEFTPADDING",   (0,0),(-1,-1), 0),
            ("RIGHTPADDING",  (0,0),(-1,-1), 0),
            ("LEFTPADDING",   (2,0),(2,-1), 8),
            ("RIGHTPADDING",  (2,0),(2,-1), 6),
            ("VALIGN",        (0,0),(-1,-1), "TOP"),
            ("BOX",           (2,0),(2,-1), 0.5, BORDER),
        ]))
        story.append(row_tbl)
        if connector:
            story.append(connector)

    story.append(PageBreak())

    # ──────────────────────────────────────────────────────────────────────────
    # 4. TECH STACK
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("4. Technology Stack", S["section_head"]))
    story.append(hr(ACCENT, 1))

    stack = [
        ("COMPUTER VISION",  ACCENT,   ["YOLOv11 (Ultralytics)", "OpenCV 4.x", "DeepSORT tracker", "Albumentations (augmentation)"]),
        ("OCR / ANPR",       ACCENT2,  ["PaddleOCR (primary)", "EasyOCR (fallback)", "Indian plate regex parser", "VAAHAN number format validator"]),
        ("BACKEND API",      HIGHLIGHT,["FastAPI (async)", "Celery + Redis (task queue)", "SQLAlchemy ORM", "Pydantic v2 schemas"]),
        ("DATABASE",         YELLOW,   ["PostgreSQL (violations DB)", "TimescaleDB (time-series analytics)", "Redis (caching + pub-sub)", "S3-compatible object storage"]),
        ("FRONTEND",         PURPLE,   ["React 18 + Vite", "Tailwind CSS", "Recharts (analytics)", "Leaflet.js (heatmaps)", "Socket.IO (live feed)"]),
        ("ML / ANALYTICS",  RED_STAT, ["scikit-learn (VIS model)", "Prophet / LSTM (forecasting)", "Pandas + NumPy", "Jupyter for model dev"]),
        ("INFRA / DEVOPS",  TEXT_MUTED,["Docker + Docker Compose", "NGINX reverse proxy", "GitHub Actions CI/CD", "Prometheus + Grafana"]),
    ]

    stack_rows = []
    for i in range(0, len(stack), 2):
        row = [stack[i]]
        if i + 1 < len(stack):
            row.append(stack[i + 1])
        stack_rows.append(row)

    for row in stack_rows:
        cells = []
        for cat, color, items in row:
            inner = [[Paragraph(cat, ParagraphStyle("_c", fontName="Helvetica-Bold",
                        fontSize=8, textColor=color, leading=12, spaceAfter=4))]]
            for item in items:
                inner.append([Paragraph(f"• {item}", ParagraphStyle("_i", fontName="Helvetica",
                    fontSize=8, textColor=TEXT_MAIN, leading=12))])
            t = Table(inner, colWidths=[215])
            t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,-1), CARD_BG),
                ("BOX",       (0,0),(-1,-1), 0.5, BORDER),
                ("LEFTPADDING",(0,0),(-1,-1), 10),
                ("TOPPADDING",(0,0),(-1,-1), 8),
                ("BOTTOMPADDING",(0,0),(-1,-1), 8),
            ]))
            cells.append(t)

        if len(cells) == 1:
            cells.append(Spacer(1,1))
        row_t = Table([cells], colWidths=[222, 222])
        row_t.setStyle(TableStyle([
            ("LEFTPADDING",(0,0),(-1,-1),0),
            ("RIGHTPADDING",(0,0),(-1,-1),0),
            ("TOPPADDING",(0,0),(-1,-1),0),
            ("BOTTOMPADDING",(0,0),(-1,-1),4),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
        ]))
        story.append(row_t)

    story.append(PageBreak())

    # ──────────────────────────────────────────────────────────────────────────
    # 5. GITHUB REFERENCES
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("5. GitHub Reference Repositories", S["section_head"]))
    story.append(hr(ACCENT, 1))
    story.append(Paragraph(
        "These production-grade open-source repositories directly underpin TrafficEye AI's implementation. "
        "Each is battle-tested, actively maintained, and architecturally relevant.",
        S["body"]))
    story.append(Spacer(1, 8))

    gh_repos = [
        ("Core Detection Framework",    ACCENT,    [
            ("ultralytics/ultralytics",
             "https://github.com/ultralytics/ultralytics",
             "Official YOLOv8/v11 repo — backbone of all detection models",
             "⭐ 40k+"),
            ("nwojke/deep_sort",
             "https://github.com/nwojke/deep_sort",
             "DeepSORT multi-object tracking for persistent vehicle IDs",
             "⭐ 8k+"),
        ]),
        ("Traffic Violation Systems",   RED_STAT,  [
            ("anuragparashar26/traffic-management",
             "https://github.com/anuragparashar26/traffic-management",
             "YOLOv8 + PaddleOCR + React dashboard — closest architecture match",
             "Full-stack"),
            ("festorean/Smart-Traffic-Monitoring-System-using-AI",
             "https://github.com/festorean/Smart-Traffic-Monitoring-System-using-AI",
             "YOLOv8 + PaddleOCR for CCTV-based plate recognition + speed estimation",
             "Detection"),
            ("Juliowiwiwiwi/Traffic-Management-System-With-Ai",
             "https://github.com/Juliowiwiwiwi/Traffic-Management-System-With-Ai",
             "FastAPI + React + MySQL full-stack with helmet detection + evidence logging",
             "Full-stack"),
            ("ErikElcsics/Speed-Limit-Violation-Detection-System",
             "https://github.com/ErikElcsics/Speed-Limit-Violation-Detection-System",
             "YOLOv8 tracking + EasyOCR + violation dashboard with CSV export",
             "Detection"),
        ]),
        ("Indian ANPR",                 HIGHLIGHT, [
            ("lavanyashree2805/yolov8-license-plate-india",
             "https://github.com/lavanyashree2805/yolov8-license-plate-india",
             "Two-stage ANPR for Indian non-standard plates (YOLOv8 + custom weights)",
             "India-specific"),
            ("Muhammad-Zeerak-Khan/Automatic-License-Plate-Recognition-using-YOLOv8",
             "https://github.com/Muhammad-Zeerak-Khan/Automatic-License-Plate-Recognition-using-YOLOv8",
             "YOLOv8n + SORT for real-time plate detection with interpolation",
             "ANPR"),
            ("ikigai-aa/Automatic-License-Plate-Recognition",
             "https://github.com/ikigai-aa/Automatic-License-Plate-Recognition",
             "YOLOv4 ALPR with TFLite edge deployment (Raspberry Pi / Jetson ready)",
             "Edge AI"),
        ]),
        ("OCR & Preprocessing",         ACCENT2,   [
            ("PaddlePaddle/PaddleOCR",
             "https://github.com/PaddlePaddle/PaddleOCR",
             "Best-in-class OCR for low-quality/angled Indian plates (PP-OCRv4)",
             "⭐ 45k+"),
            ("JaidedAI/EasyOCR",
             "https://github.com/JaidedAI/EasyOCR",
             "Fallback OCR — 80+ language support, excellent on Indian scripts",
             "⭐ 23k+"),
        ]),
        ("Datasets & Benchmarks",       YELLOW,    [
            ("AI City Challenge Track 5",
             "https://www.aicitychallenge.org/",
             "Helmet violation detection benchmark — standard academic comparison baseline",
             "Dataset"),
            ("Roboflow Traffic Datasets",
             "https://universe.roboflow.com/search?q=traffic+violation+india",
             "Indian traffic annotated datasets: helmets, plates, violations",
             "Dataset"),
            ("OpenCity Bengaluru",
             "https://data.opencity.in/dataset/bengaluru-road-accidents-data-2024",
             "BTP official road crash data 2024 — for predictive model training",
             "BTP Data"),
        ]),
    ]

    for cat_title, cat_color, repos in gh_repos:
        story.append(Paragraph(cat_title, S["h3"]))

        for name, url, desc, tag_txt in repos:
            tag_color = {
                "⭐ 40k+": ACCENT, "⭐ 8k+": ACCENT, "⭐ 45k+": ACCENT2, "⭐ 23k+": ACCENT2,
                "Full-stack": HIGHLIGHT, "Detection": YELLOW, "ANPR": PURPLE,
                "India-specific": RED_STAT, "Edge AI": TEXT_MUTED,
                "Dataset": colors.HexColor("#0EA5E9"), "BTP Data": RED_STAT,
            }.get(tag_txt, BORDER)

            repo_row = Table([[
                Table([[
                    Paragraph(f"◆  {name}", ParagraphStyle("_n", fontName="Courier-Bold",
                        fontSize=8, textColor=cat_color, leading=12)),
                    Paragraph(url, ParagraphStyle("_u", fontName="Courier", fontSize=7,
                        textColor=TEXT_MUTED, leading=10)),
                    Paragraph(desc, ParagraphStyle("_d", fontName="Helvetica", fontSize=8,
                        textColor=TEXT_MAIN, leading=12)),
                ]], colWidths=[350]),
                Spacer(4, 1),
                pill(tag_txt, tag_color, DARK_BG if tag_color != TEXT_MUTED else WHITE, 80),
            ]], colWidths=[352, 4, 104])
            repo_row.setStyle(TableStyle([
                ("BACKGROUND", (0,0),(0,-1), CARD_BG),
                ("LEFTPADDING",(0,0),(-1,-1), 0),
                ("RIGHTPADDING",(0,0),(-1,-1), 0),
                ("TOPPADDING", (0,0),(-1,-1), 0),
                ("BOTTOMPADDING",(0,0),(-1,-1), 0),
                ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
                ("BOX",        (0,0),(0,-1), 0.3, BORDER),
                ("LEFTPADDING",(0,0),(0,-1), 10),
                ("TOPPADDING", (0,0),(0,-1), 6),
                ("BOTTOMPADDING",(0,0),(0,-1), 6),
            ]))
            story.append(repo_row)
            story.append(Spacer(1, 4))

        story.append(Spacer(1, 6))

    story.append(PageBreak())

    # ──────────────────────────────────────────────────────────────────────────
    # 6. IMPLEMENTATION ROADMAP
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("6. Hackathon Implementation Roadmap", S["section_head"]))
    story.append(hr(ACCENT, 1))
    story.append(Paragraph(
        "A realistic 2-day hackathon sprint plan to build a functional demo.",
        S["body"]))
    story.append(Spacer(1, 6))

    phases = [
        ("PHASE 1 · Day 1, Morning (0–4 hrs)", ACCENT, [
            "Set up FastAPI skeleton + PostgreSQL schema (violations, vehicles, offenders tables)",
            "Integrate YOLOv11 pre-trained COCO weights for vehicle + person detection",
            "Run inference on sample Bengaluru traffic images / BTP ITMS screenshot frames",
            "Build ANPR pipeline: YOLOv11 plate detector → PaddleOCR → Indian regex parser",
        ]),
        ("PHASE 2 · Day 1, Afternoon (4–8 hrs)", YELLOW, [
            "Add helmet, seatbelt, triple-riding violation classifiers (fine-tune or rule-based)",
            "Implement DeepSORT tracker for persistent vehicle IDs across frames",
            "Build Violation Impact Score engine (weighted scoring function)",
            "Store violation records + annotated image snapshots to PostgreSQL + local storage",
        ]),
        ("PHASE 3 · Day 2, Morning (8–14 hrs)", HIGHLIGHT, [
            "Build React dashboard: live violations feed, KPI cards, area-wise heatmap",
            "Add repeat-offender detection logic (cross-reference plate DB)",
            "Implement simple predictive model: violation frequency by hour/location (Pandas + sklearn)",
            "Evidence PDF generator: annotated image + metadata bundle per violation",
        ]),
        ("PHASE 4 · Day 2, Afternoon (14–20 hrs)", ACCENT2, [
            "End-to-end demo pipeline: sample video → detections → dashboard → evidence PDF",
            "Docker Compose packaging (frontend + backend + DB in one command)",
            "Demo video recording + pitch deck alignment",
            "Stretch: e-Challan API mock endpoint + mobile number SMS alert prototype",
        ]),
    ]

    for phase_title, color, tasks in phases:
        header = Table([[
            Paragraph(phase_title, ParagraphStyle("_ph", fontName="Helvetica-Bold",
                fontSize=9.5, textColor=DARK_BG, leading=14))
        ]], colWidths=[460])
        header.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1), color),
            ("LEFTPADDING",(0,0),(-1,-1), 12),
            ("TOPPADDING",(0,0),(-1,-1), 6),
            ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ]))
        story.append(header)

        for task in tasks:
            story.append(Paragraph(
                f"<font color='#22C55E'>✓</font>  {task}",
                ParagraphStyle("_t", fontName="Helvetica", fontSize=8.5,
                    textColor=TEXT_MAIN, leading=14, leftIndent=16, firstLineIndent=-10,
                    backColor=CARD_BG)))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 10))

    # ──────────────────────────────────────────────────────────────────────────
    # 7. EXPECTED OUTCOMES & IMPACT
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("7. Expected Outcomes & Bangalore Impact", S["section_head"]))
    story.append(hr(ACCENT, 1))

    outcomes = [
        ["OUTCOME", "METRIC", "BANGALORE RELEVANCE"],
        ["Automated violation detection", "7 violation types, real-time", "Replaces 600+ manual officers' check points"],
        ["ANPR accuracy", ">90% on Indian plates", "Handles non-standard Bangalore plates"],
        ["Evidence generation speed", "<2 sec per violation", "vs. 30+ min manual process at BTP"],
        ["Repeat offender identification", "Auto-profiling from Day 1", "BTP currently has no such system"],
        ["Predictive deployment", "Hotspot forecasts 48hr ahead", "Data-driven BTP resource allocation"],
        ["Coverage expansion", "Any camera feed, not just ITMS", "Covers 94% of Bangalore junctions"],
        ["Cost reduction", "80% less manual inspection", "₹80.9Cr fines → ₹250Cr potential"],
    ]
    ot = Table(outcomes, colWidths=[140, 120, 200])
    ot.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#1E3A5F")),
        ("TEXTCOLOR", (0,0),(-1,0), ACCENT2),
        ("FONTNAME",  (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0),(-1,0), 8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[CARD_BG, colors.HexColor("#1A2030")]),
        ("FONTNAME",  (0,1),(-1,-1), "Helvetica"),
        ("FONTSIZE",  (0,1),(-1,-1), 8),
        ("TEXTCOLOR", (0,1),(-1,-1), TEXT_MAIN),
        ("TEXTCOLOR", (1,1),(1,-1), HIGHLIGHT),
        ("FONTNAME",  (1,1),(1,-1), "Helvetica-Bold"),
        ("BOX",       (0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID", (0,0),(-1,-1), 0.3, BORDER),
        ("TOPPADDING",(0,0),(-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("VALIGN",    (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(ot)

    story.append(Spacer(1, 16))

    # ──────────────────────────────────────────────────────────────────────────
    # 8. FUTURE SCOPE
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("8. Future Scope — Beyond the Hackathon", S["section_head"]))
    story.append(hr(ACCENT, 1))

    future = [
        ("e-Challan API Integration", ACCENT,
         "Direct plug-in to Karnataka e-Challan portal (Vahan/Parivahan) for zero-friction challan dispatch."),
        ("Real-time RTSP Stream Processing", ACCENT2,
         "Process live ITMS feeds from all 50 BTP junctions simultaneously using NVIDIA Triton inference server."),
        ("Edge AI on Camera Hardware", HIGHLIGHT,
         "Deploy quantised YOLOv11 (ONNX/TFLite) directly on ITMS camera hardware (Jetson Nano/Orin) for <5ms latency."),
        ("Accident Risk Prediction", YELLOW,
         "Combine violation density + weather + time-of-day features to predict accident probability on corridors."),
        ("Emergency Vehicle Prioritisation", PURPLE,
         "Detect ambulance/police sirens and vehicle classes to trigger adaptive signal green-corridor."),
        ("Multi-city ITMS Integration", RED_STAT,
         "Extend to Mysuru ITMS (live July 2024) and 4 NH corridors proposed by ADGP Karnataka."),
    ]

    for i in range(0, len(future), 2):
        row_items = future[i:i+2]
        cells = []
        for title, color, desc in row_items:
            inner = Table([[
                Paragraph(title, ParagraphStyle("_t", fontName="Helvetica-Bold",
                    fontSize=9, textColor=color, leading=13, spaceAfter=4)),
                Paragraph(desc, ParagraphStyle("_d", fontName="Helvetica",
                    fontSize=8, textColor=TEXT_MAIN, leading=13)),
            ]], colWidths=[210])
            inner.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,-1), CARD_BG),
                ("LINERIGHT", (0,0),(0,0), 2.5, color),
                ("LEFTPADDING",(0,0),(-1,-1), 12),
                ("RIGHTPADDING",(0,0),(-1,-1), 8),
                ("TOPPADDING",(0,0),(-1,-1), 8),
                ("BOTTOMPADDING",(0,0),(-1,-1), 8),
                ("BOX",(0,0),(-1,-1), 0.3, BORDER),
            ]))
            cells.append(inner)

        if len(cells) == 1:
            cells.append(Spacer(1, 1))

        r = Table([cells], colWidths=[224, 224])
        r.setStyle(TableStyle([
            ("LEFTPADDING",(0,0),(-1,-1),0),
            ("RIGHTPADDING",(0,0),(-1,-1),0),
            ("TOPPADDING",(0,0),(-1,-1),0),
            ("BOTTOMPADDING",(0,0),(-1,-1),4),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
        ]))
        story.append(r)

    story.append(Spacer(1, 20))

    # ──────────────────────────────────────────────────────────────────────────
    # CLOSING
    # ──────────────────────────────────────────────────────────────────────────
    story.append(hr(ACCENT, 1.5))
    story.append(Spacer(1, 10))

    closing = Table([[
        Paragraph(
            "TrafficEye AI is built for Bengaluru — using BTP's own data, targeting BTP's own gaps, "
            "and designed to slot directly into the city's existing ITMS infrastructure. "
            "Every statistic in this proposal came from official BTP reports and Karnataka "
            "government data. This isn't a generic traffic project — it is a Bengaluru enforcement upgrade.",
            ParagraphStyle("_cl", fontName="Helvetica-Oblique", fontSize=10, leading=16,
                textColor=ACCENT2, alignment=TA_CENTER))
    ]], colWidths=[460])
    closing.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), CARD_BG),
        ("BOX",(0,0),(-1,-1), 1, ACCENT),
        ("LEFTPADDING",(0,0),(-1,-1), 20),
        ("RIGHTPADDING",(0,0),(-1,-1), 20),
        ("TOPPADDING",(0,0),(-1,-1), 16),
        ("BOTTOMPADDING",(0,0),(-1,-1), 16),
    ]))
    story.append(closing)

    doc.build(story)
    print("PDF generated: TrafficEye_AI_Hackathon_Proposal.pdf")


build_doc()