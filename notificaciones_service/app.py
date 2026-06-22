import os
import threading
import time

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import (
    SERVICE_NAME,
    SERVICE_PORT,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_POLLING_ENABLED,
    TELEGRAM_POLLING_INTERVAL_SECONDS,
)
from database import get_connection
from repository import NotificationRepository
from services import NotificationService
from telegram_client import TelegramClient
from validators import validate_text

app = Flask(__name__)
CORS(app)

repository = NotificationRepository(get_connection)
repository.ensure_schema()
notification_service = NotificationService(repository, TelegramClient(TELEGRAM_BOT_TOKEN))


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


@app.route("/api/telegram/suscriptores", methods=["GET"])
def list_telegram_subscribers():
    return jsonify({"status": "success", "data": repository.list_telegram_subscribers()}), 200


@app.route("/api/telegram/sincronizar", methods=["POST"])
def sync_telegram_subscribers():
    try:
        result = notification_service.sync_telegram_subscribers()
        return jsonify({"status": "success", "data": result}), 200
    except Exception as exc:
        return json_error(str(exc), 500)


def start_telegram_polling():
    if not TELEGRAM_POLLING_ENABLED or not TELEGRAM_BOT_TOKEN:
        return

    def polling_loop():
        while True:
            try:
                notification_service.sync_telegram_subscribers()
            except Exception as exc:
                repository.log("telegram_polling", "error", str(exc), "telegram", None)
            time.sleep(TELEGRAM_POLLING_INTERVAL_SECONDS)

    thread = threading.Thread(target=polling_loop, daemon=True)
    thread.start()


if __name__ == "__main__":
    debug = True
    if not debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_telegram_polling()
    app.run(debug=debug, port=SERVICE_PORT)
