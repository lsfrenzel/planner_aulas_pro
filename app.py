import json
import os
from flask import Flask, jsonify, request, render_template, send_file, Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

DATA_FILE = "data/weeks.json"

def load_weeks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_weeks(weeks):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(weeks, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/weeks", methods=["GET"])
def get_weeks():
    weeks = load_weeks()
    return jsonify(weeks)

@app.route("/api/weeks/<int:week_id>", methods=["GET"])
def get_week(week_id):
    weeks = load_weeks()
    for week in weeks:
        if week["semana"] == week_id:
            return jsonify(week)
    return jsonify({"error": "Semana não encontrada"}), 404

@app.route("/api/weeks", methods=["POST"])
def add_week():
    weeks = load_weeks()
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400
    
    max_semana = max([w["semana"] for w in weeks], default=0)
    new_week = {
        "semana": data.get("semana", max_semana + 1),
        "atividades": data.get("atividades", ""),
        "unidadeCurricular": data.get("unidadeCurricular", ""),
        "capacidades": data.get("capacidades", ""),
        "conhecimentos": data.get("conhecimentos", ""),
        "recursos": data.get("recursos", "")
    }
    
    weeks.append(new_week)
    weeks.sort(key=lambda x: x["semana"])
    save_weeks(weeks)
    
    return jsonify(new_week), 201

@app.route("/api/weeks/<int:week_id>", methods=["PUT"])
def update_week(week_id):
    weeks = load_weeks()
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400
    
    for i, week in enumerate(weeks):
        if week["semana"] == week_id:
            weeks[i] = {
                "semana": week_id,
                "atividades": data.get("atividades", week["atividades"]),
                "unidadeCurricular": data.get("unidadeCurricular", week["unidadeCurricular"]),
                "capacidades": data.get("capacidades", week["capacidades"]),
                "conhecimentos": data.get("conhecimentos", week["conhecimentos"]),
                "recursos": data.get("recursos", week["recursos"])
            }
            save_weeks(weeks)
            return jsonify(weeks[i])
    
    return jsonify({"error": "Semana não encontrada"}), 404

@app.route("/api/weeks/<int:week_id>", methods=["DELETE"])
def delete_week(week_id):
    weeks = load_weeks()
    
    for i, week in enumerate(weeks):
        if week["semana"] == week_id:
            deleted = weeks.pop(i)
            save_weeks(weeks)
            return jsonify({"message": "Semana excluída com sucesso", "deleted": deleted})
    
    return jsonify({"error": "Semana não encontrada"}), 404

@app.route("/api/export/json")
def export_json():
    weeks = load_weeks()
    response = Response(
        json.dumps(weeks, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=cronograma.json"}
    )
    return response

@app.route("/api/export/pdf")
def export_pdf():
    weeks = load_weeks()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=1
    )
    
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=7,
        leading=9
    )
    
    elements.append(Paragraph("Aula Planner Pro - Cronograma Completo", title_style))
    elements.append(Spacer(1, 10))
    
    headers = ["Semana", "Atividades", "Unidade Curricular", "Capacidades", "Conhecimentos", "Recursos"]
    
    data = [headers]
    for week in weeks:
        row = [
            str(week["semana"]),
            Paragraph(week["atividades"], cell_style),
            Paragraph(week["unidadeCurricular"], cell_style),
            Paragraph(week["capacidades"], cell_style),
            Paragraph(week["conhecimentos"], cell_style),
            Paragraph(week["recursos"], cell_style)
        ]
        data.append(row)
    
    col_widths = [1.2*cm, 5*cm, 4*cm, 5*cm, 4.5*cm, 4*cm]
    
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='cronograma.pdf'
    )

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
