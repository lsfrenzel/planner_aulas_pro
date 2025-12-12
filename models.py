from app import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    schedules = db.relationship('Schedule', backref='user', lazy=True, cascade='all, delete-orphan')
    turmas = db.relationship('Turma', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Turma(db.Model):
    __tablename__ = 'turmas'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, default='')
    cor = db.Column(db.String(20), default='blue')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'cor': self.cor,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    turma_id = db.Column(db.Integer, nullable=True)
    semana = db.Column(db.Integer, nullable=False)
    atividades = db.Column(db.Text, default='')
    unidade_curricular = db.Column(db.String(200), default='')
    capacidades = db.Column(db.Text, default='')
    conhecimentos = db.Column(db.Text, default='')
    recursos = db.Column(db.String(500), default='')
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        turma_nome = None
        if self.turma_id:
            try:
                turma = Turma.query.get(self.turma_id)
                if turma:
                    turma_nome = turma.nome
            except Exception:
                pass
        return {
            'id': self.id,
            'turma_id': self.turma_id,
            'turma_nome': turma_nome,
            'semana': self.semana,
            'atividades': self.atividades,
            'unidadeCurricular': self.unidade_curricular,
            'capacidades': self.capacidades,
            'conhecimentos': self.conhecimentos,
            'recursos': self.recursos,
            'completed': self.completed
        }
