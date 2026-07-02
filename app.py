import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash

load_dotenv()

app = Flask(__name__)
app.secret_key = "clave_secreta_para_mensajes"


def get_connection():
    """Crea una conexión a PostgreSQL usando variables de entorno."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "123456"),
        cursor_factory=RealDictCursor,
    )


@app.route("/")
def index():
    orden = request.args.get("orden", "apellido")

    columnas_validas = {
        "apellido": "apellido",
        "carrera": "carrera",
        "fecha_registro": "fecha_registro"
    }

    orden_sql = columnas_validas.get(orden, "apellido")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM estudiantes ORDER BY {orden_sql} ASC"
            )
            estudiantes = cur.fetchall()

    return render_template("index.html", estudiantes=estudiantes)


@app.route("/agregar", methods=["GET", "POST"])
def agregar():
    if request.method == "POST":
        dni = request.form.get("dni", "").strip()
        apellido = request.form.get("apellido", "").strip()
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        carrera = request.form.get("carrera", "").strip()
        telefono = request.form.get("telefono", "").strip()
        edad = request.form.get("edad", "").strip()

        # ---- Validación de campos obligatorios-------
        if not dni or not apellido or not nombre:
            flash("DNI, apellido y nombre son obligatorios.", "error")
            return redirect(url_for("agregar"))
        if not dni.isdigit():
            flash ("El DNI debe contener solo números", "error")
            return redirect(url_for("agregar"))
        
        # -------Validación longitud DNI-------
        if len(dni) < 7 and len(dni) > 8:
            flash("El DNI debe contener entre 7 y 8 dígitos.", "error")
            return redirect(url_for("agregar"))
        # -----------Validación e-mail ---------
        if email and ("@" not in email or "." not in email):
            flash("Ingrese un email válido.", "error")
            return redirect(url_for("agregar"))
        

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO estudiantes (dni, apellido, nombre, email, carrera,telefono, edad)
                        VALUES (%s, %s, %s, %s, %s,%s,%s)
                        """,
                        (dni, apellido, nombre, email, carrera, telefono, edad),
                    )
                conn.commit()
            flash("Estudiante agregado correctamente.", "success")
            return redirect(url_for("index"))
        except psycopg2.errors.UniqueViolation:
            flash("Ya existe un estudiante con ese DNI.", "error")
            return redirect(url_for("agregar"))
        except Exception as e:
            flash(f"Error al agregar estudiante: {e}", "error")
            return redirect(url_for("agregar"))

    return render_template("agregar.html")


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if request.method == "POST":
        dni = request.form.get("dni", "").strip()
        apellido = request.form.get("apellido", "").strip()
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        carrera = request.form.get("carrera", "").strip()

        if not dni or not apellido or not nombre:
            flash("DNI, apellido y nombre son obligatorios.", "error")
            return redirect(url_for("editar", id=id))

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE estudiantes
                        SET dni=%s, apellido=%s, nombre=%s, email=%s, carrera=%s
                        WHERE id=%s
                        """,
                        (dni, apellido, nombre, email, carrera, id),
                    )
                conn.commit()
            flash("Estudiante actualizado correctamente.", "success")
            return redirect(url_for("index"))
        except Exception as e:
            flash(f"Error al actualizar estudiante: {e}", "error")
            return redirect(url_for("editar", id=id))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM estudiantes WHERE id = %s", (id,))
            estudiante = cur.fetchone()

    if not estudiante:
        flash("No se encontró el estudiante solicitado.", "error")
        return redirect(url_for("index"))

    return render_template("editar.html", estudiante=estudiante)


@app.route("/eliminar/<int:id>")
def eliminar(id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM estudiantes WHERE id = %s", (id,))
        conn.commit()
    flash("Estudiante eliminado correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/buscar", methods=["POST"])
def buscar():
    texto = request.form.get("buscar", "").strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM estudiantes
                WHERE dni ILIKE %s
                    OR apellido ILIKE %s
                    OR nombre ILIKE %s
                    OR carrera ILIKE %s
                ORDER BY id ASC
                """,
                (
                    f"%{texto}%",
                    f"%{texto}%",
                    f"%{texto}%",
                    f"%{texto}%"
                )
            )
            estudiantes = cur.fetchall()

    return render_template("index.html", estudiantes=estudiantes, busqueda=texto)
# --------Ruta About------
@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)




