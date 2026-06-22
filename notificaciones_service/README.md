# Microservicio de Notificaciones

Servicio Flask en el puerto `5005`. Recibe eventos REST desde otros microservicios, guarda el historial en `database/notificaciones.db` y envía notificaciones únicamente por Telegram.

## Flujo real del bot

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

Si el evento no trae `cliente_uid`, se enviará a todos los suscriptores activos. Esto sirve para eventos administrativos o generales.

## Configuración

El token se carga desde `.env` o variables de entorno. En esta máquina ya quedó configurado en `.env`, que está ignorado por Git.

Variables soportadas:

```bash
TELEGRAM_BOT_TOKEN="TOKEN_DEL_BOT"
TELEGRAM_POLLING_ENABLED=true
TELEGRAM_POLLING_INTERVAL_SECONDS=8
```

No se usa WhatsApp, SMS ni correo. Todas las notificaciones nuevas se crean con `tipo = telegram`.

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

El polling automático queda activo al levantar el servicio. Si quieres forzar una lectura de `/start` desde Telegram:

```bash
curl -X POST http://127.0.0.1:5005/api/telegram/sincronizar
```

Para ver usuarios registrados:

```bash
curl http://127.0.0.1:5005/api/telegram/suscriptores
```

## Publicar una venta

Ventas debe enviar el detalle necesario dentro del evento. Notificaciones no debe consultar directamente `ventas.db`, porque eso rompe el aislamiento de microservicios.

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
      "detalle": [
        {
          "producto": "Leche Pil 980cc",
          "cantidad": 1,
          "subtotal_centavos": 1850
        }
      ],
      "factura_pdf": "/ruta/local/factura.pdf"
    }
  }'
```

Si `factura_pdf`, `archivo_pdf` o `factura_url` existe en el `payload`, el servicio enviará el resumen y luego intentará enviar el PDF como documento de Telegram.

## Endpoints

- `GET /api/health`: estado del servicio.
- `POST /api/eventos/publicar`: registra y procesa un evento.
- `GET /api/eventos?limit=50`: lista eventos recientes.
- `GET /api/eventos/<uid>`: obtiene un evento.
- `POST /api/eventos/<uid>/reintentar`: reintenta el envío.
- `GET /api/notificaciones?limit=50`: lista notificaciones generadas.
- `POST /api/telegram/sincronizar`: lee mensajes `/start` pendientes y registra usuarios.
- `GET /api/telegram/suscriptores`: lista usuarios de Telegram registrados.

## Tablas usadas

Tablas existentes:

- `eventos`
- `notificaciones`
- `logs`

Tablas agregadas para Telegram:

- `telegram_suscriptores`: guarda `telegram_chat_id`, datos básicos del usuario y `cliente_uid` opcional.
- `telegram_estado`: guarda el último `update_id` leído para no procesar dos veces el mismo `/start`.

## Estados

- `eventos.estado = procesado`: el evento fue guardado y se enviaron las notificaciones.
- `eventos.estado = error`: el evento fue guardado, pero no había destinatarios o Telegram rechazó el envío.
- `notificaciones.estado = enviada`: Telegram aceptó el mensaje.
- `notificaciones.estado = error`: no se pudo enviar a ese destinatario.
