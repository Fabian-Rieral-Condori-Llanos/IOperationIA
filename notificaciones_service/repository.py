import json
import uuid

from database import row_to_dict


def new_uid(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"


class NotificationRepository:
    def __init__(self, connection_factory):
        self.connection_factory = connection_factory

    def ensure_schema(self):
        with self.connection_factory() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS email_suscriptores(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uid TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    nombre TEXT,
                    cliente_uid TEXT,
                    estado TEXT NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo','inactivo')),
                    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_email_suscriptores_cliente_uid ON email_suscriptores(cliente_uid)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_email_suscriptores_estado ON email_suscriptores(estado)"
            )
            
            conn.commit()

    def upsert_email_subscriber(self, subscriber_data):
        """Inserta o actualiza un suscriptor de email."""
        uid = subscriber_data.get("uid") or new_uid("EMS")
        with self.connection_factory() as conn:
            conn.execute(
                """
                INSERT INTO email_suscriptores (
                    uid, email, nombre, cliente_uid, estado
                )
                VALUES (?, ?, ?, ?, 'activo')
                ON CONFLICT(email) DO UPDATE SET
                    nombre = COALESCE(excluded.nombre, email_suscriptores.nombre),
                    cliente_uid = COALESCE(excluded.cliente_uid, email_suscriptores.cliente_uid),
                    estado = 'activo',
                    actualizado_en = CURRENT_TIMESTAMP
                """,
                (
                    uid,
                    subscriber_data["email"],
                    subscriber_data.get("nombre"),
                    subscriber_data.get("cliente_uid"),
                ),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM email_suscriptores WHERE email = ?",
                (subscriber_data["email"],),
            ).fetchone()
            return row_to_dict(row)

    def get_subscriber_by_cliente_uid(self, cliente_uid):
        """Obtiene un suscriptor por cliente_uid."""
        with self.connection_factory() as conn:
            row = conn.execute(
                """
                SELECT * FROM email_suscriptores
                WHERE cliente_uid = ? AND estado = 'activo'
                ORDER BY actualizado_en DESC
                LIMIT 1
                """,
                (cliente_uid,),
            ).fetchone()
            return row_to_dict(row) if row else None

    def list_email_subscribers(self, only_active=True):
        """Lista todos los suscriptores de email."""
        query = "SELECT * FROM email_suscriptores"
        params = []
        if only_active:
            query += " WHERE estado = ?"
            params.append("activo")
        query += " ORDER BY actualizado_en DESC"
        with self.connection_factory() as conn:
            rows = conn.execute(query, params).fetchall()
            return [row_to_dict(row) for row in rows]

    def find_email_recipient(self, cliente_uid=None, explicit_email=None):
        """Busca un destinatario de email por cliente_uid o email explícito."""
        if explicit_email:
            with self.connection_factory() as conn:
                row = conn.execute(
                    """
                    SELECT * FROM email_suscriptores
                    WHERE email = ? AND estado = 'activo'
                    """,
                    (explicit_email,),
                ).fetchone()
                return [row_to_dict(row)] if row else []

        with self.connection_factory() as conn:
            if cliente_uid:
                rows = conn.execute(
                    """
                    SELECT * FROM email_suscriptores
                    WHERE cliente_uid = ? AND estado = 'activo'
                    ORDER BY actualizado_en DESC
                    """,
                    (cliente_uid,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM email_suscriptores
                    WHERE estado = 'activo'
                    ORDER BY actualizado_en DESC
                    """
                ).fetchall()
        return [row_to_dict(row) for row in rows]

    def create_event(self, event_data):
        payload = event_data.get("payload") or {}
        uid = event_data.get("uid") or new_uid("EVT")

        with self.connection_factory() as conn:
            cursor = conn.execute(
                """
                INSERT INTO eventos (
                    uid, evento, origen, referencia_tipo, referencia_id, referencia_uid,
                    cliente_uid, sucursal_uid, payload
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uid,
                    event_data["evento"],
                    event_data["origen"],
                    event_data.get("referencia_tipo"),
                    event_data.get("referencia_id"),
                    event_data.get("referencia_uid"),
                    event_data.get("cliente_uid") or payload.get("cliente_uid"),
                    event_data.get("sucursal_uid") or payload.get("sucursal_uid"),
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM eventos WHERE id = ?", (cursor.lastrowid,)).fetchone()
            event = row_to_dict(row)
            event["payload"] = json.loads(event["payload"] or "{}")
            return event

    def get_event(self, event_uid):
        with self.connection_factory() as conn:
            row = conn.execute("SELECT * FROM eventos WHERE uid = ?", (event_uid,)).fetchone()
            event = row_to_dict(row)
            if event:
                event["payload"] = json.loads(event["payload"] or "{}")
            return event

    def list_events(self, limit=50):
        with self.connection_factory() as conn:
            rows = conn.execute(
                "SELECT * FROM eventos ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

        events = []
        for row in rows:
            event = row_to_dict(row)
            event["payload"] = json.loads(event["payload"] or "{}")
            events.append(event)
        return events

    def mark_event_processed(self, event_uid):
        with self.connection_factory() as conn:
            conn.execute(
                """
                UPDATE eventos
                SET procesado = 1, estado = 'procesado', procesado_en = CURRENT_TIMESTAMP,
                    mensaje_error = NULL
                WHERE uid = ?
                """,
                (event_uid,),
            )
            conn.commit()

    def mark_event_error(self, event_uid, message):
        with self.connection_factory() as conn:
            conn.execute(
                """
                UPDATE eventos
                SET estado = 'error', intentos = intentos + 1, mensaje_error = ?
                WHERE uid = ?
                """,
                (message, event_uid),
            )
            conn.commit()

    def create_notification(self, event_uid, payload):
        uid = new_uid("NOT")
        with self.connection_factory() as conn:
            cursor = conn.execute(
                """
                INSERT INTO notificaciones (
                    uid, evento_uid, cliente_uid, sucursal_uid, tipo, destinatario,
                    titulo, contenido, estado
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uid,
                    event_uid,
                    payload.get("cliente_uid"),
                    payload.get("sucursal_uid"),
                    payload["tipo"],
                    payload.get("destinatario"),
                    payload.get("titulo"),
                    payload["contenido"],
                    payload.get("estado", "generada"),
                ),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM notificaciones WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return row_to_dict(row)

    def update_notification_status(self, notification_uid, status, error_message=None):
        with self.connection_factory() as conn:
            conn.execute(
                """
                UPDATE notificaciones
                SET estado = ?, enviado_en = CASE WHEN ? = 'enviada' THEN CURRENT_TIMESTAMP ELSE enviado_en END,
                    mensaje_error = ?
                WHERE uid = ?
                """,
                (status, status, error_message, notification_uid),
            )
            conn.commit()

    def list_notifications(self, limit=50):
        with self.connection_factory() as conn:
            rows = conn.execute(
                "SELECT * FROM notificaciones ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [row_to_dict(row) for row in rows]

    def log(self, action, status, message=None, reference_type=None, reference_uid=None):
        with self.connection_factory() as conn:
            conn.execute(
                """
                INSERT INTO logs (uid, servicio, accion, estado, mensaje, referencia_tipo, referencia_uid)
                VALUES (?, 'notificaciones_service', ?, ?, ?, ?, ?)
                """,
                (new_uid("LOG"), action, status, message, reference_type, reference_uid),
            )
            conn.commit()
