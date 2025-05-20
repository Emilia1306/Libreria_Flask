from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

    libros = db.relationship('Libro', back_populates='usuario', cascade='all, delete-orphan')
    lecturas = db.relationship('Lectura', back_populates='usuario', cascade='all, delete-orphan')


class Libro(db.Model):
    __tablename__ = 'libros'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    genero = db.Column(db.String(50))
    portada = db.Column(db.String(200))  # nombre archivo portada

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    usuario = db.relationship('Usuario', back_populates='libros')
    lecturas = db.relationship('Lectura', back_populates='libro', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Libro {self.titulo}>'


class Lectura(db.Model):
    __tablename__ = 'lecturas'
    id = db.Column(db.Integer, primary_key=True)
    fecha_inicio = db.Column(db.Date, nullable=True)
    fecha_fin = db.Column(db.Date, nullable=True)
    comentario = db.Column(db.Text, nullable=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey('libros.id'), nullable=False)

    usuario = db.relationship('Usuario', back_populates='lecturas')
    libro = db.relationship('Libro', back_populates='lecturas')

    def __repr__(self):
        return f'<Lectura Usuario:{self.usuario_id} Libro:{self.libro_id}>'
