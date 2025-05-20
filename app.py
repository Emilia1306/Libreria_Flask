from flask import (
    Flask, render_template, redirect, url_for,
    flash, request
)
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from datetime import datetime
import os

from models import db, Usuario, Libro, Lectura
from config import Config
from forms import RegistroForm, LoginForm

app = Flask(__name__)
app.config.from_object(Config)

# ── extensiones ──────────────────────────────────────────────────────────
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# carpeta para portadas
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ── util ─────────────────────────────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )

# ── rutas ────────────────────────────────────────────────────────────────
@app.route("/")
@login_required
def index():
    libros = Libro.query.filter_by(usuario_id=current_user.id).all()
    return render_template("index.html", libros=libros)

# ----------  Libros  -----------------------------------------------------
@app.route("/agregar_libro", methods=["GET", "POST"])
@login_required
def agregar_libro():
    if request.method == "POST":
        titulo  = request.form["titulo"]
        autor   = request.form["autor"]
        genero  = request.form["genero"]
        portada = request.files.get("portada")

        if not titulo or not autor:
            flash("El título y el autor son obligatorios.")
            return redirect(request.url)

        filename = None
        if portada and allowed_file(portada.filename):
            filename = secure_filename(portada.filename)
            portada.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        elif portada and portada.filename:
            flash("Formato de archivo no permitido para la portada.")
            return redirect(request.url)

        db.session.add(
            Libro(
                titulo=titulo,
                autor=autor,
                genero=genero,
                portada=filename,
                usuario_id=current_user.id,
            )
        )
        db.session.commit()
        flash("Libro agregado correctamente.")
        return redirect(url_for("index"))

    return render_template("agregar_libro.html")

@app.route("/detalle_libro/<int:libro_id>")
@login_required
def detalle_libro(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    if libro.usuario_id != current_user.id:
        flash("No tienes acceso a este libro.")
        return redirect(url_for("index"))

    lecturas = (
        Lectura.query
        .filter_by(libro_id=libro.id, usuario_id=current_user.id)
        .order_by(Lectura.fecha_inicio.desc())
        .all()
    )
    return render_template(
        "detalle_libro.html",
        libro=libro,
        lecturas=lecturas
    )

@app.route("/editar_libro/<int:libro_id>", methods=["GET", "POST"])
@login_required
def editar_libro(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    if libro.usuario_id != current_user.id:
        flash("No tienes permiso para editar este libro.")
        return redirect(url_for("index"))

    if request.method == "POST":
        libro.titulo = request.form["titulo"]
        libro.autor  = request.form["autor"]
        libro.genero = request.form["genero"]

        portada = request.files.get("portada")
        if portada and allowed_file(portada.filename):
            filename = secure_filename(portada.filename)
            portada.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            libro.portada = filename

        db.session.commit()
        flash("Libro actualizado.")
        return redirect(url_for("detalle_libro", libro_id=libro.id))

    return render_template("editar_libro.html", libro=libro)

@app.route("/eliminar_libro/<int:libro_id>", methods=["POST"])
@login_required
def eliminar_libro(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    if libro.usuario_id != current_user.id:
        flash("No tienes permiso para eliminar este libro.")
        return redirect(url_for("index"))

    db.session.delete(libro)
    db.session.commit()
    flash("Libro eliminado.")
    return redirect(url_for("index"))

# ----------  Lecturas  ---------------------------------------------------
@app.route("/agregar_lectura/<int:libro_id>", methods=["POST"])
@login_required
def agregar_lectura(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    if libro.usuario_id != current_user.id:
        flash("No puedes agregar lecturas a un libro ajeno.")
        return redirect(url_for("index"))

    fecha_inicio = request.form["fecha_inicio"]
    fecha_fin    = request.form.get("fecha_fin")  # opcional
    comentario   = request.form["comentario"]

    nueva_lectura = Lectura(
        fecha_inicio=datetime.strptime(fecha_inicio, "%Y-%m-%d"),
        fecha_fin=datetime.strptime(fecha_fin, "%Y-%m-%d") if fecha_fin else None,
        comentario=comentario,
        usuario_id=current_user.id,
        libro_id=libro.id,
    )
    db.session.add(nueva_lectura)
    db.session.commit()
    flash("Lectura registrada.")
    return redirect(url_for("detalle_libro", libro_id=libro.id))

# ----------  Autenticación  ---------------------------------------------
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegistroForm()
    if form.validate_on_submit():
        db.session.add(
            Usuario(
                nombre=form.nombre.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data),
            )
        )
        db.session.commit()
        flash("Registro exitoso. Ahora puedes iniciar sesión.")
        return redirect(url_for("login"))
    return render_template("registro.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        if usuario and check_password_hash(usuario.password, form.password.data):
            login_user(usuario)
            return redirect(request.args.get("next") or url_for("index"))
        flash("Email o contraseña incorrectos.")
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión.")
    return redirect(url_for("login"))

# ── main ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
