from html import escape


class NotificationService:
    def __init__(self, repository, telegram_client):
        self.repository = repository
        self.telegram_client = telegram_client

    def publish_event(self, event_data):
        event = self.repository.create_event(event_data)
        return self._process_event(event)

    def retry_event(self, event_uid):
        event = self.repository.get_event(event_uid)
        if not event:
            raise ValueError("Evento no encontrado")
        return self._process_event(event)

    def _process_event(self, event):
        try:
            notifications = self._create_notifications_for_event(event)
            for notification in notifications:
                self._deliver_telegram_notification(event, notification)
            self.repository.mark_event_processed(event["uid"])
            self.repository.log("publicar_evento", "exitoso", "Evento procesado", "evento", event["uid"])
            return {"event": event, "notifications": notifications, "delivered": True}
        except Exception as exc:
            self.repository.mark_event_error(event["uid"], str(exc))
            self.repository.log("publicar_evento", "error", str(exc), "evento", event["uid"])
            return {"event": event, "notifications": [], "delivered": False, "error": str(exc)}

    def sync_telegram_subscribers(self):
        last_update_id = self.repository.get_state("telegram_last_update_id")
        offset = int(last_update_id) + 1 if last_update_id else None
        updates = self.telegram_client.get_updates(offset=offset)

        subscribers = []
        max_update_id = int(last_update_id) if last_update_id else None
        for update in updates:
            update_id = update.get("update_id")
            if update_id is not None:
                max_update_id = max(max_update_id or update_id, update_id)

            message = update.get("message") or {}
            text = str(message.get("text") or "").strip()
            if not text.startswith("/start"):
                continue

            chat = message.get("chat") or {}
            user = message.get("from") or {}
            cliente_uid = parse_start_parameter(text)
            subscriber = self.repository.upsert_telegram_subscriber(
                {
                    "telegram_user_id": user.get("id") or chat.get("id"),
                    "telegram_chat_id": chat.get("id"),
                    "username": user.get("username") or chat.get("username"),
                    "first_name": user.get("first_name") or chat.get("first_name"),
                    "last_name": user.get("last_name") or chat.get("last_name"),
                    "cliente_uid": cliente_uid,
                    "ultimo_update_id": update_id,
                }
            )
            subscribers.append(subscriber)

            welcome = "Registro completado. Ya puedes recibir notificaciones del ERP."
            if cliente_uid:
                welcome += f"\nCliente vinculado: {escape(cliente_uid)}"
            self.telegram_client.send_message(chat.get("id"), welcome)

        if max_update_id is not None:
            self.repository.set_state("telegram_last_update_id", max_update_id)

        return {"updates": len(updates), "subscribers": subscribers}

    def _create_notifications_for_event(self, event):
        payload = self._payload_from_event(event)
        content = build_message(event["evento"], payload)
        explicit_chat_id = payload.get("telegram_chat_id") or payload.get("chat_id")
        cliente_uid = event.get("cliente_uid") or payload.get("cliente_uid")
        recipients = self.repository.find_telegram_recipients(
            cliente_uid=cliente_uid,
            explicit_chat_id=explicit_chat_id,
        )

        if not recipients:
            raise ValueError("No hay usuarios de Telegram registrados para esta notificacion")

        notifications = []
        for recipient in recipients:
            notifications.append(
                self.repository.create_notification(
                    event["uid"],
                    {
                        "cliente_uid": cliente_uid,
                        "sucursal_uid": event.get("sucursal_uid") or payload.get("sucursal_uid"),
                        "tipo": "telegram",
                        "destinatario": str(recipient["telegram_chat_id"]),
                        "titulo": title_for_event(event["evento"]),
                        "contenido": content,
                    },
                )
            )

        return notifications

    def _deliver_telegram_notification(self, event, notification):
        payload = self._payload_from_event(event)
        chat_id = notification.get("destinatario")

        try:
            self.telegram_client.send_message(chat_id, notification["contenido"])
            pdf = payload.get("factura_pdf") or payload.get("archivo_pdf") or payload.get("factura_url")
            if pdf:
                self.telegram_client.send_document(
                    chat_id,
                    pdf,
                    caption=f"Factura de venta {escape(str(payload.get('venta_uid') or event.get('referencia_uid') or ''))}",
                )
            self.repository.update_notification_status(notification["uid"], "enviada")
        except Exception as exc:
            self.repository.update_notification_status(notification["uid"], "error", str(exc))
            raise

    @staticmethod
    def _payload_from_event(event):
        return event.get("payload") or {}


def title_for_event(event_name):
    titles = {
        "VENTA_CONFIRMADA": "Venta confirmada",
        "VENTA_COMPLETADA": "Venta completada",
        "FACTURA_EMITIDA": "Factura emitida",
        "SUCURSAL_CREADA": "Sucursal creada",
        "EMPLEADO_CREADO": "Empleado creado",
    }
    return titles.get(event_name, event_name.replace("_", " ").title())


def parse_start_parameter(text):
    parts = text.split(maxsplit=1)
    command = parts[0].split("@", 1)[0]
    if command != "/start":
        return None
    if len(parts) == 1:
        return None
    value = parts[1].strip()
    return value or None


def build_message(event_name, payload):
    if event_name in ("VENTA_CONFIRMADA", "VENTA_COMPLETADA", "FACTURA_EMITIDA"):
        return build_sale_message(event_name, payload)

    title = escape(title_for_event(event_name))
    lines = [f"<b>{title}</b>"]
    for key in ("nombre", "uid", "cliente_uid", "sucursal_uid"):
        if payload.get(key):
            lines.append(f"{escape(key)}: {escape(str(payload[key]))}")
    return "\n".join(lines)


def build_sale_message(event_name, payload):
    title = escape(title_for_event(event_name))
    venta_uid = escape(str(payload.get("venta_uid") or payload.get("referencia_uid") or "Sin UID"))
    cliente = escape(str(payload.get("cliente_nombre") or payload.get("cliente_uid") or "Consumidor final"))
    sucursal = escape(str(payload.get("sucursal_nombre") or payload.get("sucursal_uid") or "Sin sucursal"))
    total = format_money(payload.get("total_centavos") or payload.get("total"))

    lines = [
        f"<b>{title}</b>",
        f"Venta: {venta_uid}",
        f"Cliente: {cliente}",
        f"Sucursal: {sucursal}",
        f"Total: {total}",
    ]

    items = payload.get("detalle") or payload.get("items") or []
    if items:
        lines.append("")
        lines.append("<b>Detalle de compra</b>")
        for item in items[:20]:
            nombre = escape(str(item.get("nombre") or item.get("producto") or item.get("producto_uid") or "Producto"))
            cantidad = escape(str(item.get("cantidad") or 1))
            subtotal = format_money(item.get("subtotal_centavos") or item.get("subtotal"))
            lines.append(f"- {nombre} x{cantidad}: {subtotal}")

    factura = payload.get("numero_factura")
    if factura:
        lines.append(f"Factura: {escape(str(factura))}")

    return "\n".join(lines)


def format_money(value):
    try:
        cents = int(value)
    except (TypeError, ValueError):
        return "Bs 0.00"
    return f"Bs {cents / 100:.2f}"
