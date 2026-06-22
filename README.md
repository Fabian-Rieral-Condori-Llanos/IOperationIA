# 🛒 Abuelita Serafina SuperMarket - Arquitectura de Microservicios

Este proyecto es la plataforma tecnológica distribuida para la cadena nacional de supermercados **Abuelita Serafina SuperMarket Bolivia S.A.**

El sistema migra de una estructura monolítica a una **Arquitectura de Microservicios**, asegurando alta disponibilidad, escalabilidad horizontal y despliegue independiente.

El proyecto contempla el desarrollo integral del Backend, Frontend y sus respectivas pruebas.

---

# 🛠️ Stack Tecnológico Estandarizado

* **Frontend:** HTML5, CSS3 (Verde Pastel corporativo) y JavaScript (Vanilla) estructurado como Single Page Application (SPA).
* **Backend:** Python 3.x con el framework **Flask**.
* **Comunicación Interna:** Librería `requests` para comunicación síncrona/asíncrona entre microservicios (REST).
* **Seguridad entre Orígenes:** `Flask-CORS` integrado en cada módulo para la SPA.
* **Base de Datos:** Un archivo **SQLite** independiente por cada microservicio.

> ⚠️ Está estrictamente prohibido compartir tablas entre servicios.

---

# 🚀 Asignación de Equipos, Puertos y Bases de Datos

La arquitectura se divide en 5 servicios independientes.

Cada servicio debe poseer su propia API REST, Base de Datos y documentación Swagger.

| Equipo | Microservicio      | Puerto | Responsable | Base de Datos       | Responsabilidades Principales                                                  |
| ------ | ------------------ | ------ | ----------- | ------------------- | ------------------------------------------------------------------------------ |
| **1**  | **Productos**      | `5003` | Celeste     | `inventario.db`     | CRUD Productos, Categorías, Marcas, productos_costos, historial_precios        |
| **2**  | **Inventario**     | `5002` | Alan        | `inventario.db`     | Stock por sucursal, ingresos, bajas, transferencias e importación desde Excel  |
| **3**  | **Ventas**         | `5001` | Marcelo     | `ventas.db`         | Registrar ventas, descontar inventario, registrar pagos y generar comprobantes |
| **4**  | **Clientes**       | `5004` | Ronaldo     | `ventas.db`         | Gestión de clientes, programa de fidelización, puntos e historial              |
| **5**  | **Notificaciones** | `5005` | Fabian      | `notificaciones.db` | Escuchar eventos y generar notificaciones simuladas (Correo, SMS o WhatsApp)   |
| **6**  | **Administración** | `5006` | Fabian      | `administración.db` | CRUD sucursales, crud empleados                                                |

---

# 📐 Reglas Arquitectónicas (Obligatorias)

Todo el equipo de desarrollo debe regirse por estas directrices técnicas validadas por el Arquitecto del Proyecto.

## 1. Aislamiento de Datos (Regla de Oro)

Cada microservicio debe poseer su propia base de datos.

No se pueden realizar consultas SQL directas entre archivos `.db`.

Si **Ventas** necesita conocer el stock de un producto, deberá consultarlo a **Inventario** mediante una petición HTTP REST.

---

## 2. Validaciones y Seguridad (Requisito de Evaluación)

El sistema será sometido a pruebas estrictas.

Al desarrollar endpoints de creación (productos, sucursales, clientes, etc.):

### Prevención XSS

Está totalmente prohibido aceptar etiquetas HTML o scripts.

Ejemplo:

```html
<script>alert('xss')</script>
```

Las entradas deben ser sanitizadas en el backend.

### Validación de Campos Vacíos

El sistema debe rechazar solicitudes con:

* Campos vacíos.
* Campos que contengan únicamente espacios en blanco.

Ejemplo:

```text
"   "
```

La respuesta debe retornar:

```http
HTTP 400 Bad Request
```

### Manejo de Excepciones

Implementar validaciones y manejo adecuado de excepciones en cada servicio.

---

## 3. Comunicación mediante Eventos

Las acciones que disparan procesos secundarios deben manejarse mediante eventos.

Por ejemplo:

Cuando se complete una venta:

```text
SaleCompleted
```

El servicio de Ventas debe enviar una petición HTTP al servicio de Notificaciones informando del evento.

---

## 4. Manejo de Dinero

Todos los valores monetarios deben almacenarse y procesarse como números enteros (`INTEGER`) representando centavos.

Ejemplo:

| Valor Real | Valor Almacenado |
| ---------- | ---------------- |
| Bs 18.50   | 1850             |
| Bs 99.99   | 9999             |
| Bs 1.00    | 100              |

---

## 5. Control de Versiones y Flujo de Trabajo (Git)

Para mantener la estabilidad del ecosistema:

> 🚫 Está estrictamente prohibido realizar `push` o `commit` directamente sobre la rama `main` o `master`.

### Ramas Asignadas

Cada desarrollador deberá trabajar únicamente sobre la rama asignada para su microservicio.

### Gestión del Project Manager

El Project Manager (Kevin) creará y asignará las ramas oficiales.

No se debe subir código al repositorio remoto hasta recibir la rama correspondiente.

### Integración de Código

Cuando un módulo esté terminado:

1. Realizar pruebas locales.
2. Crear un Pull Request (PR).
3. Esperar revisión.
4. Fusionar únicamente tras aprobación del PM o Arquitecto.

---

# ⚙️ Pasos para Inicializar el Proyecto

Sigue estos pasos para levantar y probar tu módulo localmente.

## Paso 1: Clonar e Instalar Dependencias Generales

Desde la carpeta raíz del proyecto:

```bash
pip install -r requirements.txt
```

---

## Paso 2: Inicializar los Microservicios

Utiliza terminales divididas en VS Code para ejecutar varios servicios simultáneamente.

Navega al directorio de tu servicio:

```bash
cd ventas_service
```

Inicia el servidor:

```bash
python app.py
```

---

## Paso 3: Validar el Backend

Abre el navegador o Postman y verifica el endpoint de salud.

Ejemplo para Ventas:

```text
http://127.0.0.1:5001/api/health
```

Si todo está correcto deberías recibir una respuesta exitosa.

---

## Paso 4: Levantar el Frontend (SPA)

### Instalar Live Server

Instala la extensión **Live Server** desde VS Code.

### Ejecutar el Frontend

1. Abrir:

```text
frontend/index.html
```

2. Clic derecho sobre el archivo.

3. Seleccionar:

```text
Open with Live Server
```

4. Interactuar con la SPA desde el navegador.

---

# 🧩 Extensiones Obligatorias para Visual Studio Code

Para homologar el entorno de trabajo todos los desarrolladores deben instalar las siguientes extensiones.

---

## SQLite Viewer

**Autor:** Florian Klampfer

Permite abrir, explorar y editar archivos SQLite (`.db`) directamente desde Visual Studio Code.

---

## Live Server

**Autor:** Ritwick Dey

Permite crear un servidor web local instantáneo para ejecutar y probar el frontend con recarga automática cada vez que se guardan cambios.

---

# 📄 Créditos

Documento de gobernanza técnica y arquitectura de software desarrollado por:

* **Roberto Vallejos** — Arquitecto de Software
* **Kevin** — Project Manager

---

© ERP Supermercado - Arquitectura basada en Microservicios
