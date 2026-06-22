import os
import re
import sqlite3
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

SERVICE_PORT = 5006
SERVICE_NAME = "Administracion"
DATABASE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "database", "administracion.db")
)
NOTIFICACIONES_URL = "http://127.0.0.1:5005/api/eventos/publicar"
HTML_PATTERN = re.compile(r"<[^>]+>")


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row):
    return dict(row) if row else None


def json_error(message, status=400):
    return jsonify({"status": "error", "message": message}), status


def validate_text(data, field, required=True):
    value = data.get(field)
    if value is None:
        if required:
            raise ValueError(f"El campo '{field}' es obligatorio")
        return None

    value = str(value).strip()
    if required and not value:
        raise ValueError(f"El campo '{field}' no puede estar vacio")
    if value and HTML_PATTERN.search(value):
        raise ValueError(f"El campo '{field}' no puede contener HTML")
    return value if value else None


def validate_estado(value, allowed, field="estado"):
    value = str(value or "").strip().lower()
    if value not in allowed:
        raise ValueError(f"El campo '{field}' debe ser: {', '.join(allowed)}")
    return value


def generate_uid(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def publish_event(evento, payload):
    event_data = {
        "evento": evento,
        "origen": "administracion_service",
        "payload": payload,
    }
    try:
        requests.post(NOTIFICACIONES_URL, json=event_data, timeout=2)
    except requests.RequestException:
        pass


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "success", "message": f"{SERVICE_NAME} OK en puerto {SERVICE_PORT}"}), 200


@app.route("/api/sucursales", methods=["GET"])
@app.route("/api/sucursal", methods=["GET"])
def get_sucursales():
    try:
        with get_db_connection() as conn:
            rows = conn.execute("SELECT * FROM sucursales ORDER BY id DESC").fetchall()
        return jsonify({"status": "success", "data": [row_to_dict(row) for row in rows]}), 200
    except Exception as e:
        return json_error(str(e), 500)


@app.route("/api/sucursales/<int:sucursal_id>", methods=["GET"])
def get_sucursal(sucursal_id):
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM sucursales WHERE id = ?", (sucursal_id,)).fetchone()
        if not row:
            return json_error("Sucursal no encontrada", 404)
        return jsonify({"status": "success", "data": row_to_dict(row)}), 200
    except Exception as e:
        return json_error(str(e), 500)


@app.route("/api/sucursales", methods=["POST"])
@app.route("/api/sucursal", methods=["POST"])
def create_sucursal():
    try:
        data = request.get_json(silent=True) or {}
        uid = validate_text(data, "uid", required=False) or generate_uid("SUC")
        nombre = validate_text(data, "nombre")
        direccion = validate_text(data, "direccion", required=False)
        ciudad = validate_text(data, "ciudad", required=False)
        estado = validate_estado(data.get("estado", "activa"), ["activa", "inactiva"])

        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO sucursales (uid, nombre, direccion, ciudad, estado)
                VALUES (?, ?, ?, ?, ?)
                """,
                (uid, nombre, direccion, ciudad, estado),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM sucursales WHERE id = ?", (cursor.lastrowid,)).fetchone()

        sucursal = row_to_dict(row)
        publish_event("SUCURSAL_CREADA", {"uid": sucursal["uid"], "nombre": sucursal["nombre"]})
        return jsonify({"status": "success", "data": sucursal}), 201
    except ValueError as e:
        return json_error(str(e), 400)
    except sqlite3.IntegrityError as e:
        return json_error(f"No se pudo crear la sucursal: {e}", 400)
    except Exception as e:
        return json_error(str(e), 500)


@app.route("/api/sucursales/<int:sucursal_id>", methods=["PUT"])
def update_sucursal(sucursal_id):
    try:
        data = request.get_json(silent=True) or {}
        nombre = validate_text(data, "nombre")
        direccion = validate_text(data, "direccion", required=False)
        ciudad = validate_text(data, "ciudad", required=False)
        estado = validate_estado(data.get("estado", "activa"), ["activa", "inactiva"])

        with get_db_connection() as conn:
            exists = conn.execute("SELECT id FROM sucursales WHERE id = ?", (sucursal_id,)).fetchone()
            if not exists:
                return json_error("Sucursal no encontrada", 404)

            conn.execute(
                """
                UPDATE sucursales
                SET nombre = ?, direccion = ?, ciudad = ?, estado = ?, actualizado_en = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (nombre, direccion, ciudad, estado, sucursal_id),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM sucursales WHERE id = ?", (sucursal_id,)).fetchone()

        sucursal = row_to_dict(row)
        publish_event("SUCURSAL_ACTUALIZADA", {"uid": sucursal["uid"], "nombre": sucursal["nombre"]})
        return jsonify({"status": "success", "data": sucursal}), 200
    except ValueError as e:
        return json_error(str(e), 400)
    except Exception as e:
        return json_error(str(e), 500)


@app.route("/api/sucursales/<int:sucursal_id>", methods=["DELETE"])
def delete_sucursal(sucursal_id):
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM sucursales WHERE id = ?", (sucursal_id,)).fetchone()
            if not row:
                return json_error("Sucursal no encontrada", 404)

            empleados = conn.execute(
                "SELECT COUNT(*) AS total FROM empleados WHERE sucursal_id = ?", (sucursal_id,)
            ).fetchone()["total"]
            if empleados > 0:
                return json_error("No se puede eliminar una sucursal con empleados asignados", 400)

            conn.execute("DELETE FROM sucursales WHERE id = ?", (sucursal_id,))
            conn.commit()

        sucursal = row_to_dict(row)
        publish_event("SUCURSAL_ELIMINADA", {"uid": sucursal["uid"], "nombre": sucursal["nombre"]})
        return jsonify({"status": "success", "message": "Sucursal eliminada"}), 200
    except Exception as e:
        return json_error(str(e), 500)


@app.route("/api/empleados", methods=["GET"])
def get_empleados():
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT e.*, s.nombre AS sucursal_nombre
                FROM empleados e
                LEFT JOIN sucursales s ON s.id = e.sucursal_id
                ORDER BY e.id DESC
                """
            ).fetchall()
        return jsonify({"status": "success", "data": [row_to_dict(row) for row in rows]}), 200
    except Exception as e:
        return json_error(str(e), 500)


@app.route("/api/empleados/<int:empleado_id>", methods=["GET"])
def get_empleado(empleado_id):
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT e.*, s.nombre AS sucursal_nombre
                FROM empleados e
                LEFT JOIN sucursales s ON s.id = e.sucursal_id
                WHERE e.id = ?
                """,
                (empleado_id,),
            ).fetchone()
        if not row:
            return json_error("Empleado no encontrado", 404)
        return jsonify({"status": "success", "data": row_to_dict(row)}), 200
    except Exception as e:
        return json_error(str(e), 500)


def get_sucursal_for_employee(conn, sucursal_id):
    try:
        sucursal_id = int(sucursal_id)
    except (TypeError, ValueError):
        raise ValueError("El campo 'sucursal_id' es obligatorio")

    sucursal = conn.execute("SELECT * FROM sucursales WHERE id = ?", (sucursal_id,)).fetchone()
    if not sucursal:
        raise ValueError("La sucursal seleccionada no existe")
    return sucursal


@app.route("/api/empleados", methods=["POST"])
def create_empleado():
    try:
        data = request.get_json(silent=True) or {}
        uid = validate_text(data, "uid", required=False) or generate_uid("EMP")
        nombre = validate_text(data, "nombre")
        cargo = validate_text(data, "cargo")
        telefono = validate_text(data, "telefono", required=False)
        estado = validate_estado(data.get("estado", "activo"), ["activo", "inactivo"])

        with get_db_connection() as conn:
            sucursal = get_sucursal_for_employee(conn, data.get("sucursal_id"))
            cursor = conn.execute(
                """
                INSERT INTO empleados (uid, sucursal_id, sucursal_uid, nombre, cargo, telefono, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (uid, sucursal["id"], sucursal["uid"], nombre, cargo, telefono, estado),
            )
            conn.commit()
            row = conn.execute(
                """
                SELECT e.*, s.nombre AS sucursal_nombre
                FROM empleados e
                LEFT JOIN sucursales s ON s.id = e.sucursal_id
                WHERE e.id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()

        empleado = row_to_dict(row)
        publish_event("EMPLEADO_CREADO", {"uid": empleado["uid"], "nombre": empleado["nombre"]})
        return jsonify({"status": "success", "data": empleado}), 201
    except ValueError as e:
        return json_error(str(e), 400)
    except sqlite3.IntegrityError as e:
        return json_error(f"No se pudo crear el empleado: {e}", 400)
    except Exception as e:
        return json_error(str(e), 500)


@app.route("/api/empleados/<int:empleado_id>", methods=["PUT"])
def update_empleado(empleado_id):
    try:
        data = request.get_json(silent=True) or {}
        nombre = validate_text(data, "nombre")
        cargo = validate_text(data, "cargo")
        telefono = validate_text(data, "telefono", required=False)
        estado = validate_estado(data.get("estado", "activo"), ["activo", "inactivo"])

        with get_db_connection() as conn:
            exists = conn.execute("SELECT id FROM empleados WHERE id = ?", (empleado_id,)).fetchone()
            if not exists:
                return json_error("Empleado no encontrado", 404)

            sucursal = get_sucursal_for_employee(conn, data.get("sucursal_id"))
            conn.execute(
                """
                UPDATE empleados
                SET sucursal_id = ?, sucursal_uid = ?, nombre = ?, cargo = ?, telefono = ?,
                    estado = ?, actualizado_en = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (sucursal["id"], sucursal["uid"], nombre, cargo, telefono, estado, empleado_id),
            )
            conn.commit()
            row = conn.execute(
                """
                SELECT e.*, s.nombre AS sucursal_nombre
                FROM empleados e
                LEFT JOIN sucursales s ON s.id = e.sucursal_id
                WHERE e.id = ?
                """,
                (empleado_id,),
            ).fetchone()

        empleado = row_to_dict(row)
        publish_event("EMPLEADO_ACTUALIZADO", {"uid": empleado["uid"], "nombre": empleado["nombre"]})
        return jsonify({"status": "success", "data": empleado}), 200
    except ValueError as e:
        return json_error(str(e), 400)
    except Exception as e:
        return json_error(str(e), 500)


@app.route("/api/empleados/<int:empleado_id>", methods=["DELETE"])
def delete_empleado(empleado_id):
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM empleados WHERE id = ?", (empleado_id,)).fetchone()
            if not row:
                return json_error("Empleado no encontrado", 404)

            conn.execute("DELETE FROM empleados WHERE id = ?", (empleado_id,))
            conn.commit()

        empleado = row_to_dict(row)
        publish_event("EMPLEADO_ELIMINADO", {"uid": empleado["uid"], "nombre": empleado["nombre"]})
        return jsonify({"status": "success", "message": "Empleado eliminado"}), 200
    except Exception as e:
        return json_error(str(e), 500)


if __name__ == "__main__":
    app.run(debug=True, port=SERVICE_PORT)
