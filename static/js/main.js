// static/js/main.js 
console.log('Cargando GeoMonitor Full Stack...');

const API_URL = 'https://propitiative-kristen-untarnishing.ngrok-free.dev'; 

// 1. CONFIGURACIÓN DEL MAPA
// Centrado en Bahía de Concepción (Coincide con tus datos de prueba)
const map = L.map('map-container').setView([-36.68, -73.03], 11);

L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; CARTO',
    maxZoom: 19
}).addTo(map);

// Variables Globales
let marcadorActual = null;
let capaPuntos = L.layerGroup().addTo(map);
let datosGlobales = [];
let rolUsuario = 'Invitado';

// 2. CARGA INICIAL
document.addEventListener("DOMContentLoaded", function() {
    // Poner fecha
    const textoFecha = document.getElementById('fecha-actual');
    if (textoFecha) {
        textoFecha.innerText = new Date().toLocaleDateString('es-CL', { 
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
        });
    }

    cargarMapa();
});

function cargarMapa() {
    console.log(" Solicitando datos al servidor...");
    fetch(`${API_URL}/api/v1/mediciones`)
        .then(res => res.json())
        .then(resp => {
            console.log(" Datos recibidos:", resp);
            datosGlobales = resp.datos || [];
            cambiarCapa(); // Dibujar puntos
        })
        .catch(err => console.error("❌ Error cargando mapa:", err));
}

// 3. GESTIÓN DE CAPAS Y COLORES
function cambiarCapa() {
    const radios = document.getElementsByName('capa');
    let capaSeleccionada = 'temperatura';
    for (const r of radios) { if (r.checked) capaSeleccionada = r.value; }

    console.log(" Pintando capa:", capaSeleccionada);
    capaPuntos.clearLayers();

    datosGlobales.forEach(d => {
        let valor = 0;
        // Mapeo seguro de datos
        if(capaSeleccionada === 'temperatura') valor = d.temperatura;
        if(capaSeleccionada === 'salinidad') valor = d.salinidad;
        if(capaSeleccionada === 'velocidad') valor = d.velocidad;
        if(capaSeleccionada === 'altura') valor = d.altura || 0;

        const color = obtenerColor(valor, capaSeleccionada);

        // Creamos el círculo
        L.circleMarker([d.coords.lat, d.coords.lng], {
            radius: 10, fillColor: color, color: "#fff", weight: 1, opacity: 1, fillOpacity: 0.8
        })
        .bindTooltip(`<b>${capaSeleccionada.toUpperCase()}:</b> ${parseFloat(valor).toFixed(2)}`)
        .addTo(capaPuntos);
    });
}

function obtenerColor(val, tipo) {
    if (tipo === 'temperatura') {
        const t = parseFloat(val || 0);
        if (t >= 17) return '#D32F2F'; // Rojo (Caliente/Peligro)
        if (t >= 14) return '#FBC02D'; // Amarillo
        return '#29B6F6';              // Azul
    }
    return '#00E5FF'; // Cyan para todo lo demás
}

// 4. SONDA VIRTUAL (CLIC EN MAPA)
map.on('click', function(e) {
    document.getElementById('map-container').style.cursor = 'wait';
    
    // Enviamos consulta al backend
    fetch(`${API_URL}/api/v1/consulta-punto`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat: e.latlng.lat, lng: e.latlng.lng })
    })
    .then(res => res.json())
    .then(resp => {
        document.getElementById('map-container').style.cursor = 'crosshair';
        if (resp.encontrado) {
            mostrarPopup(resp.datos, e.latlng.lat, e.latlng.lng);
        } else {
            console.log("No hay datos cercanos");
        }
    })
    .catch(err => {
        console.error(err);
        document.getElementById('map-container').style.cursor = 'default';
    });
});

function mostrarPopup(d, lat, lng) {
    if (marcadorActual) map.removeLayer(marcadorActual);
    
    const fmt = (n) => (n !== null && n !== undefined) ? parseFloat(n).toFixed(2) : '--';
    
    const html = `
        <div style="font-family: Arial; text-align:center;">
            <h4 style="margin:0; color:#0288D1;">🔍 Sonda Virtual</h4>
            <hr style="margin:5px 0;">
            <table style="width:100%; font-size:12px; text-align:left;">
                <tr><td>🌡️ Temp:</td><td><b>${fmt(d.temperatura)} °C</b></td></tr>
                <tr><td>🌊 Velocidad:</td><td><b>${fmt(d.velocidad)} m/s</b></td></tr>
                <tr><td>🧂 Salinidad:</td><td><b>${fmt(d.salinidad)} PSU</b></td></tr>
            </table>
            <div style="margin-top:5px; background:#4CAF50; color:white; border-radius:3px; padding:2px;">
                Estado: Normal
            </div>
        </div>
    `;
    marcadorActual = L.marker([lat, lng]).addTo(map).bindPopup(html).openPopup();
}

// 5. INGRESO MANUAL (MODAL)
function abrirModal() { document.getElementById('modal-ingreso').style.display = 'block'; }
function cerrarModal() { document.getElementById('modal-ingreso').style.display = 'none'; }

// Cerrar al hacer clic fuera
window.onclick = function(event) {
    const modal = document.getElementById('modal-ingreso');
    if (event.target == modal) modal.style.display = "none";
}

function guardarDatosManuales() {
    // Solo capturamos lo que el servidor realmente guarda
    const temp = document.getElementById('input-temp').value;
    const sal = document.getElementById('input-sal').value;
    const u = document.getElementById('input-u').value;
    const v = document.getElementById('input-v').value;

    // Validación básica
    if (!temp) {
        alert("⚠️ Debes ingresar al menos la Temperatura.");
        return;
    }

    const datosEnvio = {
        temperatura: parseFloat(temp),
        salinidad: sal ? parseFloat(sal) : 0.0,
        u: u ? parseFloat(u) : 0.0,
        v: v ? parseFloat(v) : 0.0
        // Nota: Lat/Lng se ignoran porque el servidor asigna Zona 1 automáticamente
    };

    fetch(`${API_URL}/api/v1/ingreso-manual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datosEnvio)
    })
    .then(res => res.json())
    .then(data => {
        if (data.mensaje === 'OK' || data.exito) { // Aceptamos ambas respuestas
            alert("✅ ¡Datos guardados exitosamente!");
            cerrarModal();
            location.reload(); // Recargamos para ver el nuevo punto
        } else {
            alert("❌ Error: " + (data.error || 'Desconocido'));
        }
    })
    .catch(err => alert("Error de conexión: " + err));
}
// 6. LOGIN Y SEGURIDAD

function loginReal() {
    const email = prompt("📧 Correo Admin:", "admin@geochile.cl");
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
            alert(`🔓 Acceso concedido: ${data.rol}`);
            aplicarPermisos(data.rol);
        } else {
            alert("❌ " + (data.mensaje || "Acceso denegado"));
        }
    })
    .catch(err => alert("Error de servidor: " + err));
}

function cerrarSesion() {
    if(confirm("¿Cerrar sesión?")) window.location.reload();
}

function aplicarPermisos(rol) {
    // Cambiar texto de usuario
    document.getElementById('lbl-usuario').innerText = rol;
    document.getElementById('panel-botones').style.display = 'none';
    document.getElementById('panel-usuario').style.display = 'flex';

    // Mostrar botón de ingreso solo si es Admin o Investigador
    const btnIngreso = document.getElementById('btn-ingreso');
    if (btnIngreso) {
        if (rol === 'Lector') btnIngreso.style.display = 'none';
        else btnIngreso.style.display = 'block';
  
    }

    const panelAcciones = document.querySelector('.panel-seccion:nth-child(3)'); // Panel de botones
    
    // Si ya existe el botón, lo borramos para no duplicar
    const btnViejo = document.getElementById('btn-admin-users');
    if (btnViejo) btnViejo.remove();

    if (rol === 'Admin') {
        const btnAdmin = document.createElement('button');
        btnAdmin.id = 'btn-admin-users';
        btnAdmin.className = 'btn-gris';
        btnAdmin.style.marginTop = '5px';
        btnAdmin.style.background = '#333';
        btnAdmin.style.color = '#fff';
        btnAdmin.innerText = '⚙️ Gestión Usuarios';
        
        // Al hacer clic, nos lleva a la página que creamos en el Paso 2
        btnAdmin.onclick = function() { window.location.href = 'admin_usuarios.html'; };
        
        // Lo agregamos al panel
        if(panelAcciones) panelAcciones.appendChild(btnAdmin);
    }
}
    
