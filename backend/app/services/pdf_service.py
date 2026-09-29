"""
PDF report generator for UnderRoot soil analysis.

Visual layout (A4, portrait):
  ┌─────────────────────────────────────────────────┐
  │  [LOGO]          SOIL HEALTH REPORT             │  ← header table
  │                  Test #N · Field · Date         │
  │  UnderRoot · Know Your Soil. Grow Smarter.      │  ← tagline rule
  ├─────────────────────────────────────────────────┤
  │  SOIL HEALTH SUMMARY  (score / status / note)   │
  ├─────────────────────────────────────────────────┤
  │  MEASURED PARAMETERS  (3-col: param | val | st) │
  │  KEY FINDINGS (optional)                        │
  ├─────────────────────────────────────────────────┤
  │  CROP RECOMMENDATIONS  (4-col with wrap)        │
  │  FERTILIZER RECOMMENDATIONS (4-col with wrap)   │
  │  DECISION-SUPPORT NOTICE                        │
  └─────────────────────────────────────────────────┘
  Footer: UnderRoot · Know Your Soil. Grow Smarter. | Page N

Data contract: unchanged — all values come from the caller's test/analysis dicts.
Units: N/P/K in kg/ha (consistent with frontend and analyzer).
"""
from __future__ import annotations

from io import BytesIO
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
    KeepTogether, HRFlowable, Image as RLImage,
)

from app.services.soil_analyzer import PARAM_RULES, analyze_parameters

# ── Asset path ────────────────────────────────────────────────────────────────
_ASSETS = Path(__file__).parent.parent / "assets"
_LOGO_PATH = _ASSETS / "underroot-logo.png"

# ── Palette (UnderRoot brand) ─────────────────────────────────────────────────
_FOREST      = colors.HexColor("#17211D")   # primary text
_GREEN_DARK  = colors.HexColor("#35664D")   # heading / Optimal
_GREEN_LIGHT = colors.HexColor("#EAF6EC")   # header bg tint
_GREEN_MED   = colors.HexColor("#C8DED0")   # grid lines
_GREEN_ALT   = colors.HexColor("#F4F7F5")   # alternating rows / surfaces
_AMBER       = colors.HexColor("#A47B2C")   # Low / High
_RED         = colors.HexColor("#A74646")   # Critical
_MUTED       = colors.HexColor("#57666A")   # secondary text
_RULE        = colors.HexColor("#DCE6DE")   # horizontal rules
_WHITE       = colors.white

_STATUS_COLOR = {
    "Optimal":  _GREEN_DARK,
    "Low":      _AMBER,
    "High":     _AMBER,
    "Critical": _RED,
    "Missing":  _MUTED,
}

# ── Page geometry ─────────────────────────────────────────────────────────────
_PAGE_W, _PAGE_H = A4          # 210 × 297 mm
_MARGIN_LR = 16 * mm
_MARGIN_TOP = 14 * mm
_MARGIN_BOT = 20 * mm          # extra bottom margin for footer
_CONTENT_W  = _PAGE_W - 2 * _MARGIN_LR   # usable content width ≈ 178 mm


# ── Footer canvas callback ────────────────────────────────────────────────────
def _draw_footer(canvas, doc):
    """Draw the footer on every page: tagline left, page number right."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_MUTED)

    y = 10 * mm
    canvas.drawString(_MARGIN_LR, y,
                      "UnderRoot  ·  Know Your Soil. Grow Smarter.")
    canvas.drawRightString(_PAGE_W - _MARGIN_LR, y,
                           f"Page {doc.page}")

    # thin rule above footer
    canvas.setStrokeColor(_RULE)
    canvas.setLineWidth(0.4)
    canvas.line(_MARGIN_LR, y + 5 * mm,
                _PAGE_W - _MARGIN_LR, y + 5 * mm)
    canvas.restoreState()


# ── Style factory ─────────────────────────────────────────────────────────────
def _make_styles():
    ss = getSampleStyleSheet()

    def add(name, **kw):
        ss.add(ParagraphStyle(name=name, **kw))

    add("RptTitle",
        parent=ss["Normal"],
        fontSize=17, leading=21,
        fontName="Helvetica-Bold",
        textColor=_FOREST)

    add("RptSubtitle",
        parent=ss["Normal"],
        fontSize=8.5, leading=12,
        textColor=_MUTED)

    add("RptTagline",
        parent=ss["Normal"],
        fontSize=8, leading=11,
        textColor=_MUTED,
        spaceAfter=0)

    add("SectionHead",
        parent=ss["Normal"],
        fontSize=9, leading=12,
        fontName="Helvetica-Bold",
        textColor=_GREEN_DARK,
        spaceBefore=10, spaceAfter=5,
        textTransform="uppercase",
        letterSpacing=0.8)

    add("HealthScore",
        parent=ss["Normal"],
        fontSize=28, leading=30,
        fontName="Helvetica-Bold",
        textColor=_FOREST)

    add("HealthStatus",
        parent=ss["Normal"],
        fontSize=13, leading=16,
        fontName="Helvetica-Bold",
        textColor=_GREEN_DARK)

    add("HealthNote",
        parent=ss["Normal"],
        fontSize=8.5, leading=12,
        textColor=_MUTED)

    add("CellBody",
        parent=ss["Normal"],
        fontSize=8, leading=11,
        textColor=_FOREST)

    add("CellMuted",
        parent=ss["Normal"],
        fontSize=7.5, leading=11,
        textColor=_MUTED)

    add("Notice",
        parent=ss["Normal"],
        fontSize=7.5, leading=11,
        textColor=_MUTED,
        spaceBefore=4)

    add("FindingLine",
        parent=ss["Normal"],
        fontSize=8.5, leading=12,
        textColor=_FOREST)

    return ss


# ── Helper: safe Paragraph (escapes & in text for ReportLab XML) ──────────────
def _p(text: str, style) -> Paragraph:
    safe = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(safe, style)


def _status_color(status: str):
    return _STATUS_COLOR.get(status, _FOREST)


# ── Main builder ──────────────────────────────────────────────────────────────
def build_soil_report_pdf(test: dict, crops: list[dict], fertilizers: list[dict]) -> bytes:
    buf = BytesIO()

    # BaseDocTemplate gives us full control over frames/templates
    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=_MARGIN_LR,
        leftMargin=_MARGIN_LR,
        topMargin=_MARGIN_TOP,
        bottomMargin=_MARGIN_BOT,
    )

    frame = Frame(
        _MARGIN_LR, _MARGIN_BOT,
        _CONTENT_W, _PAGE_H - _MARGIN_TOP - _MARGIN_BOT,
        id="main", leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame],
                                       onPage=_draw_footer)])

    S = _make_styles()
    story = []

    # ── Format date ───────────────────────────────────────────────────────────
    date_str = test.get("created_at", "")
    if isinstance(date_str, datetime):
        date_str = date_str.strftime("%d %b %Y")
    elif isinstance(date_str, str):
        if "T" in date_str:
            date_str = date_str.split("T")[0]
        # reformat YYYY-MM-DD → DD Mon YYYY when possible
        try:
            date_str = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d %b %Y")
        except ValueError:
            pass

    loc_str = test.get("location") or "Field"
    test_id = test.get("id", "—")

    # ── HEADER TABLE: [logo] | [title block] ─────────────────────────────────
    logo_cell: list = []
    if _LOGO_PATH.exists():
        logo_img = RLImage(str(_LOGO_PATH))
        aspect = logo_img.imageWidth / max(logo_img.imageHeight, 1)
        logo_h = 14 * mm
        logo_w = logo_h * aspect
        logo_img._restrictSize(logo_w, logo_h)
        logo_cell = [logo_img]
    else:
        logo_cell = [_p("UnderRoot", S["RptTitle"])]

    title_block = [
        [_p("SOIL HEALTH REPORT", S["RptTitle"])],
        [_p(f"Test #{test_id}  ·  {loc_str}  ·  {date_str}", S["RptSubtitle"])],
    ]

    logo_col_w = 20 * mm
    title_col_w = _CONTENT_W - logo_col_w - 4 * mm

    hdr_tbl = Table(
        [[logo_cell, Table(title_block,
                           colWidths=[title_col_w],
                           style=TableStyle([
                               ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
                               ("LEFTPADDING",  (0, 0), (-1, -1), 0),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                               ("TOPPADDING",   (0, 0), (-1, -1), 1),
                               ("BOTTOMPADDING",(0, 0), (-1, -1), 1),
                           ]))
         ]],
        colWidths=[logo_col_w + 4 * mm, title_col_w],
    )
    hdr_tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 2 * mm))

    # Tagline rule
    story.append(HRFlowable(width="100%", thickness=0.5, color=_RULE,
                             spaceAfter=2 * mm))
    story.append(_p("UnderRoot  ·  Know Your Soil. Grow Smarter.", S["RptTagline"]))
    story.append(Spacer(1, 5 * mm))

    # ── HEALTH SUMMARY ────────────────────────────────────────────────────────
    score       = test.get("health_score", 0)
    health_st   = test.get("health_status", "—")
    score_disp  = f"{score}/100"

    params      = test.get("parameters", {})
    analysis    = analyze_parameters(params)
    deficiencies = analysis.get("deficiencies", [])
    excesses     = analysis.get("excesses", [])
    warnings     = analysis.get("warnings", [])

    if deficiencies or excesses or warnings:
        health_note = (
            ("⚠ Critical: " + ", ".join(warnings) + ".  " if warnings else "") +
            ("Below optimal: " + ", ".join(deficiencies) + ".  " if deficiencies else "") +
            ("Above optimal: " + ", ".join(excesses) + "." if excesses else "")
        ).strip()
    else:
        health_note = "All measured parameters are currently within the defined optimal ranges."

    health_tbl = Table(
        [[
            _p(score_disp, S["HealthScore"]),
            Table(
                [[_p(health_st, S["HealthStatus"])],
                 [_p(health_note, S["HealthNote"])]],
                colWidths=[_CONTENT_W - 40 * mm],
                style=TableStyle([
                    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
                    ("TOPPADDING",    (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]),
            ),
        ]],
        colWidths=[40 * mm, _CONTENT_W - 40 * mm],
    )
    health_tbl.setStyle(TableStyle([
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND",     (0, 0), (-1, -1), _GREEN_ALT),
        ("ROUNDEDCORNERS", [6],),
        ("LEFTPADDING",    (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 10),
        ("TOPPADDING",     (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 10),
    ]))

    story.append(_p("Soil Health", S["SectionHead"]))
    story.append(KeepTogether([health_tbl]))
    story.append(Spacer(1, 5 * mm))

    # ── PARAMETERS TABLE (3 columns: Parameter | Value+Unit | Status) ─────────
    # Merge Value + Unit into one cell to avoid 4-col layout squeezing the label
    col_param  = 72 * mm
    col_val    = 60 * mm
    col_status = _CONTENT_W - col_param - col_val

    story.append(_p("Measured Soil Parameters", S["SectionHead"]))

    param_map = {r["key"]: r for r in analysis["parameter_analysis"]}

    hdr_row = [
        _p("Parameter",    S["CellBody"]),
        _p("Value",        S["CellBody"]),
        _p("Status",       S["CellBody"]),
    ]
    p_rows = [hdr_row]
    for key, rule in PARAM_RULES.items():
        r = param_map.get(key)
        if not r:
            continue
        val_str = "—" if r["value"] is None else f"{r['value']} {rule['unit']}".strip()
        p_rows.append([
            _p(rule["label"],   S["CellBody"]),
            _p(val_str,         S["CellBody"]),
            _p(r["status"],     S["CellBody"]),
        ])

    p_tbl = Table(p_rows, colWidths=[col_param, col_val, col_status],
                  repeatRows=1)

    p_style = [
        ("BACKGROUND",    (0, 0), (-1, 0), _GREEN_LIGHT),
        ("TEXTCOLOR",     (0, 0), (-1, 0), _GREEN_DARK),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
        ("GRID",          (0, 0), (-1, -1), 0.35, _GREEN_MED),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_WHITE, _GREEN_ALT]),
    ]
    for i, row in enumerate(p_rows[1:], start=1):
        status_val = row[2].text if hasattr(row[2], "text") else ""
        # Extract the status text from the Paragraph
        status_val = analysis["parameter_analysis"][i - 1]["status"]
        c = _status_color(status_val)
        p_style.append(("TEXTCOLOR",  (2, i), (2, i), c))
        if status_val == "Critical":
            p_style.append(("FONTNAME", (2, i), (2, i), "Helvetica-Bold"))

    p_tbl.setStyle(TableStyle(p_style))
    story.append(p_tbl)
    story.append(Spacer(1, 4 * mm))

    # ── KEY FINDINGS (only if any) ────────────────────────────────────────────
    if deficiencies or excesses or warnings:
        findings = []
        findings.append(_p("Key Findings", S["SectionHead"]))
        if warnings:
            findings.append(_p(f"⚠ Critical: {', '.join(warnings)}", S["FindingLine"]))
        if deficiencies:
            findings.append(_p(f"↓ Below optimal: {', '.join(deficiencies)}", S["FindingLine"]))
        if excesses:
            findings.append(_p(f"↑ Above optimal: {', '.join(excesses)}", S["FindingLine"]))
        findings.append(Spacer(1, 3 * mm))
        story.append(KeepTogether(findings))

    # ── CROP RECOMMENDATIONS ──────────────────────────────────────────────────
    # Columns: Crop | Suitability | Season | Notes
    # Notes gets the majority of the width; all cells use Paragraph so they wrap
    story.append(_p("Crop Recommendations", S["SectionHead"]))

    c_crop = 28 * mm
    c_suit = 18 * mm
    c_seas = 34 * mm
    c_note = _CONTENT_W - c_crop - c_suit - c_seas

    crop_hdr = [
        _p("Crop",        S["CellBody"]),
        _p("Suitability", S["CellBody"]),
        _p("Season",      S["CellBody"]),
        _p("Notes",       S["CellBody"]),
    ]
    crop_rows = [crop_hdr]

    display_crops = crops[:5] if crops else []
    for c in display_crops:
        reason = c.get("reason", "")
        crop_rows.append([
            _p(c.get("crop", "—"),              S["CellBody"]),
            _p(f"{c.get('suitability', 0)}%",   S["CellMuted"]),
            _p(c.get("season", "—"),             S["CellBody"]),
            _p(reason,                           S["CellBody"]),
        ])

    if len(crop_rows) == 1:
        crop_rows.append([
            _p("—", S["CellMuted"]),
            _p("—", S["CellMuted"]),
            _p("—", S["CellMuted"]),
            _p("Enter complete soil test data for crop recommendations.", S["CellMuted"]),
        ])

    c_tbl = Table(crop_rows,
                  colWidths=[c_crop, c_suit, c_seas, c_note],
                  repeatRows=1,
                  splitByRow=True)
    c_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), _GREEN_LIGHT),
        ("TEXTCOLOR",     (0, 0), (-1, 0), _GREEN_DARK),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.35, _GREEN_MED),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_WHITE, _GREEN_ALT]),
    ]))
    story.append(c_tbl)
    story.append(Spacer(1, 4 * mm))

    # ── FERTILIZER RECOMMENDATIONS ────────────────────────────────────────────
    # Columns: Recommendation | Type | Dose | Notes
    story.append(_p("Fertilizer Recommendations", S["SectionHead"]))

    f_name = 38 * mm
    f_type = 18 * mm
    f_dose = 30 * mm
    f_note = _CONTENT_W - f_name - f_type - f_dose

    fert_hdr = [
        _p("Recommendation", S["CellBody"]),
        _p("Type",           S["CellBody"]),
        _p("Dose",           S["CellBody"]),
        _p("Notes",          S["CellBody"]),
    ]
    fert_rows = [fert_hdr]

    display_ferts = fertilizers[:3] if fertilizers else []
    for f in display_ferts:
        fert_rows.append([
            _p(f.get("name", "—"),     S["CellBody"]),
            _p(f.get("type", "—"),     S["CellMuted"]),
            _p(f.get("quantity", "—"), S["CellBody"]),
            _p(f.get("reason", "—"),   S["CellBody"]),
        ])

    if len(fert_rows) == 1:
        fert_rows.append([
            _p("—", S["CellMuted"]),
            _p("—", S["CellMuted"]),
            _p("—", S["CellMuted"]),
            _p("Complete the soil test first.", S["CellMuted"]),
        ])

    f_tbl = Table(fert_rows,
                  colWidths=[f_name, f_type, f_dose, f_note],
                  repeatRows=1,
                  splitByRow=True)
    f_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), _GREEN_LIGHT),
        ("TEXTCOLOR",     (0, 0), (-1, 0), _GREEN_DARK),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.35, _GREEN_MED),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_WHITE, _GREEN_ALT]),
    ]))
    story.append(f_tbl)
    story.append(Spacer(1, 5 * mm))

    # ── DECISION-SUPPORT NOTICE ───────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.4, color=_RULE,
                             spaceAfter=3 * mm))
    story.append(_p("DECISION-SUPPORT NOTICE", S["SectionHead"]))
    story.append(_p(
        "The analysis above is an indicative screening based on published range thresholds "
        "for Indian agricultural conditions. Values and recommendations should be confirmed "
        "with a certified soil testing laboratory or local agricultural officer before making "
        "input decisions.",
        S["Notice"],
    ))

    doc.build(story)
    return buf.getvalue()
