import json
import os
import sqlite3
from functools import wraps
from flask import Flask, jsonify, request, render_template, send_file, Response, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

DATA_FILE = "data/weeks.json"
USERS_DB = "data/users.db"

def init_db():
    os.makedirs(os.path.dirname(USERS_DB), exist_ok=True)
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    if cursor.fetchone()[0] == 0:
        admin_password = generate_password_hash("admin123")
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Administrador", "admin@aula.com", admin_password, "admin")
        )
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                return jsonify({"error": "Não autorizado"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                return jsonify({"error": "Não autorizado"}), 401
            return redirect(url_for('login'))
        if session.get('user_role') != 'admin':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                return jsonify({"error": "Acesso negado"}), 403
            flash("Acesso negado. Apenas administradores podem acessar esta área.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def load_weeks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_weeks(weeks):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(weeks, f, ensure_ascii=False, indent=2)

@app.route("/login", methods=["GET", "POST"])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        if not email or not password:
            flash("Por favor, preencha todos os campos.", "error")
            return render_template("login.html")
        
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ? AND active = 1", (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user["password_hash"], password):
            session['user_id'] = user["id"]
            session['user_name'] = user["name"]
            session['user_email'] = user["email"]
            session['user_role'] = user["role"]
            flash(f"Bem-vindo, {user['name']}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Email ou senha incorretos.", "error")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for('login'))

@app.route("/")
@login_required
def index():
    return render_template("index.html", user=session)

@app.route("/admin")
@admin_required
def admin_panel():
    return render_template("admin.html", user=session)

@app.route("/api/users", methods=["GET"])
@admin_required
def get_users():
    conn = get_db()
    users = conn.execute("SELECT id, name, email, role, active, created_at FROM users ORDER BY id").fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])

@app.route("/api/users", methods=["POST"])
@admin_required
def add_user():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400
    
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "user")
    
    if not name or not email or not password:
        return jsonify({"error": "Nome, email e senha são obrigatórios"}), 400
    
    if role not in ["user", "admin"]:
        role = "user"
    
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (name, email, generate_password_hash(password), role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        user = conn.execute("SELECT id, name, email, role, active, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return jsonify(dict(user)), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Email já cadastrado"}), 400

@app.route("/api/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({"error": "Usuário não encontrado"}), 404
    
    name = data.get("name", user["name"]).strip()
    email = data.get("email", user["email"]).strip()
    role = data.get("role", user["role"])
    active = data.get("active", user["active"])
    
    if role not in ["user", "admin"]:
        role = user["role"]
    
    try:
        if "password" in data and data["password"]:
            conn.execute(
                "UPDATE users SET name = ?, email = ?, password_hash = ?, role = ?, active = ? WHERE id = ?",
                (name, email, generate_password_hash(data["password"]), role, active, user_id)
            )
        else:
            conn.execute(
                "UPDATE users SET name = ?, email = ?, role = ?, active = ? WHERE id = ?",
                (name, email, role, active, user_id)
            )
        conn.commit()
        updated_user = conn.execute("SELECT id, name, email, role, active, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return jsonify(dict(updated_user))
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Email já cadastrado"}), 400

@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    if session.get('user_id') == user_id:
        return jsonify({"error": "Você não pode excluir sua própria conta"}), 400
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({"error": "Usuário não encontrado"}), 404
    
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Usuário excluído com sucesso"})

@app.route("/api/weeks", methods=["GET"])
@login_required
def get_weeks():
    weeks = load_weeks()
    return jsonify(weeks)

@app.route("/api/weeks/<int:week_id>", methods=["GET"])
@login_required
def get_week(week_id):
    weeks = load_weeks()
    for week in weeks:
        if week["semana"] == week_id:
            return jsonify(week)
    return jsonify({"error": "Semana não encontrada"}), 404

@app.route("/api/weeks", methods=["POST"])
@login_required
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
@login_required
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
@login_required
def delete_week(week_id):
    weeks = load_weeks()
    
    for i, week in enumerate(weeks):
        if week["semana"] == week_id:
            deleted = weeks.pop(i)
            save_weeks(weeks)
            return jsonify({"message": "Semana excluída com sucesso", "deleted": deleted})
    
    return jsonify({"error": "Semana não encontrada"}), 404

@app.route("/api/export/json")
@login_required
def export_json():
    weeks = load_weeks()
    response = Response(
        json.dumps(weeks, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=cronograma.json"}
    )
    return response

@app.route("/api/export/pdf")
@login_required
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

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
