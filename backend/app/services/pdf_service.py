from __future__ import annotations
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.graphics.shapes import Drawing, Rect, String


def build_soil_report_pdf(test: dict, crops: list[dict], fertilizers: list[dict]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=14*mm, bottomMargin=14*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.5, leading=11))
    styles.add(ParagraphStyle(name="Green", parent=styles["Heading1"], textColor=colors.HexColor("#166534"), fontSize=18, spaceAfter=7))
    styles.add(ParagraphStyle(name="Sub", parent=styles["Heading2"], textColor=colors.HexColor("#166534"), fontSize=11, spaceBefore=9, spaceAfter=5))
    story=[]
    story.append(Paragraph("Smart Soil Health — Soil Analysis Report", styles["Green"]))
    story.append(Paragraph(f"Test #{test['id']} · {test.get('location') or 'Field'} · {test.get('created_at','')}", styles["Small"]))
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(f"Overall soil health: <b>{test.get('health_score',0)}/100</b> — {test.get('health_status','Analyzed')}", styles["BodyText"]))

    params=test.get("parameters",{})
    rows=[["Parameter","Value","Unit"]]
    units={"ph":"","nitrogen":"mg/kg","phosphorus":"mg/kg","potassium":"mg/kg","ec":"dS/m","moisture":"%","temperature":"°C","organic_carbon":"%"}
    labels={"ph":"pH","nitrogen":"Nitrogen","phosphorus":"Phosphorus","potassium":"Potassium","ec":"EC","moisture":"Moisture","temperature":"Temperature","organic_carbon":"Organic carbon"}
    for k,v in params.items():
        if v is not None: rows.append([labels.get(k,k.replace("_"," ").title()), str(v), units.get(k,"")])
    story.append(Paragraph("Measured soil parameters", styles["Sub"]))
    table=Table(rows,colWidths=[65*mm,45*mm,35*mm])
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#eaf6ec")),("TEXTCOLOR",(0,0),(-1,0),colors.HexColor("#166534")),("GRID",(0,0),(-1,-1),.4,colors.HexColor("#dce6de")),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8.5),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f8fbf8")])]))
    story.append(table)

    # Simple graphical bar chart, normalized for display only.
    display=[(labels.get(k,k),float(v)) for k,v in params.items() if isinstance(v,(int,float))]
    if display:
        story.append(Paragraph("Parameter profile (visual scale)", styles["Sub"]))
        d=Drawing(500, max(55, len(display)*22))
        maxv=max(v for _,v in display) or 1
        for i,(label,val) in enumerate(display):
            y=max(5, len(display)*22-20-i*22)
            width=300*min(1,val/maxv)
            d.add(String(0,y+4,label,fontSize=7))
            d.add(Rect(95,y,300,10,fillColor=colors.HexColor("#edf2ed"),strokeColor=None))
            d.add(Rect(95,y,width,10,fillColor=colors.HexColor("#166534"),strokeColor=None))
            d.add(String(402,y+2,f"{val:g}",fontSize=7))
        story.append(d)

    story.append(Paragraph("Crop recommendation", styles["Sub"]))
    crop_rows=[["Crop","Suitability","Season","Reason"]]
    for c in crops[:5]: crop_rows.append([c.get("crop"),f"{c.get('suitability')}%",c.get("season","—"),c.get("reason","")])
    if len(crop_rows)==1: crop_rows.append(["No model result","—","—","Enter a complete soil test to generate recommendations."])
    ct=Table(crop_rows,colWidths=[30*mm,25*mm,25*mm,100*mm])
    ct.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#eaf6ec")),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#dce6de")),("FONTSIZE",(0,0),(-1,-1),7.5),("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(ct)

    story.append(Paragraph("Fertilizer recommendation", styles["Sub"]))
    fert_rows=[["Recommendation","Type","Reason"]]
    for f in fertilizers[:3]: fert_rows.append([f.get("name"),f.get("type","—"),f.get("reason","")])
    if len(fert_rows)==1: fert_rows.append(["No result","—","Complete the soil test first."])
    ft=Table(fert_rows,colWidths=[45*mm,25*mm,110*mm])
    ft.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#eaf6ec")),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#dce6de")),("FONTSIZE",(0,0),(-1,-1),7.5),("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(ft)
    story.append(Spacer(1,5*mm))
    story.append(Paragraph("Decision-support note: model outputs are screening recommendations trained on the project's development dataset. Confirm crop suitability, fertilizer dose, units and field-specific treatment with a soil laboratory or local agricultural professional.", styles["Small"]))
    doc.build(story)
    return buf.getvalue()
