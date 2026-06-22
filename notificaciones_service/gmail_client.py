import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from html import unescape

from config import (
    GMAIL_EMAIL,
    GMAIL_APP_PASSWORD,
    GMAIL_SMTP_SERVER,
    GMAIL_SMTP_PORT,
    GMAIL_USE_TLS,
)


class GmailClient:
    """Cliente para envío de correos electrónicos mediante Gmail."""

    def __init__(self, email=None, app_password=None):
        self.email = email or GMAIL_EMAIL
        self.app_password = app_password or GMAIL_APP_PASSWORD
        self.smtp_server = GMAIL_SMTP_SERVER
        self.smtp_port = GMAIL_SMTP_PORT
        self.use_tls = GMAIL_USE_TLS

    @property
    def enabled(self):
        """Verifica si el cliente está configurado correctamente."""
        return bool(self.email and self.app_password)

    def send_email(self, recipient, subject, body, html=False):
        """
        Envía un correo electrónico.

        Args:
            recipient: Email del destinatario
            subject: Asunto del correo
            body: Cuerpo del mensaje
            html: Si True, el cuerpo se interpreta como HTML

        Returns:
            dict: Resultado del envío
        """
        if not self.enabled:
            raise RuntimeError("GMAIL_EMAIL o GMAIL_APP_PASSWORD no están configurados")

        if not recipient:
            raise ValueError("No existe email destinatario para enviar la notificación")

        # Crear el mensaje
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.email
        msg["To"] = recipient

        # Convertir HTML a texto plano si es necesario
        if html:
            text_body = unescape(body).replace("<br>", "\n").replace("<p>", "").replace("</p>", "\n")
            msg.attach(MIMEText(text_body, "plain", "utf-8"))
            msg.attach(MIMEText(body, "html", "utf-8"))
        else:
            msg.attach(MIMEText(body, "plain", "utf-8"))

        # Conectar y enviar
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.email, self.app_password)
            server.sendmail(self.email, recipient, msg.as_string())
            server.quit()
            return {"success": True, "message": "Correo enviado exitosamente"}
        except smtplib.SMTPAuthenticationError as e:
            raise RuntimeError(f"Error de autenticación con Gmail: {str(e)}")
        except smtplib.SMTPException as e:
            raise RuntimeError(f"Error al enviar correo: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error inesperado al enviar correo: {str(e)}")

    def send_notification_email(self, recipient, title, content, event_data=None):
        """
        Envía una notificación formateada por correo electrónico.

        Args:
            recipient: Email del destinatario
            title: Título de la notificación
            content: Contenido de la notificación
            event_data: Datos adicionales del evento (opcional)
        """
        subject = f"Notificación: {title}"
        
        # Crear cuerpo HTML atractivo
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">{title}</h2>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    {content}
                </div>
                {self._build_event_details(event_data) if event_data else ''}
                <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">
                    Este es un mensaje automático del sistema de notificaciones ERP.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(recipient, subject, html_body, html=True)

    @staticmethod
    def _build_event_details(event_data):
        """Construye una tabla con detalles del evento."""
        if not event_data:
            return ""
        
        details = [
            ("Evento", event_data.get("evento")),
            ("Origen", event_data.get("origen")),
            ("Referencia", event_data.get("referencia_uid")),
            ("Cliente", event_data.get("cliente_uid")),
            ("Sucursal", event_data.get("sucursal_uid")),
        ]
        
        html = '<table style="width: 100%; border-collapse: collapse; margin-top: 15px;">'
        for label, value in details:
            if value:
                html += f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">{label}:</td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{value}</td>
                </tr>
                """
        html += "</table>"
        return html
