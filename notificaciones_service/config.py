import os


def load_local_env():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()

SERVICE_NAME = "Notificaciones"
SERVICE_PORT = int(os.getenv("NOTIFICACIONES_PORT", "5005"))

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.getenv(
    "NOTIFICACIONES_DB_PATH",
    os.path.abspath(os.path.join(BASE_DIR, "..", "database", "notificaciones.db")),
)

# Configuración de Gmail para envío de notificaciones
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()
GMAIL_SMTP_SERVER = os.getenv("GMAIL_SMTP_SERVER", "smtp.gmail.com")
GMAIL_SMTP_PORT = int(os.getenv("GMAIL_SMTP_PORT", "587"))
GMAIL_USE_TLS = os.getenv("GMAIL_USE_TLS", "true").lower() == "true"
