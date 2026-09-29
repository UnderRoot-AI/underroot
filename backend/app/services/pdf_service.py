"""
PDF report generator for UnderRoot soil analysis.

The PDF reflects the exact same data shown in the web UI:
same parameters, same units, same analysis statuses.

Units: N/P/K in kg/ha (consistent with frontend and analyzer).
"""
from __future__ import annotations
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from app.services.soil_analyzer import PARAM_RULES, analyze_parameters


# ── Palette ───────────────────────────────────────────────────────────────────
_GREEN_DARK   = colors.HexColor("#166534")
_GREEN_LIGHT  = colors.HexColor("#eaf6ec")
_GREEN_MED    = colors.HexColor("#dce6de")
_GREEN_ROW    = colors.HexColor("#f8fbf8")
_RED          = colors.HexColor("#dc2626")
_AMBER        = colors.HexColor("#d97706")
_BLUE         = colors.HexColor("#1d4ed8")

_STATUS_COLOR = {
    "Optimal":  _GREEN_DARK,
    "Low":      _AMBER,
    "High":     _AMBER,
    "Critical": _RED,
    "Missing":  colors.grey,
}


def _status_color(status: str) -> object:
    return _STATUS_COLOR.get(status, colors.black)


def build_soil_report_pdf(test: dict, crops: list[dict], fertilizers: list[dict]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small",  parent=styles["BodyText"], fontSize=8.0, leading=11))
    styles.add(ParagraphStyle(name="Title",  parent=styles["Heading1"], textColor=_GREEN_DARK, fontSize=17, spaceAfter=4))
    styles.add(ParagraphStyle(name="Sub",    parent=styles["Heading2"], textColor=_GREEN_DARK, fontSize=10.5, spaceBefore=9, spaceAfter=4))
    styles.add(ParagraphStyle(name="Muted",  parent=styles["BodyText"], fontSize=8.5, textColor=colors.HexColor("#57606a")))
    styles.add(ParagraphStyle(name="Bold",   parent=styles["BodyText"], fontSize=9.5, leading=13))

    story = []

    # ── Header ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("UnderRoot · Soil Analysis Report", styles["Title"]))
    loc_str = test.get("location") or "Field"
    date_str = test.get("created_at", "")
    if isinstance(date_str, datetime):
        date_str = date_str.strftime("%d %b %Y")
    elif isinstance(date_str, str) and "T" in date_str:
        date_str = date_str.split("T")[0]

    story.append(Paragraph(
        f"Test #{test['id']}  ·  {loc_str}  ·  {date_str}",
        styles["Muted"],
    ))
    story.append(Spacer(1, 4 * mm))

    # ── Health score summary ──────────────────────────────────────────────────
    score = test.get("health_score", 0)
    status = test.get("health_status", "—")
    story.append(Paragraph(
        f"Overall soil health: <b>{score}/100</b> — <b>{status}</b>",
        styles["Bold"],
    ))
    story.append(Spacer(1, 4 * mm))

    # ── Parameter table with status ───────────────────────────────────────────
    story.append(Paragraph("Measured Soil Parameters", styles["Sub"]))

    params = test.get("parameters", {})
    analysis = analyze_parameters(params)
    param_map = {r["key"]: r for r in analysis["parameter_analysis"]}

    rows = [["Parameter", "Value", "Unit", "Status"]]
    for key, rule in PARAM_RULES.items():
        r = param_map.get(key)
        if r:
            val_str = "—" if r["value"] is None else str(r["value"])
            rows.append([rule["label"], val_str, rule["unit"], r["status"]])

    tbl = Table(rows, colWidths=[65 * mm, 35 * mm, 25 * mm, 30 * mm])
    # Build per-row status coloring for status column (col index 3)
    row_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), _GREEN_LIGHT),
        ("TEXTCOLOR",  (0, 0), (-1, 0), _GREEN_DARK),
        ("GRID",       (0, 0), (-1, -1), 0.4, _GREEN_MED),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8.5),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _GREEN_ROW]),
    ]
    for i, row in enumerate(rows[1:], start=1):
        status_val = row[3]
        c = _status_color(status_val)
        row_styles.append(("TEXTCOLOR", (3, i), (3, i), c))
        if status_val == "Critical":
            row_styles.append(("FONTNAME", (3, i), (3, i), "Helvetica-Bold"))

    tbl.setStyle(TableStyle(row_styles))
    story.append(tbl)

    # ── Findings ──────────────────────────────────────────────────────────────
    deficiencies = analysis.get("deficiencies", [])
    excesses = analysis.get("excesses", [])
    warnings = analysis.get("warnings", [])

    if deficiencies or excesses or warnings:
        story.append(Paragraph("Key Findings", styles["Sub"]))
        if warnings:
            story.append(Paragraph(f"⚠ Critical: {', '.join(warnings)}", styles["Bold"]))
        if deficiencies:
            story.append(Paragraph(f"↓ Below optimal: {', '.join(deficiencies)}", styles["BodyText"]))
        if excesses:
            story.append(Paragraph(f"↑ Above optimal: {', '.join(excesses)}", styles["BodyText"]))
        story.append(Spacer(1, 3 * mm))

    # ── Crop recommendations ──────────────────────────────────────────────────
    story.append(Paragraph("Crop Recommendations", styles["Sub"]))
    crop_rows = [["Crop", "Suitability", "Season", "Notes"]]
    for c in crops[:4]:
        reason = c.get("reason", "")
        # Truncate long reason for table
        if len(reason) > 200:
            reason = reason[:197] + "…"
        crop_rows.append([
            c.get("crop", "—"),
            f"{c.get('suitability', 0)}%",
            c.get("season", "—"),
            reason,
        ])
    if len(crop_rows) == 1:
        crop_rows.append(["—", "—", "—", "Enter complete soil test data for crop recommendations."])

    ct = Table(crop_rows, colWidths=[28 * mm, 20 * mm, 28 * mm, 104 * mm])
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _GREEN_LIGHT),
        ("TEXTCOLOR",  (0, 0), (-1, 0), _GREEN_DARK),
        ("GRID",       (0, 0), (-1, -1), 0.35, _GREEN_MED),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 7.5),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _GREEN_ROW]),
    ]))
    story.append(ct)

    # ── Fertilizer recommendations ────────────────────────────────────────────
    story.append(Paragraph("Fertilizer Recommendations", styles["Sub"]))
    fert_rows = [["Recommendation", "Type", "Dose", "Notes"]]
    for f in fertilizers[:3]:
        reason = f.get("reason", "")
        if len(reason) > 180:
            reason = reason[:177] + "…"
        fert_rows.append([
            f.get("name", "—"),
            f.get("type", "—"),
            f.get("quantity", "—"),
            reason,
        ])
    if len(fert_rows) == 1:
        fert_rows.append(["—", "—", "—", "Complete the soil test first."])

    ft = Table(fert_rows, colWidths=[38 * mm, 18 * mm, 28 * mm, 96 * mm])
    ft.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _GREEN_LIGHT),
        ("TEXTCOLOR",  (0, 0), (-1, 0), _GREEN_DARK),
        ("GRID",       (0, 0), (-1, -1), 0.35, _GREEN_MED),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 7.5),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _GREEN_ROW]),
    ]))
    story.append(ft)

    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph(
        "Decision-support notice: The analysis above is an indicative screening based on "
        "published range thresholds for Indian agricultural conditions. "
        "Values and recommendations should be confirmed with a certified soil testing laboratory "
        "or local agricultural officer before making input decisions.",
        styles["Small"],
    ))

    doc.build(story)
    return buf.getvalue()
