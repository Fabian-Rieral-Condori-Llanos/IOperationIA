// Puertos definidos para cada microservicio
const API_PORTS = {
    ventas: 5001,
    inventario: 5002,
    productos: 5003,
    clientes: 5004,
    notificaciones: 5005,
    administracion: 5006
};

const BASE_URL = 'http://localhost';

let adminState = {
    currentTab: 'sucursales',
    sucursales: [],
    empleados: [],
    editingSucursalId: null,
    editingEmpleadoId: null
};

let notificationState = {
    events: [],
    notifications: []
};

// =========================================================
// FUNCIÓN GLOBAL PARA PETICIONES (USAR ESTA FUNCIÓN SIEMPRE)
// =========================================================
async function apiCall(servicePort, route, method = 'GET', bodyData = null) {
    const url = `${BASE_URL}:${servicePort}${route}`;
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (bodyData && ['POST', 'PUT', 'PATCH'].includes(method)) {
        options.body = JSON.stringify(bodyData);
    }

    try {
        const response = await fetch(url, options);
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.message || `Error HTTP: ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error(`Fallo en la petición a ${url}:`, error);
        throw error;
    }
}

// =========================================================
// LÓGICA DE NAVEGACIÓN Y VISTAS DE LA SPA
// =========================================================
function loadModule(moduleName, buttonElement) {
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    buttonElement.classList.add('active');

    const moduleTitle = moduleName.charAt(0).toUpperCase() + moduleName.slice(1);
    document.getElementById('module-title').innerText = `Módulo de ${moduleTitle}`;

    if (moduleName === 'administracion') {
        renderAdministracionModule();
        return;
    }

    if (moduleName === 'notificaciones') {
        renderNotificacionesModule();
        return;
    }

    const contentArea = document.getElementById('main-content');
    contentArea.innerHTML = `
        <section class="module-card">
            <h4>Área de trabajo del Dev asignado a ${moduleName}</h4>
            <p>La API de este servicio corre en: <strong>${BASE_URL}:${API_PORTS[moduleName]}</strong></p>
            <button class="primary-btn" onclick="testConnection('${moduleName}')">Probar Conexión Backend</button>
        </section>
    `;
}

// =========================================================
// MÓDULO NOTIFICACIONES
// =========================================================
function renderNotificacionesModule() {
    const contentArea = document.getElementById('main-content');
    contentArea.innerHTML = `
        <section class="admin-shell">
            <div class="admin-toolbar">
                <div>
                    <h4>Centro de notificaciones</h4>
                    <p>Eventos recibidos y mensajes generados en notificaciones.db</p>
                </div>
                <div class="form-actions">
                    <button class="secondary-btn" onclick="testConnection('notificaciones')">Probar conexión</button>
                    <button class="primary-btn" onclick="loadNotificacionesData()">Actualizar</button>
                </div>
            </div>
            <div id="notification-message" class="admin-message" hidden></div>
            <div class="admin-grid notifications-grid">
                <div class="table-panel">
                    <div class="table-header">
                        <h5>Eventos</h5>
                        <span id="events-count">0 registros</span>
                    </div>
                    <div class="table-scroll" id="events-table"></div>
                </div>
                <div class="table-panel">
                    <div class="table-header">
                        <h5>Notificaciones</h5>
                        <span id="notifications-count">0 registros</span>
                    </div>
                    <div class="table-scroll" id="notifications-table"></div>
                </div>
            </div>
        </section>
    `;

    loadNotificacionesData();
}

async function loadNotificacionesData() {
    try {
        const port = API_PORTS.notificaciones;
        const [eventsResponse, notificationsResponse] = await Promise.all([
            apiCall(port, '/api/eventos?limit=20'),
            apiCall(port, '/api/notificaciones?limit=20')
        ]);

        notificationState.events = eventsResponse.data || [];
        notificationState.notifications = notificationsResponse.data || [];
        renderNotificacionesTables();
    } catch (error) {
        showNotificationMessage(error.message || 'No se pudo cargar Notificaciones', 'error');
    }
}

function renderNotificacionesTables() {
    const eventsTable = document.getElementById('events-table');
    const notificationsTable = document.getElementById('notifications-table');
    if (!eventsTable || !notificationsTable) return;

    document.getElementById('events-count').textContent = `${notificationState.events.length} registros`;
    document.getElementById('notifications-count').textContent = `${notificationState.notifications.length} registros`;

    eventsTable.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>UID</th>
                    <th>Evento</th>
                    <th>Origen</th>
                    <th>Estado</th>
                    <th>Creado</th>
                </tr>
            </thead>
            <tbody>
                ${notificationState.events.map(event => `
                    <tr>
                        <td>${escapeHtml(event.uid)}</td>
                        <td>${escapeHtml(event.evento)}</td>
                        <td>${escapeHtml(event.origen)}</td>
                        <td><span class="status ${event.estado}">${escapeHtml(event.estado)}</span></td>
                        <td>${escapeHtml(event.creado_en || '-')}</td>
                    </tr>
                `).join('') || '<tr><td colspan="5" class="empty-cell">Sin eventos registrados</td></tr>'}
            </tbody>
        </table>
    `;

    notificationsTable.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>UID</th>
                    <th>Tipo</th>
                    <th>Título</th>
                    <th>Estado</th>
                    <th>Enviado</th>
                </tr>
            </thead>
            <tbody>
                ${notificationState.notifications.map(notification => `
                    <tr>
                        <td>${escapeHtml(notification.uid)}</td>
                        <td>${escapeHtml(notification.tipo)}</td>
                        <td>${escapeHtml(notification.titulo || '-')}</td>
                        <td><span class="status ${notification.estado}">${escapeHtml(notification.estado)}</span></td>
                        <td>${escapeHtml(notification.enviado_en || '-')}</td>
                    </tr>
                `).join('') || '<tr><td colspan="5" class="empty-cell">Sin notificaciones registradas</td></tr>'}
            </tbody>
        </table>
    `;
}

function showNotificationMessage(message, type) {
    const messageBox = document.getElementById('notification-message');
    if (!messageBox) return;

    messageBox.textContent = message;
    messageBox.className = `admin-message ${type}`;
    messageBox.hidden = false;
    window.clearTimeout(showNotificationMessage.timer);
    showNotificationMessage.timer = window.setTimeout(() => {
        messageBox.hidden = true;
    }, 4500);
}

// =========================================================
// MÓDULO ADMINISTRACIÓN
// =========================================================
function renderAdministracionModule() {
    const contentArea = document.getElementById('main-content');
    contentArea.innerHTML = `
        <section class="admin-shell">
            <div class="admin-toolbar">
                <div>
                    <h4>Gestión administrativa</h4>
                    <p>Sucursales y empleados registrados en administracion.db</p>
                </div>
                <button class="secondary-btn" onclick="loadAdministracionData()">Actualizar</button>
            </div>

            <div class="tabs">
                <button class="tab-btn active" id="tab-sucursales" onclick="switchAdminTab('sucursales')">Sucursales</button>
                <button class="tab-btn" id="tab-empleados" onclick="switchAdminTab('empleados')">Empleados</button>
            </div>

            <div id="admin-message" class="admin-message" hidden></div>
            <div id="admin-panel"></div>
        </section>
    `;

    loadAdministracionData();
}

async function loadAdministracionData() {
    try {
        const port = API_PORTS.administracion;
        const [sucursalesResponse, empleadosResponse] = await Promise.all([
            apiCall(port, '/api/sucursales'),
            apiCall(port, '/api/empleados')
        ]);

        adminState.sucursales = sucursalesResponse.data || [];
        adminState.empleados = empleadosResponse.data || [];
        renderAdminPanel();
    } catch (error) {
        showAdminMessage(error.message || 'No se pudo cargar Administración', 'error');
    }
}

function switchAdminTab(tabName) {
    adminState.currentTab = tabName;
    adminState.editingSucursalId = null;
    adminState.editingEmpleadoId = null;
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`tab-${tabName}`).classList.add('active');
    renderAdminPanel();
}

function renderAdminPanel() {
    const panel = document.getElementById('admin-panel');
    if (!panel) return;

    if (adminState.currentTab === 'empleados') {
        panel.innerHTML = renderEmpleadoView();
    } else {
        panel.innerHTML = renderSucursalView();
    }
}

function renderSucursalView() {
    const editing = adminState.sucursales.find(item => item.id === adminState.editingSucursalId);

    return `
        <div class="admin-grid">
            <form class="form-panel" onsubmit="saveSucursal(event)">
                <h5>${editing ? 'Editar sucursal' : 'Nueva sucursal'}</h5>
                <input type="hidden" id="sucursal-id" value="${editing?.id || ''}">
                <label>Nombre
                    <input id="sucursal-nombre" required maxlength="100" value="${escapeHtml(editing?.nombre || '')}">
                </label>
                <label>Dirección
                    <input id="sucursal-direccion" maxlength="140" value="${escapeHtml(editing?.direccion || '')}">
                </label>
                <label>Ciudad
                    <input id="sucursal-ciudad" maxlength="80" value="${escapeHtml(editing?.ciudad || '')}">
                </label>
                <label>Estado
                    <select id="sucursal-estado">
                        <option value="activa" ${editing?.estado === 'activa' ? 'selected' : ''}>Activa</option>
                        <option value="inactiva" ${editing?.estado === 'inactiva' ? 'selected' : ''}>Inactiva</option>
                    </select>
                </label>
                <div class="form-actions">
                    <button class="primary-btn" type="submit">${editing ? 'Guardar cambios' : 'Crear sucursal'}</button>
                    ${editing ? '<button class="secondary-btn" type="button" onclick="cancelSucursalEdit()">Cancelar</button>' : ''}
                </div>
            </form>

            <div class="table-panel">
                <div class="table-header">
                    <h5>Sucursales</h5>
                    <span>${adminState.sucursales.length} registros</span>
                </div>
                <div class="table-scroll">
                    <table>
                        <thead>
                            <tr>
                                <th>UID</th>
                                <th>Nombre</th>
                                <th>Ciudad</th>
                                <th>Estado</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${adminState.sucursales.map(sucursal => `
                                <tr>
                                    <td>${escapeHtml(sucursal.uid)}</td>
                                    <td>${escapeHtml(sucursal.nombre)}</td>
                                    <td>${escapeHtml(sucursal.ciudad || '-')}</td>
                                    <td><span class="status ${sucursal.estado}">${escapeHtml(sucursal.estado)}</span></td>
                                    <td class="row-actions">
                                        <button type="button" onclick="editSucursal(${sucursal.id})">Editar</button>
                                        <button type="button" class="danger" onclick="toggleSucursalStatus(${sucursal.id}, '${sucursal.estado}')">${sucursal.estado === 'activa' ? 'Desactivar' : 'Activar'}</button>
                                    </td>
                                </tr>
                            `).join('') || '<tr><td colspan="5" class="empty-cell">Sin sucursales registradas</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

function renderEmpleadoView() {
    const editing = adminState.empleados.find(item => item.id === adminState.editingEmpleadoId);

    return `
        <div class="admin-grid">
            <form class="form-panel" onsubmit="saveEmpleado(event)">
                <h5>${editing ? 'Editar empleado' : 'Nuevo empleado'}</h5>
                <input type="hidden" id="empleado-id" value="${editing?.id || ''}">
                <label>Nombre
                    <input id="empleado-nombre" required maxlength="100" value="${escapeHtml(editing?.nombre || '')}">
                </label>
                <label>Cargo
                    <input id="empleado-cargo" required maxlength="100" value="${escapeHtml(editing?.cargo || '')}">
                </label>
                <label>Teléfono
                    <input id="empleado-telefono" maxlength="40" value="${escapeHtml(editing?.telefono || '')}">
                </label>
                <label>Sucursal
                    <select id="empleado-sucursal" required>
                        <option value="">Seleccionar sucursal</option>
                        ${adminState.sucursales.map(sucursal => `
                            <option value="${sucursal.id}" ${editing?.sucursal_id === sucursal.id ? 'selected' : ''}>
                                ${escapeHtml(sucursal.nombre)}
                            </option>
                        `).join('')}
                    </select>
                </label>
                <label>Estado
                    <select id="empleado-estado">
                        <option value="activo" ${editing?.estado === 'activo' ? 'selected' : ''}>Activo</option>
                        <option value="inactivo" ${editing?.estado === 'inactivo' ? 'selected' : ''}>Inactivo</option>
                    </select>
                </label>
                <div class="form-actions">
                    <button class="primary-btn" type="submit">${editing ? 'Guardar cambios' : 'Crear empleado'}</button>
                    ${editing ? '<button class="secondary-btn" type="button" onclick="cancelEmpleadoEdit()">Cancelar</button>' : ''}
                </div>
            </form>

            <div class="table-panel">
                <div class="table-header">
                    <h5>Empleados</h5>
                    <span>${adminState.empleados.length} registros</span>
                </div>
                <div class="table-scroll">
                    <table>
                        <thead>
                            <tr>
                                <th>UID</th>
                                <th>Nombre</th>
                                <th>Cargo</th>
                                <th>Sucursal</th>
                                <th>Estado</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${adminState.empleados.map(empleado => `
                                <tr>
                                    <td>${escapeHtml(empleado.uid)}</td>
                                    <td>${escapeHtml(empleado.nombre)}</td>
                                    <td>${escapeHtml(empleado.cargo)}</td>
                                    <td>${escapeHtml(empleado.sucursal_nombre || empleado.sucursal_uid)}</td>
                                    <td><span class="status ${empleado.estado}">${escapeHtml(empleado.estado)}</span></td>
                                    <td class="row-actions">
                                        <button type="button" onclick="editEmpleado(${empleado.id})">Editar</button>
                                        <button type="button" class="danger" onclick="toggleEmpleadoStatus(${empleado.id}, '${empleado.estado}')">${empleado.estado === 'activo' ? 'Desactivar' : 'Activar'}</button>
                                    </td>
                                </tr>
                            `).join('') || '<tr><td colspan="6" class="empty-cell">Sin empleados registrados</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

async function saveSucursal(event) {
    event.preventDefault();
    const id = document.getElementById('sucursal-id').value;
    const payload = {
        nombre: document.getElementById('sucursal-nombre').value,
        direccion: document.getElementById('sucursal-direccion').value,
        ciudad: document.getElementById('sucursal-ciudad').value,
        estado: document.getElementById('sucursal-estado').value
    };

    try {
        if (id) {
            await apiCall(API_PORTS.administracion, `/api/sucursales/${id}`, 'PUT', payload);
            showAdminMessage('Sucursal actualizada correctamente', 'success');
        } else {
            const response = await apiCall(API_PORTS.administracion, '/api/sucursales', 'POST', payload);
            showAdminMessage('Sucursal creada correctamente', 'success');
            // Enviar notificación de creación de sucursal
            await sendNotification('sucursal_creada', 'Nueva Sucursal Creada', `Se ha creado la sucursal: ${payload.nombre}`);
        }
        adminState.editingSucursalId = null;
        await loadAdministracionData();
    } catch (error) {
        showAdminMessage(error.message, 'error');
    }
}

async function saveEmpleado(event) {
    event.preventDefault();
    const id = document.getElementById('empleado-id').value;
    const payload = {
        nombre: document.getElementById('empleado-nombre').value,
        cargo: document.getElementById('empleado-cargo').value,
        telefono: document.getElementById('empleado-telefono').value,
        sucursal_id: Number(document.getElementById('empleado-sucursal').value),
        estado: document.getElementById('empleado-estado').value
    };

    try {
        if (id) {
            await apiCall(API_PORTS.administracion, `/api/empleados/${id}`, 'PUT', payload);
            showAdminMessage('Empleado actualizado correctamente', 'success');
        } else {
            const response = await apiCall(API_PORTS.administracion, '/api/empleados', 'POST', payload);
            showAdminMessage('Empleado creado correctamente', 'success');
            // Enviar notificación de creación de empleado
            await sendNotification('empleado_creado', 'Nuevo Empleado Creado', `Se ha creado el empleado: ${payload.nombre} - ${payload.cargo}`);
        }
        adminState.editingEmpleadoId = null;
        await loadAdministracionData();
    } catch (error) {
        showAdminMessage(error.message, 'error');
    }
}

function editSucursal(id) {
    adminState.editingSucursalId = id;
    renderAdminPanel();
}

function cancelSucursalEdit() {
    adminState.editingSucursalId = null;
    renderAdminPanel();
}

function editEmpleado(id) {
    adminState.editingEmpleadoId = id;
    renderAdminPanel();
}

function cancelEmpleadoEdit() {
    adminState.editingEmpleadoId = null;
    renderAdminPanel();
}

async function toggleSucursalStatus(id, currentStatus) {
    const newStatus = currentStatus === 'activa' ? 'inactiva' : 'activa';
    const payload = { estado: newStatus };

    try {
        await apiCall(API_PORTS.administracion, `/api/sucursales/${id}`, 'PUT', payload);
        showAdminMessage(`Sucursal ${newStatus === 'activa' ? 'activada' : 'desactivada'} correctamente`, 'success');
        // Enviar notificación de cambio de estado
        await sendNotification('sucursal_estado_cambiado', `Sucursal ${newStatus}`, `La sucursal ha sido ${newStatus}`);
        await loadAdministracionData();
    } catch (error) {
        showAdminMessage(error.message, 'error');
    }
}

async function toggleEmpleadoStatus(id, currentStatus) {
    const newStatus = currentStatus === 'activo' ? 'inactivo' : 'activo';
    const payload = { estado: newStatus };

    try {
        await apiCall(API_PORTS.administracion, `/api/empleados/${id}`, 'PUT', payload);
        showAdminMessage(`Empleado ${newStatus === 'activo' ? 'activado' : 'desactivado'} correctamente`, 'success');
        // Enviar notificación de cambio de estado
        await sendNotification('empleado_estado_cambiado', `Empleado ${newStatus}`, `El empleado ha sido ${newStatus}`);
        await loadAdministracionData();
    } catch (error) {
        showAdminMessage(error.message, 'error');
    }
}

async function sendNotification(eventType, titulo, mensaje) {
    try {
        await apiCall(API_PORTS.notificaciones, '/api/eventos', 'POST', {
            evento: eventType,
            origen: 'administracion',
            datos: { titulo, mensaje }
        });
    } catch (error) {
        console.error('Error al enviar notificación:', error);
    }
}

function showAdminMessage(message, type) {
    const messageBox = document.getElementById('admin-message');
    if (!messageBox) return;

    messageBox.textContent = message;
    messageBox.className = `admin-message ${type}`;
    messageBox.hidden = false;
    window.clearTimeout(showAdminMessage.timer);
    showAdminMessage.timer = window.setTimeout(() => {
        messageBox.hidden = true;
    }, 4500);
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// =========================================================
// PRUEBA DE CONEXIÓN UTILIZANDO LA NUEVA FUNCIÓN GLOBAL
// =========================================================
async function testConnection(moduleName) {
    const port = API_PORTS[moduleName];
    try {
        const data = await apiCall(port, '/api/health');
        alert(`Éxito: ${data.message}`);
    } catch (error) {
        alert(error.message || 'Error de conexión con el servicio.');
    }
}

// Cargar vista inicial al iniciar la app
window.onload = () => {
    loadModule('ventas', document.querySelector('.nav-btn'));
};
