from flask import Flask, jsonify, request
from flask_cors import CORS

from config import (
    SERVICE_NAME,
    SERVICE_PORT,
    GMAIL_EMAIL,
    GMAIL_APP_PASSWORD,
)
from database import get_connection
from repository import NotificationRepository
from services import NotificationService
from gmail_client import GmailClient
from validators import validate_text

app = Flask(__name__)
CORS(app)

repository = NotificationRepository(get_connection)
repository.ensure_schema()

# Inicializar cliente de Gmail para envío de notificaciones
gmail_client = GmailClient(GMAIL_EMAIL, GMAIL_APP_PASSWORD) if GMAIL_EMAIL and GMAIL_APP_PASSWORD else None

notification_service = NotificationService(
    repository,
    gmail_client=gmail_client
)


def json_error(message, status=400):
    return jsonify({"status": "error", "message": message}), status


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "success", "message": f"{SERVICE_NAME} OK en puerto {SERVICE_PORT}"}), 200


@app.route("/api/eventos/publicar", methods=["POST"])
def publish_event():
    try:
        data = request.get_json(silent=True) or {}
        event_data = {
            "uid": validate_text(data, "uid", required=False),
            "evento": validate_text(data, "evento"),
            "origen": validate_text(data, "origen"),
            "referencia_tipo": validate_text(data, "referencia_tipo", required=False),
            "referencia_id": data.get("referencia_id"),
            "referencia_uid": validate_text(data, "referencia_uid", required=False),
            "cliente_uid": validate_text(data, "cliente_uid", required=False),
            "sucursal_uid": validate_text(data, "sucursal_uid", required=False),
            "payload": data.get("payload") or {},
        }
        result = notification_service.publish_event(event_data)
        status_code = 201 if result["delivered"] else 202
        return jsonify({"status": "success", "data": result}), status_code
    except ValueError as exc:
        return json_error(str(exc), 400)
    except Exception as exc:
        return json_error(str(exc), 500)


@app.route("/api/eventos", methods=["GET"])
def list_events():
    limit = request.args.get("limit", default=50, type=int)
    limit = max(1, min(limit, 200))
    return jsonify({"status": "success", "data": repository.list_events(limit)}), 200


@app.route("/api/eventos/<event_uid>", methods=["GET"])
def get_event(event_uid):
    event = repository.get_event(event_uid)
    if not event:
        return json_error("Evento no encontrado", 404)
    return jsonify({"status": "success", "data": event}), 200


@app.route("/api/eventos/<event_uid>/reintentar", methods=["POST"])
def retry_event(event_uid):
    try:
        result = notification_service.retry_event(event_uid)
        status_code = 200 if result["delivered"] else 202
        return jsonify({"status": "success", "data": result}), status_code
    except ValueError as exc:
        return json_error(str(exc), 404)
    except Exception as exc:
        return json_error(str(exc), 500)


@app.route("/api/notificaciones", methods=["GET"])
def list_notifications():
    limit = request.args.get("limit", default=50, type=int)
    limit = max(1, min(limit, 200))
    return jsonify({"status": "success", "data": repository.list_notifications(limit)}), 200


@app.route("/api/email/suscriptores", methods=["GET"])
def list_email_subscribers():
    """Lista todos los suscriptores de email."""
    return jsonify({"status": "success", "data": repository.list_email_subscribers()}), 200


@app.route("/api/email/suscriptores", methods=["POST"])
def create_email_subscriber():
    """Registra un nuevo suscriptor de email."""
    try:
        data = request.get_json(silent=True) or {}
        subscriber_data = {
            "email": validate_text(data, "email"),
            "nombre": validate_text(data, "nombre", required=False),
            "cliente_uid": validate_text(data, "cliente_uid", required=False),
        }
        subscriber = repository.upsert_email_subscriber(subscriber_data)
        return jsonify({"status": "success", "data": subscriber}), 201
    except ValueError as exc:
        return json_error(str(exc), 400)
    except Exception as exc:
        return json_error(str(exc), 500)


@app.route("/api/email/probar", methods=["POST"])
def test_email():
    """Endpoint para probar el envío de correos electrónicos."""
    try:
        data = request.get_json(silent=True) or {}
        recipient = data.get("email") or GMAIL_EMAIL
        
        if not recipient:
            return json_error("Debe proporcionar un email destinatario", 400)
        
        if not gmail_client or not gmail_client.enabled:
            return json_error("Cliente de Gmail no está configurado", 503)
        
        result = gmail_client.send_notification_email(
            recipient=recipient,
            title="Prueba de Notificación",
            content="Este es un mensaje de prueba del servicio de notificaciones por email.",
            event_data={"evento": "PRUEBA", "origen": "api_test"}
        )
        
        return jsonify({"status": "success", "data": result}), 200
    except Exception as exc:
        return json_error(str(exc), 500)


if __name__ == "__main__":
    debug = True
    app.run(debug=debug, port=SERVICE_PORT)
