# Microservicio de Notificaciones

Servicio Flask en el puerto `5005`. Recibe eventos REST desde otros microservicios, guarda el historial en `database/notificaciones.db` y envía notificaciones por **Telegram** y **Gmail**.

## Canales de notificación soportados

### 1. Telegram (mantenido para compatibilidad)
El bot trabaja con muchos usuarios:

1. Un usuario abre `t.me/ERPNotificacionGrupo3_bot`.
2. Envía `/start`.
3. El servicio lee ese mensaje con `getUpdates`.
4. Se guarda su `telegram_chat_id` en la tabla `telegram_suscriptores`.
5. Cuando llega un evento, el servicio busca destinatarios registrados y envía la notificación por Telegram.

Si quieres vincular un usuario con un cliente del ERP, el usuario debe iniciar el bot así:

```text
/start CLI-JUANITO-001
```

Ese valor se guarda como `cliente_uid`. Cuando Ventas publique un evento con ese mismo `cliente_uid`, la notificación irá solo a los chats vinculados a ese cliente.

### 2. Gmail (nuevo)
El servicio ahora también puede enviar notificaciones por correo electrónico utilizando Gmail con una contraseña de aplicación.

**Configuración requerida:**
- `GMAIL_EMAIL`: Tu dirección de Gmail
- `GMAIL_APP_PASSWORD`: Contraseña de aplicación generada en Google

**Para generar una contraseña de aplicación:**
1. Ve a tu cuenta de Google
2. Activa la verificación en dos pasos
3. Genera una contraseña de aplicación en: https://myaccount.google.com/apppasswords
4. Usa esa contraseña en la variable `GMAIL_APP_PASSWORD`

## Configuración

Las credenciales se cargan desde `.env` o variables de entorno.

Variables soportadas:

```bash
# Configuración de Telegram (opcional)
TELEGRAM_BOT_TOKEN="TOKEN_DEL_BOT"
TELEGRAM_POLLING_ENABLED=true
TELEGRAM_POLLING_INTERVAL_SECONDS=8

# Configuración de Gmail (requerido para notificaciones por email)
GMAIL_EMAIL="tu_email@gmail.com"
GMAIL_APP_PASSWORD="hmln jmpo yqol fwwc"
GMAIL_SMTP_SERVER="smtp.gmail.com"
GMAIL_SMTP_PORT=587
GMAIL_USE_TLS=true
```

## Levantar el servicio

Desde la raíz del proyecto:

```bash
source .venv/bin/activate
python notificaciones_service/app.py
```

Endpoint de salud:

```text
http://127.0.0.1:5005/api/health
```

## Endpoints

### Generales
- `GET /api/health`: estado del servicio.
- `POST /api/eventos/publicar`: registra y procesa un evento.
- `GET /api/eventos?limit=50`: lista eventos recientes.
- `GET /api/eventos/<uid>`: obtiene un evento.
- `POST /api/eventos/<uid>/reintentar`: reintenta el envío.
- `GET /api/notificaciones?limit=50`: lista notificaciones generadas.

### Telegram
- `POST /api/telegram/sincronizar`: lee mensajes `/start` pendientes y registra usuarios.
- `GET /api/telegram/suscriptores`: lista usuarios de Telegram registrados.

### Email (nuevo)
- `POST /api/email/probar`: envía un correo de prueba para verificar la configuración.

```bash
curl -X POST http://127.0.0.1:5005/api/email/probar \
  -H "Content-Type: application/json" \
  -d '{"email": "destinatario@ejemplo.com"}'
```

## Publicar una venta con notificación por email

Ventas debe enviar el detalle necesario dentro del evento. Para enviar notificaciones por email, incluir el campo `email` en el payload:

```bash
curl -X POST http://127.0.0.1:5005/api/eventos/publicar \
  -H "Content-Type: application/json" \
  -d '{
    "evento": "VENTA_CONFIRMADA",
    "origen": "ventas_service",
    "referencia_tipo": "venta",
    "referencia_uid": "VEN-001",
    "cliente_uid": "CLI-JUANITO-001",
    "sucursal_uid": "SUC-PRADO",
    "payload": {
      "venta_uid": "VEN-001",
      "cliente_nombre": "Juanito Pérez",
      "sucursal_nombre": "Sucursal Prado",
      "numero_factura": "F-0001",
      "total_centavos": 1850,
      "email": "juanito@ejemplo.com",
      "detalle": [
        {
          "producto": "Leche Pil 980cc",
          "cantidad": 1,
          "subtotal_centavos": 1850
        }
      ]
    }
  }'
```

El servicio enviará notificaciones por:
- **Telegram**: A todos los suscriptores vinculados al `cliente_uid`
- **Email**: Al correo especificado en `payload.email` o al registrado en el suscriptor

## Tablas usadas

Tablas existentes:

- `eventos`
- `notificaciones`
- `logs`

Tablas agregadas para Telegram y Email:

- `telegram_suscriptores`: guarda `telegram_chat_id`, datos básicos del usuario, `cliente_uid` opcional y `email` opcional.
- `telegram_estado`: guarda el último `update_id` leído para no procesar dos veces el mismo `/start`.

## Estados

- `eventos.estado = procesado`: el evento fue guardado y se enviaron las notificaciones.
- `eventos.estado = error`: el evento fue guardado, pero no había destinatarios o el canal rechazó el envío.
- `notificaciones.estado = enviada`: El canal (Telegram/Email) aceptó el mensaje.
- `notificaciones.estado = error`: no se pudo enviar a ese destinatario.
- `notificaciones.tipo = telegram`: Notificación enviada por Telegram.
- `notificaciones.tipo = email`: Notificación enviada por correo electrónico.
