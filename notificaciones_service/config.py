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

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_API_BASE_URL = os.getenv("TELEGRAM_API_BASE_URL", "https://api.telegram.org").rstrip("/")
TELEGRAM_TIMEOUT_SECONDS = int(os.getenv("TELEGRAM_TIMEOUT_SECONDS", "12"))
TELEGRAM_POLLING_ENABLED = os.getenv("TELEGRAM_POLLING_ENABLED", "true").lower() == "true"
TELEGRAM_POLLING_INTERVAL_SECONDS = int(os.getenv("TELEGRAM_POLLING_INTERVAL_SECONDS", "8"))
