from html import escape


class NotificationService:
    def __init__(self, repository, gmail_client=None):
        self.repository = repository
        self.gmail_client = gmail_client

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
                self._deliver_notification(event, notification)
            self.repository.mark_event_processed(event["uid"])
            self.repository.log("publicar_evento", "exitoso", "Evento procesado", "evento", event["uid"])
            return {"event": event, "notifications": notifications, "delivered": True}
        except Exception as exc:
            self.repository.mark_event_error(event["uid"], str(exc))
            self.repository.log("publicar_evento", "error", str(exc), "evento", event["uid"])
            return {"event": event, "notifications": [], "delivered": False, "error": str(exc)}

    def _create_notifications_for_event(self, event):
        payload = self._payload_from_event(event)
        content = build_message(event["evento"], payload)
        
        notifications = []
        
        # Notificaciones por Email
        email_recipient = payload.get("email") or payload.get("correo_electronico")
        cliente_uid = event.get("cliente_uid") or payload.get("cliente_uid")
        if not email_recipient and cliente_uid:
            subscriber = self.repository.get_subscriber_by_cliente_uid(cliente_uid)
            if subscriber and subscriber.get("email"):
                email_recipient = subscriber["email"]
        
        if email_recipient:
            notifications.append(
                self.repository.create_notification(
                    event["uid"],
                    {
                        "cliente_uid": cliente_uid,
                        "sucursal_uid": event.get("sucursal_uid") or payload.get("sucursal_uid"),
                        "tipo": "correo",
                        "destinatario": email_recipient,
                        "titulo": title_for_event(event["evento"]),
                        "contenido": content,
                    },
                )
            )
        
        # Si no hay email, simplemente retornamos lista vacía sin error
        # Esto permite registrar eventos que no requieren notificación por email
        # (ej: creación de sucursales o empleados sin email)
        
        return notifications

    def _deliver_notification(self, event, notification):
        """Entrega una notificación por el canal correspondiente (Email)."""
        notification_type = notification.get("tipo")
        
        if notification_type == "correo":
            self._deliver_email_notification(event, notification)
        else:
            raise ValueError(f"Tipo de notificación no soportado: {notification_type}")

    def _deliver_email_notification(self, event, notification):
        """Envía una notificación por correo electrónico."""
        recipient = notification.get("destinatario")
        
        try:
            if not self.gmail_client or not self.gmail_client.enabled:
                raise RuntimeError("Cliente de Gmail no está configurado")
            
            self.gmail_client.send_notification_email(
                recipient=recipient,
                title=notification["titulo"],
                content=notification["contenido"],
                event_data=event
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
