from app import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')
    cargo = db.Column(db.String(100), default='')
    photo = db.Column(db.String(255), default='')
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
            'cargo': self.cargo,
            'photo': self.photo,
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
    carga_horaria = db.Column(db.Integer, default=0)
    dias_aula = db.Column(db.String(100), default='')
    horario_inicio = db.Column(db.String(10), default='')
    horario_fim = db.Column(db.String(10), default='')
    data_inicio = db.Column(db.Date, nullable=True)
    data_fim = db.Column(db.Date, nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    schedules = db.relationship('Schedule', backref='turma', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        schedule_count = len([s for s in self.schedules if s]) if self.schedules else 0
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'cor': self.cor,
            'carga_horaria': self.carga_horaria,
            'dias_aula': self.dias_aula,
            'horario_inicio': self.horario_inicio,
            'horario_fim': self.horario_fim,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
            'active': self.active,
            'schedule_count': schedule_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turmas.id', ondelete='CASCADE'), nullable=False)
    semana = db.Column(db.Integer, nullable=False)
    atividades = db.Column(db.Text, default='')
    unidade_curricular = db.Column(db.String(200), default='')
    capacidades = db.Column(db.Text, default='')
    conhecimentos = db.Column(db.Text, default='')
    recursos = db.Column(db.String(500), default='')
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'turma_id': self.turma_id,
            'turma_nome': self.turma.nome if self.turma else None,
            'turma_cor': self.turma.cor if self.turma else None,
            'semana': self.semana,
            'atividades': self.atividades,
            'unidadeCurricular': self.unidade_curricular,
            'capacidades': self.capacidades,
            'conhecimentos': self.conhecimentos,
            'recursos': self.recursos,
            'completed': self.completed
        }
