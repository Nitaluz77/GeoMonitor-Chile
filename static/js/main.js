// static/js/main.js - VERSIÓN FINAL INTEGRADA (MAPA + ROLES)
console.log('Cargando GeoMonitor Full Stack...');

const API_URL = 'http://localhost:3000';

// ==========================================
// 1. CONFIGURACIÓN DEL MAPA
// ==========================================
const map = L.map('map-container').setView([-36.675, -73.543], 8);

L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; CARTO',
    maxZoom: 19
}).addTo(map);

// Variables Globales
let marcadorActual = null;
let capaPuntos = L.layerGroup().addTo(map);
let datosGlobales = [];
let rolUsuario = 'Invitado'; // Por defecto

// ==========================================
// 2. CARGA INICIAL
// ==========================================
document.addEventListener("DOMContentLoaded", function() {
    // Poner fecha
    const textoFecha = document.getElementById('fecha-actual');
    if (textoFecha) {
        textoFecha.innerText = new Date().toLocaleDateString('es-CL', { 
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
        });
    }

    // Cargar datos del mapa
    fetch(`${API_URL}/api/v1/mediciones`)
        .then(res => res.json())
        .then(resp => {
            datosGlobales = resp.datos || [];
            cambiarCapa(); // Dibujar mapa inicial
        })
        .catch(err => console.error("Error cargando mapa:", err));
});

// ==========================================
// 3. GESTIÓN DE CAPAS Y COLORES
// ==========================================
function cambiarCapa() {
    // Ver qué radio button está seleccionado
    const radios = document.getElementsByName('capa');
    let capaSeleccionada = 'temperatura';
    for (const r of radios) { if (r.checked) capaSeleccionada = r.value; }

    console.log("🎨 Cambiando a capa:", capaSeleccionada);
    capaPuntos.clearLayers();

    datosGlobales.forEach(d => {
        let valor = 0;
        if(capaSeleccionada === 'temperatura') valor = d.temperatura;
        if(capaSeleccionada === 'salinidad') valor = d.salinidad;
        if(capaSeleccionada === 'velocidad') valor = d.velocidad;
        if(capaSeleccionada === 'altura') valor = d.altura;
        if(capaSeleccionada === 'clorofila') valor = d.clorofila;
        if(capaSeleccionada === 'oxigeno') valor = d.oxigeno;

        const color = obtenerColor(valor, capaSeleccionada);

        L.circleMarker([d.coords.lat, d.coords.lng], {
            radius: 8, fillColor: color, color: "#000", weight: 1, opacity: 1, fillOpacity: 0.8
        })
        .bindTooltip(`${capaSeleccionada.toUpperCase()}: ${parseFloat(valor).toFixed(2)}`)
        .addTo(capaPuntos);
    });
}

function obtenerColor(val, tipo) {
    // Semáforo solo para Temperatura
    if (tipo === 'temperatura') {
        const t = parseFloat(val || 0);
        if (t >= 17) return '#D32F2F'; // Rojo
        if (t >= 14) return '#FBC02D'; // Amarillo
        return '#29B6F6';              // Azul (Frío)
    }
    // Color Cyan para el resto
    return '#00E5FF'; 
}

// ==========================================
// 4. SONDA VIRTUAL (CLIC EN MAPA)
// ==========================================
map.on('click', function(e) {
    document.getElementById('map-container').style.cursor = 'wait';
    
    fetch(`${API_URL}/api/v1/consulta-punto`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat: e.latlng.lat, lng: e.latlng.lng })
    })
    .then(res => res.json())
    .then(resp => {
        document.getElementById('map-container').style.cursor = 'crosshair';
        if (resp.encontrado) {
            mostrarResultado(resp.datos, e.latlng.lat, e.latlng.lng);
        } else {
            // Opcional: alert("⚠️ Zona sin datos.");
        }
    })
    .catch(err => {
        console.error(err);
        document.getElementById('map-container').style.cursor = 'default';
    });
});

function mostrarResultado(d, lat, lng) {
    if (marcadorActual) map.removeLayer(marcadorActual);
    const fmt = (n) => (n !== null && n !== undefined) ? parseFloat(n).toFixed(2) : '--';
    
    const html = `
        <div style="font-family: Arial; min-width: 200px;">
            <h3 style="margin:0 0 10px 0; color:#0288D1; border-bottom: 2px solid #ccc;">📍 Sonda Virtual</h3>
            <table style="width:100%; font-size:13px;">
                <tr><td>🌡️ Temp:</td><td><b>${fmt(d.temperatura)} °C</b></td></tr>
                <tr style="background:#f9f9f9;"><td>🌊 Corriente:</td><td><b>${fmt(d.velocidad)} m/s</b></td></tr>
                <tr><td>📏 Altura:</td><td><b>${fmt(d.altura)} m</b></td></tr>
                <tr style="background:#f9f9f9;"><td>🧂 Salinidad:</td><td><b>${fmt(d.salinidad)} PSU</b></td></tr>
            </table>
            <div style="margin-top:5px; text-align:center; font-weight:bold; color: #555;">
                ${d.nivel_alerta || '--'}
            </div>
        </div>
    `;
    marcadorActual = L.marker([lat, lng]).addTo(map).bindPopup(html).openPopup();
}

// ==========================================
// 5. INGRESO MANUAL (VENTANA MODAL)
// ==========================================
function abrirModal() { document.getElementById('modal-ingreso').style.display = 'block'; }
function cerrarModal() { document.getElementById('modal-ingreso').style.display = 'none'; }

// Cerrar si clic fuera
window.onclick = function(event) {
    const modal = document.getElementById('modal-ingreso');
    if (event.target == modal) modal.style.display = "none";
}

function guardarDatosManuales() {
    const lat = document.getElementById('input-lat').value;
    const lng = document.getElementById('input-lng').value;
    const temp = document.getElementById('input-temp').value;
    
    // Captura de datos extra
    const sal = document.getElementById('input-sal').value;
    const chl = document.getElementById('input-chl').value;
    const oxy = document.getElementById('input-oxy').value;
    const alt = document.getElementById('input-alt').value;
    const u = document.getElementById('input-u').value;
    const v = document.getElementById('input-v').value;
    const alerta = document.getElementById('input-alerta').value;

    if (!lat || !lng || !temp) {
        alert("⚠️ Faltan datos obligatorios (Lat, Lng, Temp).");
        return;
    }

    const datosEnvio = {
        coords: { lat: parseFloat(lat), lng: parseFloat(lng) },
        temperatura: parseFloat(temp),
        salinidad: sal ? parseFloat(sal) : 0.0,
        clorofila: chl ? parseFloat(chl) : 0.0,
        oxigeno: oxy ? parseFloat(oxy) : 0.0,
        altura: alt ? parseFloat(alt) : 0.0,
        u: u ? parseFloat(u) : 0.0,
        v: v ? parseFloat(v) : 0.0,
        nivel_alerta: alerta
    };

    fetch(`${API_URL}/api/v1/ingreso-manual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datosEnvio)
    })
    .then(res => res.json())
    .then(data => {
        if (data.mensaje === 'OK') {
            alert("✅ ¡Datos guardados!");
            cerrarModal();
            // Recargar página para actualizar mapa
            location.reload();
        } else {
            alert("❌ Error: " + (data.error || 'Desconocido'));
        }
    })
    .catch(err => alert("Error de conexión: " + err));
}

// ==========================================
// 6. LOGIN Y ROLES (AQUÍ ESTÁ LO QUE FALTABA)
// ==========================================
function loginReal() {
    const email = prompt("📧 Correo:", "admin@geochile.cl");
    if (!email) return;
    const password = prompt("🔑 Contraseña:", "1234");
    if (!password) return;

    fetch(`${API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, password: password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.exito) {
            rolUsuario = data.rol;
            alert(`👋 ¡Bienvenido ${data.rol}!`);
            actualizarInterfazPorRol(data.rol, email);
        } else {
            alert("❌ " + (data.mensaje || "Error de acceso"));
        }
    })
    .catch(err => alert("Error de servidor: " + err));
}

function cerrarSesion() {
    if(confirm("¿Cerrar sesión?")) {
        window.location.reload(); // Recargar página reinicia todo a modo invitado
    }
}

function actualizarInterfazPorRol(rol, email) {
    // 1. Cambiar cabecera
    document.getElementById('panel-botones').style.display = 'none';
    const panelUser = document.getElementById('panel-usuario');
    panelUser.style.display = 'flex';
    document.getElementById('lbl-usuario').innerText = `${rol}`;

    // 2. Controlar botones según Rol
    // Necesitas poner id="btn-ingreso" a tu botón de ingreso manual en el HTML
    const btnIngreso = document.getElementById('btn-ingreso');
    const panelAcciones = document.querySelector('.panel-seccion:nth-child(3)'); // Busca el panel de acciones

    // Si es Lector -> Esconder Ingreso
    if (rol === 'Lector' && btnIngreso) {
        btnIngreso.style.display = 'none';
    } 
    // Si es Investigador -> Mostrar Ingreso
    else if (rol === 'Investigador' && btnIngreso) {
        btnIngreso.style.display = 'block';
    }
    // Si es Admin -> Mostrar Todo + Gestión
    else if (rol === 'Admin') {
        if (btnIngreso) btnIngreso.style.display = 'block';
        
        // Crear botón Admin si no existe
        if (!document.getElementById('btn-admin-users')) {
            const btnAdmin = document.createElement('button');
            btnAdmin.id = 'btn-admin-users';
            btnAdmin.className = 'btn-gris';
            btnAdmin.innerText = '⚙️ Gestión Usuarios';
            btnAdmin.style.marginTop = '5px';
            btnAdmin.style.background = '#333';
            btnAdmin.style.color = 'white';
            btnAdmin.onclick = function() { window.location.href = 'admin_usuarios.html'; };
            
            // Agregarlo al panel
            if(panelAcciones) panelAcciones.appendChild(btnAdmin);
        }
    }
}