# Microservicio de Notificaciones

Servicio Flask en el puerto `5005`. Recibe eventos REST desde otros microservicios, guarda el historial en `database/notificaciones.db` y envía notificaciones por **Gmail**.

## Canales de notificación soportados

### Gmail (único canal configurado)
El servicio envía notificaciones por correo electrónico utilizando Gmail con una contraseña de aplicación.

**Configuración requerida en `config.py`:**
- `GMAIL_EMAIL`: Tu dirección de Gmail (reemplazar "tu_email@gmail.com" por tu email real)
- `GMAIL_APP_PASSWORD`: Contraseña de aplicación generada en Google ("hmln jmpo yqol fwwc")

**Para generar una contraseña de aplicación:**
1. Ve a tu cuenta de Google
2. Activa la verificación en dos pasos
3. Genera una contraseña de aplicación en: https://myaccount.google.com/apppasswords
4. Reemplaza el valor en `config.py`

## Configuración

Las credenciales están hardcodeadas directamente en `config.py`. No se usa archivo `.env`.

Variables en `config.py`:

```python
GMAIL_EMAIL = "tu_email@gmail.com"  # Reemplazar con el email real
GMAIL_APP_PASSWORD = "hmln jmpo yqol fwwc"  # Contraseña de aplicación
GMAIL_SMTP_SERVER = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587
GMAIL_USE_TLS = True
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

### Email
- `GET /api/email/suscriptores`: lista suscriptores de email registrados.
- `POST /api/email/suscriptores`: registra un nuevo suscriptor de email.
- `POST /api/email/probar`: envía un correo de prueba para verificar la configuración.

```bash
curl -X POST http://127.0.0.1:5005/api/email/probar \
  -H "Content-Type: application/json" \
  -d '{"email": "destinatario@ejemplo.com"}'
```

## Integración con otros microservicios

### Desde Ventas Service (venta confirmada/completada)

Cuando se confirma o completa una venta, enviar evento con los siguientes campos:

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
      "pdf_url": "http://localhost:5001/api/ventas/VEN-001/pdf",
      "pdf_documento": "base64_del_pdf_opcional",
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

**Campos importantes para ventas:**
- `evento`: "VENTA_CONFIRMADA" o "VENTA_COMPLETADA"
- `payload.email`: Email del cliente (obligatorio si no está registrado como suscriptor)
- `payload.pdf_url`: URL donde se puede descargar el PDF de la factura/venta
- `payload.pdf_documento`: Contenido del PDF en base64 (opcional, para adjuntar)
- `payload.detalle`: Lista de productos comprados
- `payload.total_centavos`: Total en centavos
- `payload.numero_factura`: Número de factura emitida

### Desde Clientes Service (registro de cliente)

Cuando se registra un nuevo cliente:

```bash
curl -X POST http://127.0.0.1:5005/api/eventos/publicar \
  -H "Content-Type: application/json" \
  -d '{
    "evento": "CLIENTE_CREADO",
    "origen": "clientes_service",
    "referencia_tipo": "cliente",
    "referencia_uid": "CLI-NUEVO-001",
    "payload": {
      "cliente_uid": "CLI-NUEVO-001",
      "nombre": "María Gómez",
      "email": "maria@ejemplo.com"
    }
  }'
```

### Desde Inventario Service (stock bajo)

Cuando el stock de un producto es bajo:

```bash
curl -X POST http://127.0.0.1:5005/api/eventos/publicar \
  -H "Content-Type: application/json" \
  -d '{
    "evento": "STOCK_BAJO",
    "origen": "inventario_service",
    "referencia_tipo": "producto",
    "referencia_uid": "PROD-001",
    "sucursal_uid": "SUC-PRADO",
    "payload": {
      "producto_uid": "PROD-001",
      "producto_nombre": "Leche Pil 980cc",
      "stock_actual": 5,
      "stock_minimo": 10,
      "sucursal_nombre": "Sucursal Prado",
      "email": "admin@ejemplo.com"
    }
  }'
```

### Desde Productos Service (producto creado/actualizado)

Cuando se crea o actualiza un producto:

```bash
curl -X POST http://127.0.0.1:5005/api/eventos/publicar \
  -H "Content-Type: application/json" \
  -d '{
    "evento": "PRODUCTO_CREADO",
    "origen": "productos_service",
    "referencia_tipo": "producto",
    "referencia_uid": "PROD-NUEVO-001",
    "payload": {
      "producto_uid": "PROD-NUEVO-001",
      "nombre": "Nuevo Producto",
      "precio_centavos": 1500,
      "email": "admin@ejemplo.com"
    }
  }'
```

### Desde Administración Service (sucursal/empleado creado)

Cuando se crea una sucursal o empleado:

```bash
curl -X POST http://127.0.0.1:5005/api/eventos/publicar \
  -H "Content-Type: application/json" \
  -d '{
    "evento": "SUCURSAL_CREADA",
    "origen": "administracion_service",
    "referencia_tipo": "sucursal",
    "referencia_uid": "SUC-NUEVA-001",
    "payload": {
      "sucursal_uid": "SUC-NUEVA-001",
      "nombre": "Nueva Sucursal",
      "ciudad": "Cochabamba",
      "email": "admin@ejemplo.com"
    }
  }'
```

## Campos comunes para todos los eventos

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `evento` | string | Sí | Nombre del evento (ej: VENTA_CONFIRMADA, STOCK_BAJO) |
| `origen` | string | Sí | Microservicio que origina el evento |
| `referencia_uid` | string | No | UID de referencia del objeto que generó el evento |
| `cliente_uid` | string | No | UID del cliente afectado (para vincular con suscriptores) |
| `sucursal_uid` | string | No | UID de la sucursal relacionada |
| `payload.email` | string | Conditional | Email del destinatario (requerido si no hay suscriptor) |
| `payload.pdf_url` | string | No | URL para descargar PDF adjunto |
| `payload.pdf_documento` | string | No | Contenido PDF en base64 para adjuntar |

## Registrar suscriptor de email

Para registrar un cliente como suscriptor de notificaciones por email:

```bash
curl -X POST http://127.0.0.1:5005/api/email/suscriptores \
  -H "Content-Type: application/json" \
  -d '{
    "email": "cliente@ejemplo.com",
    "nombre": "Juan Pérez",
    "cliente_uid": "CLI-JUANITO-001"
  }'
```

Una vez registrado, las notificaciones para ese `cliente_uid` se enviarán automáticamente a ese email.

## Tablas usadas

- `eventos`: Historial de eventos recibidos
- `notificaciones`: Historial de notificaciones generadas
- `logs`: Logs del servicio
- `email_suscriptores`: Suscriptores registrados para recibir emails

## Estados

- `eventos.estado = procesado`: El evento fue guardado y se enviaron las notificaciones.
- `eventos.estado = error`: El evento fue guardado, pero no había destinatarios o el canal rechazó el envío.
- `notificaciones.estado = enviada`: El canal (Email) aceptó el mensaje.
- `notificaciones.estado = error`: No se pudo enviar a ese destinatario.
- `notificaciones.tipo = email`: Notificación enviada por correo electrónico.

## Notas sobre PDFs

Para el caso de ventas, el PDF de la factura puede incluirse de dos formas:

1. **URL (`pdf_url`)**: Se incluye un enlace en el cuerpo del email para descargar el PDF.
2. **Documento adjunto (`pdf_documento`)**: El contenido del PDF en base64 se adjunta al email (implementación pendiente).

Recomendación: Usar `pdf_url` apuntando al endpoint del microservicio de ventas que genera el PDF.
