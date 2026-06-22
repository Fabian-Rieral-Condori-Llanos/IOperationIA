import os


SERVICE_NAME = "Notificaciones"
SERVICE_PORT = int(os.getenv("NOTIFICACIONES_PORT", "5005"))

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.getenv(
    "NOTIFICACIONES_DB_PATH",
    os.path.abspath(os.path.join(BASE_DIR, "..", "database", "notificaciones.db")),
)

# Configuración de Gmail para envío de notificaciones
# Credenciales hardcodeadas - usar correo real y contraseña de aplicación
GMAIL_EMAIL = "tu_email@gmail.com"  # Reemplazar con el email real de Gmail
GMAIL_APP_PASSWORD = "hmln jmpo yqol fwwc"  # Contraseña de aplicación generada en Google
GMAIL_SMTP_SERVER = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587
GMAIL_USE_TLS = True
