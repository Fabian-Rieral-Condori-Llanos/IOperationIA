# Microservicio de Notificaciones

Servicio Flask en el puerto `5005`. Recibe eventos REST desde otros microservicios, guarda el historial en `database/notificaciones.db` y envía notificaciones por **Gmail**.

## Canal de notificación soportado

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

El servicio de notificaciones está diseñado para ser consumido por cualquier microservicio del sistema. Cada microservicio debe enviar un evento al endpoint `/api/eventos/publicar` con la estructura adecuada según el tipo de notificación.

### Estructura común de todos los eventos

```json
{
  "evento": "NOMBRE_DEL_EVENTO",
  "origen": "nombre_del_microservicio",
  "referencia_tipo": "tipo_de_objeto",
  "referencia_uid": "UID_DEL_OBJETO",
  "cliente_uid": "UID_DEL_CLIENTE",
  "sucursal_uid": "UID_DE_SUCURSAL",
  "payload": {
    "email": "destinatario@ejemplo.com",
    "pdf_url": "http://url/al/pdf",
    "otros_datos_especificos": "valor"
  }
}
```

**Campos comunes:**
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `evento` | string | Sí | Nombre del evento (ej: VENTA_CONFIRMADA, STOCK_BAJO) |
| `origen` | string | Sí | Microservicio que origina el evento |
| `referencia_uid` | string | No | UID de referencia del objeto que generó el evento |
| `cliente_uid` | string | No | UID del cliente afectado (para vincular con suscriptores) |
| `sucursal_uid` | string | No | UID de la sucursal relacionada |
| `payload.email` | string | Condicional | Email del destinatario (requerido si no hay suscriptor registrado) |
| `payload.pdf_url` | string | No | URL para descargar PDF adjunto (el servicio NO genera PDFs, solo los enlaza) |

---

### 1. Desde Ventas Service

#### Evento: VENTA_CONFIRMADA
Cuando se confirma una venta:

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

**Campos específicos para ventas:**
- `payload.venta_uid`: UID único de la venta
- `payload.cliente_nombre`: Nombre del cliente
- `payload.sucursal_nombre`: Nombre de la sucursal
- `payload.numero_factura`: Número de factura emitida
- `payload.total_centavos`: Total en centavos de la venta
- `payload.pdf_url`: URL donde se puede descargar el PDF de la factura (**IMPORTANTE**: El PDF debe ser generado por el servicio de ventas, este servicio solo lo enlaza)
- `payload.detalle`: Lista de productos comprados (array de objetos con `producto`, `cantidad`, `subtotal_centavos`)

#### Evento: VENTA_COMPLETADA
Cuando se completa una venta (mismo formato que VENTA_CONFIRMADA).

---

### 2. Desde Clientes Service

#### Evento: CLIENTE_CREADO
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
      "correo": "maria@ejemplo.com",
      "telefono": "77712345",
      "nit_ci": "1234567"
    }
  }'
```

**Campos específicos para clientes:**
- `payload.cliente_uid`: UID del cliente creado
- `payload.nombre`: Nombre completo del cliente
- `payload.correo`: Correo electrónico del cliente
- `payload.telefono`: Teléfono de contacto (opcional)
- `payload.nit_ci`: NIT o CI del cliente (opcional)

---

### 3. Desde Inventario Service

#### Evento: STOCK_BAJO
Cuando el stock de un producto es bajo:

```bash
curl -X POST http://127.0.0.1:5005/api/eventos/publicar \
  -H "Content-Type: application/json" \
  -d '{
    "evento": "STOCK_BAJO",
    "origen": "inventario_service",
    "referencia_tipo": "inventario",
    "referencia_uid": "INV-001",
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

**Campos específicos para inventario:**
- `payload.producto_uid`: UID del producto con stock bajo
- `payload.producto_nombre`: Nombre del producto
- `payload.stock_actual`: Cantidad actual en stock
- `payload.stock_minimo`: Stock mínimo configurado
- `payload.sucursal_nombre`: Nombre de la sucursal
- `payload.email`: Email del responsable de compras/administrador

---

### 4. Desde Productos Service

#### Evento: PRODUCTO_CREADO
Cuando se crea un nuevo producto:

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
      "categoria": "Lácteos",
      "precio_centavos": 1500,
      "email": "admin@ejemplo.com"
    }
  }'
```

**Campos específicos para productos:**
- `payload.producto_uid`: UID del producto creado
- `payload.nombre`: Nombre del producto
- `payload.categoria`: Categoría del producto
- `payload.precio_centavos`: Precio en centavos
- `payload.email`: Email del destinatario de la notificación

---

### 5. Desde Administración Service

#### Evento: SUCURSAL_CREADA
Cuando se crea una nueva sucursal:

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
      "direccion": "Av. Principal #123",
      "ciudad": "Cochabamba",
      "email": "admin@ejemplo.com"
    }
  }'
```

**Campos específicos para sucursales:**
- `payload.sucursal_uid`: UID de la sucursal creada
- `payload.nombre`: Nombre de la sucursal
- `payload.direccion`: Dirección física
- `payload.ciudad`: Ciudad donde se ubica
- `payload.email`: Email del destinatario

#### Evento: EMPLEADO_CREADO
Cuando se crea un nuevo empleado:

```bash
curl -X POST http://127.0.0.1:5005/api/eventos/publicar \
  -H "Content-Type: application/json" \
  -d '{
    "evento": "EMPLEADO_CREADO",
    "origen": "administracion_service",
    "referencia_tipo": "empleado",
    "referencia_uid": "EMP-NUEVO-001",
    "sucursal_uid": "SUC-PRADO",
    "payload": {
      "empleado_uid": "EMP-NUEVO-001",
      "nombre": "Carlos López",
      "cargo": "Vendedor",
      "telefono": "77798765",
      "sucursal_nombre": "Sucursal Prado",
      "email": "admin@ejemplo.com"
    }
  }'
```

**Campos específicos para empleados:**
- `payload.empleado_uid`: UID del empleado creado
- `payload.nombre`: Nombre completo del empleado
- `payload.cargo`: Cargo o puesto
- `payload.telefono`: Teléfono de contacto
- `payload.sucursal_nombre`: Nombre de la sucursal asignada
- `payload.email`: Email del destinatario

---

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

**Nota:** Si el payload del evento ya incluye un campo `email`, ese será usado prioritariamente. El suscriptor se usa como fallback cuando no se proporciona email explícito.

---

## Tablas usadas en la base de datos

- `eventos`: Historial de eventos recibidos
- `notificaciones`: Historial de notificaciones generadas
- `logs`: Logs del servicio
- `email_suscriptores`: Suscriptores registrados para recibir emails

Estructura de `email_suscriptores`:
```sql
CREATE TABLE email_suscriptores(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL UNIQUE,
    nombre TEXT,
    cliente_uid TEXT,
    estado TEXT NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo','inactiva')),
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## Estados

- `eventos.estado = procesado`: El evento fue guardado y se enviaron las notificaciones.
- `eventos.estado = error`: El evento fue guardado, pero no había destinatarios o el canal rechazó el envío.
- `notificaciones.estado = enviada`: El canal (Email) aceptó el mensaje.
- `notificaciones.estado = error`: No se pudo enviar a ese destinatario.
- `notificaciones.tipo = email`: Notificación enviada por correo electrónico.

---

## Notas sobre PDFs

**IMPORTANTE:** Este servicio de notificaciones NO genera PDFs. Los PDFs deben ser generados por los microservicios correspondientes (ej: ventas_service genera el PDF de la factura) y proporcionar una URL accesible.

Para el caso de ventas u otros eventos que requieran adjuntar documentos:

1. **URL (`pdf_url`)**: Se incluye un enlace en el cuerpo del email para descargar el PDF desde la URL proporcionada.
   - Ejemplo: `http://localhost:5001/api/ventas/VEN-001/pdf`
   - El servicio de ventas debe tener un endpoint que genere y retorne el PDF

2. **El servicio solo muestra un botón atractivo** en el email HTML que permite al usuario descargar el PDF haciendo clic.

**Recomendación:** Cada microservicio que necesite enviar PDFs debe:
- Generar el PDF internamente
- Exponer un endpoint público para descargarlo
- Pasar la URL en el campo `payload.pdf_url` al publicar el evento

---

## Ejemplo de código Python para enviar eventos desde otro microservicio

```python
import requests

NOTIFICACIONES_URL = "http://127.0.0.1:5005/api/eventos/publicar"

def publicar_evento_venta_confirmada(venta_data):
    """Publica un evento de venta confirmada al servicio de notificaciones."""
    evento = {
        "evento": "VENTA_CONFIRMADA",
        "origen": "ventas_service",
        "referencia_tipo": "venta",
        "referencia_uid": venta_data["uid"],
        "cliente_uid": venta_data["cliente_uid"],
        "sucursal_uid": venta_data["sucursal_uid"],
        "payload": {
            "venta_uid": venta_data["uid"],
            "cliente_nombre": venta_data.get("cliente_nombre"),
            "sucursal_nombre": venta_data.get("sucursal_nombre"),
            "numero_factura": venta_data.get("numero_factura"),
            "total_centavos": venta_data["total_centavos"],
            "pdf_url": f"http://localhost:5001/api/ventas/{venta_data['uid']}/pdf",
            "email": venta_data.get("cliente_email"),
            "detalle": venta_data.get("detalle", [])
        }
    }
    
    try:
        respuesta = requests.post(NOTIFICACIONES_URL, json=evento, timeout=2)
        return respuesta.status_code == 201
    except requests.RequestException:
        # Si falla la notificación, no se detiene el proceso principal
        return False
```

---

## Frontend

El frontend incluye una sección de notificaciones accesible desde la SPA que muestra:
- Eventos recibidos
- Notificaciones generadas
- Suscriptores de email registrados

Para acceder: Click en el botón "Notificaciones" del menú lateral.
