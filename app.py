import json
import os
import logging
from functools import wraps
from flask import Flask, jsonify, request, render_template, send_file, Response, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO

logging.basicConfig(level=logging.DEBUG)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    
if not database_url:
    raise RuntimeError("DATABASE_URL environment variable must be set. Please configure your PostgreSQL database connection.")
    
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

DATA_FILE = "data/weeks.json"


def init_data():
    from models import User, Schedule, Turma
    
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            name="Administrador",
            email="admin@aula.com",
            password_hash=generate_password_hash("admin123"),
            role="admin",
            active=True
        )
        db.session.add(admin)
        db.session.commit()
        
        default_turma = Turma(
            user_id=admin.id,
            nome="Tecnico em Programacao de Jogos Digitais",
            descricao="Curso tecnico de desenvolvimento de jogos digitais",
            cor="blue",
            active=True
        )
        db.session.add(default_turma)
        db.session.commit()
        
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                weeks = json.load(f)
            for week in weeks:
                schedule = Schedule(
                    user_id=admin.id,
                    turma_id=default_turma.id,
                    semana=week.get("semana", 0),
                    atividades=week.get("atividades", ""),
                    unidade_curricular=week.get("unidadeCurricular", ""),
                    capacidades=week.get("capacidades", ""),
                    conhecimentos=week.get("conhecimentos", ""),
                    recursos=week.get("recursos", "")
                )
                db.session.add(schedule)
            db.session.commit()
    else:
        default_turma = Turma.query.filter_by(user_id=admin.id, nome="Tecnico em Programacao de Jogos Digitais").first()
        if not default_turma:
            default_turma = Turma(
                user_id=admin.id,
                nome="Tecnico em Programacao de Jogos Digitais",
                descricao="Curso tecnico de desenvolvimento de jogos digitais",
                cor="blue",
                active=True
            )
            db.session.add(default_turma)
            db.session.commit()
            
            orphan_schedules = Schedule.query.filter_by(user_id=admin.id, turma_id=None).all()
            for schedule in orphan_schedules:
                schedule.turma_id = default_turma.id
            db.session.commit()


with app.app_context():
    import models
    db.create_all()
    init_data()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                return jsonify({"error": "Nao autorizado"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                return jsonify({"error": "Nao autorizado"}), 401
            return redirect(url_for('login'))
        if session.get('user_role') != 'admin':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                return jsonify({"error": "Acesso negado"}), 403
            flash("Acesso negado. Apenas administradores podem acessar esta area.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login():
    from models import User
    
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        if not email or not password:
            flash("Por favor, preencha todos os campos.", "error")
            return render_template("login.html")
        
        user = User.query.filter_by(email=email, active=True).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            session['user_role'] = user.role
            flash(f"Bem-vindo, {user.name}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Email ou senha incorretos.", "error")
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Voce saiu do sistema.", "info")
    return redirect(url_for('login'))


@app.route("/")
@login_required
def index():
    return render_template("index.html", user=session)


@app.route("/dashboard")
@login_required
def dashboard():
    from models import Schedule
    
    user_id = session['user_id']
    schedules = Schedule.query.filter_by(user_id=user_id).order_by(Schedule.semana).all()
    
    weeks = [s.to_dict() for s in schedules]
    
    unidades = set()
    recursos_set = set()
    for s in schedules:
        if s.unidade_curricular:
            unidades.add(s.unidade_curricular)
        if s.recursos:
            for r in s.recursos.split(','):
                recursos_set.add(r.strip())
    
    return render_template("dashboard.html", 
                          user=session, 
                          weeks=weeks,
                          unidades=list(unidades),
                          recursos=list(recursos_set))


@app.route("/admin")
@admin_required
def admin_panel():
    return render_template("admin.html", user=session)


@app.route("/turmas")
@login_required
def turmas_page():
    return render_template("turmas.html", user=session)


@app.route("/api/turmas", methods=["GET"])
@login_required
def get_turmas():
    from models import Turma
    user_id = session['user_id']
    turmas = Turma.query.filter_by(user_id=user_id, active=True).order_by(Turma.nome).all()
    return jsonify([t.to_dict() for t in turmas])


@app.route("/api/turmas", methods=["POST"])
@login_required
def add_turma():
    from models import Turma
    
    user_id = session['user_id']
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Dados invalidos"}), 400
    
    nome = data.get("nome", "").strip()
    descricao = data.get("descricao", "").strip()
    cor = data.get("cor", "blue")
    
    if not nome:
        return jsonify({"error": "Nome da turma e obrigatorio"}), 400
    
    turma = Turma(
        user_id=user_id,
        nome=nome,
        descricao=descricao,
        cor=cor,
        active=True
    )
    db.session.add(turma)
    db.session.commit()
    
    return jsonify(turma.to_dict()), 201


@app.route("/api/turmas/<int:turma_id>", methods=["PUT"])
@login_required
def update_turma(turma_id):
    from models import Turma
    
    user_id = session['user_id']
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Dados invalidos"}), 400
    
    turma = Turma.query.filter_by(id=turma_id, user_id=user_id).first()
    
    if not turma:
        return jsonify({"error": "Turma nao encontrada"}), 404
    
    turma.nome = data.get("nome", turma.nome).strip()
    turma.descricao = data.get("descricao", turma.descricao).strip()
    turma.cor = data.get("cor", turma.cor)
    
    db.session.commit()
    
    return jsonify(turma.to_dict())


@app.route("/api/turmas/<int:turma_id>", methods=["DELETE"])
@login_required
def delete_turma(turma_id):
    from models import Turma
    
    user_id = session['user_id']
    turma = Turma.query.filter_by(id=turma_id, user_id=user_id).first()
    
    if not turma:
        return jsonify({"error": "Turma nao encontrada"}), 404
    
    turma.active = False
    db.session.commit()
    
    return jsonify({"message": "Turma excluida com sucesso"})


@app.route("/api/users", methods=["GET"])
@admin_required
def get_users():
    from models import User
    users = User.query.order_by(User.id).all()
    return jsonify([u.to_dict() for u in users])


@app.route("/api/users", methods=["POST"])
@admin_required
def add_user():
    from models import User
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Dados invalidos"}), 400
    
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "user")
    
    if not name or not email or not password:
        return jsonify({"error": "Nome, email e senha sao obrigatorios"}), 400
    
    if role not in ["user", "admin"]:
        role = "user"
    
    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "Email ja cadastrado"}), 400
    
    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
        active=True
    )
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict()), 201


@app.route("/api/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    from models import User
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Dados invalidos"}), 400
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    
    user.name = data.get("name", user.name).strip()
    email = data.get("email", user.email).strip()
    role = data.get("role", user.role)
    active = data.get("active", user.active)
    
    if role not in ["user", "admin"]:
        role = user.role
    
    if email != user.email:
        existing = User.query.filter_by(email=email).first()
        if existing:
            return jsonify({"error": "Email ja cadastrado"}), 400
        user.email = email
    
    user.role = role
    user.active = active
    
    if "password" in data and data["password"]:
        user.password_hash = generate_password_hash(data["password"])
    
    db.session.commit()
    
    return jsonify(user.to_dict())


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    from models import User
    
    if session.get('user_id') == user_id:
        return jsonify({"error": "Voce nao pode excluir sua propria conta"}), 400
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({"message": "Usuario excluido com sucesso"})


@app.route("/api/weeks", methods=["GET"])
@login_required
def get_weeks():
    from models import Schedule
    
    user_id = session['user_id']
    turma_id = request.args.get('turma_id', type=int)
    
    query = Schedule.query.filter_by(user_id=user_id)
    if turma_id:
        query = query.filter_by(turma_id=turma_id)
    
    schedules = query.order_by(Schedule.semana).all()
    return jsonify([s.to_dict() for s in schedules])


@app.route("/api/weeks/<int:week_id>", methods=["GET"])
@login_required
def get_week(week_id):
    from models import Schedule
    
    user_id = session['user_id']
    schedule = Schedule.query.filter_by(user_id=user_id, semana=week_id).first()
    
    if schedule:
        return jsonify(schedule.to_dict())
    return jsonify({"error": "Semana nao encontrada"}), 404


@app.route("/api/weeks", methods=["POST"])
@login_required
def add_week():
    from models import Schedule, Turma
    
    user_id = session['user_id']
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Dados invalidos"}), 400
    
    turma_id = data.get("turma_id")
    if not turma_id:
        return jsonify({"error": "Turma e obrigatoria. Selecione uma turma antes de adicionar semanas."}), 400
    
    turma = Turma.query.filter_by(id=turma_id, user_id=user_id, active=True).first()
    if not turma:
        return jsonify({"error": "Turma nao encontrada"}), 404
    
    max_semana = db.session.query(db.func.max(Schedule.semana)).filter_by(user_id=user_id, turma_id=turma_id).scalar() or 0
    
    schedule = Schedule(
        user_id=user_id,
        turma_id=turma_id,
        semana=data.get("semana", max_semana + 1),
        atividades=data.get("atividades", ""),
        unidade_curricular=data.get("unidadeCurricular", ""),
        capacidades=data.get("capacidades", ""),
        conhecimentos=data.get("conhecimentos", ""),
        recursos=data.get("recursos", "")
    )
    
    db.session.add(schedule)
    db.session.commit()
    
    return jsonify(schedule.to_dict()), 201


@app.route("/api/weeks/<int:week_id>", methods=["PUT"])
@login_required
def update_week(week_id):
    from models import Schedule
    
    user_id = session['user_id']
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Dados invalidos"}), 400
    
    schedule = Schedule.query.filter_by(user_id=user_id, semana=week_id).first()
    
    if not schedule:
        return jsonify({"error": "Semana nao encontrada"}), 404
    
    schedule.atividades = data.get("atividades", schedule.atividades)
    schedule.unidade_curricular = data.get("unidadeCurricular", schedule.unidade_curricular)
    schedule.capacidades = data.get("capacidades", schedule.capacidades)
    schedule.conhecimentos = data.get("conhecimentos", schedule.conhecimentos)
    schedule.recursos = data.get("recursos", schedule.recursos)
    
    db.session.commit()
    
    return jsonify(schedule.to_dict())


@app.route("/api/weeks/<int:week_id>", methods=["DELETE"])
@login_required
def delete_week(week_id):
    from models import Schedule
    
    user_id = session['user_id']
    schedule = Schedule.query.filter_by(user_id=user_id, semana=week_id).first()
    
    if not schedule:
        return jsonify({"error": "Semana nao encontrada"}), 404
    
    db.session.delete(schedule)
    db.session.commit()
    
    return jsonify({"message": "Semana excluida com sucesso"})


@app.route("/api/weeks/<int:week_id>/toggle-complete", methods=["POST"])
@login_required
def toggle_week_complete(week_id):
    from models import Schedule
    
    user_id = session['user_id']
    schedule = Schedule.query.filter_by(user_id=user_id, semana=week_id).first()
    
    if not schedule:
        return jsonify({"error": "Semana nao encontrada"}), 404
    
    schedule.completed = not schedule.completed
    db.session.commit()
    
    return jsonify(schedule.to_dict())


@app.route("/api/migrate")
def run_migration():
    from models import User, Schedule, Turma
    
    try:
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS turmas (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                nome VARCHAR(200) NOT NULL,
                descricao TEXT DEFAULT '',
                cor VARCHAR(20) DEFAULT 'blue',
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        db.session.execute(db.text("ALTER TABLE schedules ADD COLUMN IF NOT EXISTS completed BOOLEAN DEFAULT FALSE;"))
        db.session.execute(db.text("ALTER TABLE schedules ADD COLUMN IF NOT EXISTS turma_id INTEGER REFERENCES turmas(id) ON DELETE SET NULL;"))
        db.session.commit()
        
        users = User.query.all()
        for user in users:
            orphan_schedules = Schedule.query.filter_by(user_id=user.id, turma_id=None).all()
            if orphan_schedules:
                default_turma = Turma.query.filter_by(user_id=user.id).first()
                if not default_turma:
                    default_turma = Turma(
                        user_id=user.id,
                        nome="Tecnico em Programacao de Jogos Digitais",
                        descricao="Turma padrao criada automaticamente",
                        cor="blue",
                        active=True
                    )
                    db.session.add(default_turma)
                    db.session.commit()
                
                for schedule in orphan_schedules:
                    schedule.turma_id = default_turma.id
                db.session.commit()
        
        return jsonify({"success": True, "message": "Migracao executada com sucesso! Schedules orfaos associados a turma padrao."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/export/json")
@login_required
def export_json():
    from models import Schedule
    
    user_id = session['user_id']
    schedules = Schedule.query.filter_by(user_id=user_id).order_by(Schedule.semana).all()
    weeks = [s.to_dict() for s in schedules]
    
    response = Response(
        json.dumps(weeks, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=cronograma.json"}
    )
    return response


@app.route("/api/export/pdf")
@login_required
def export_pdf():
    from models import Schedule
    
    user_id = session['user_id']
    schedules = Schedule.query.filter_by(user_id=user_id).order_by(Schedule.semana).all()
    weeks = [s.to_dict() for s in schedules]
    
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
