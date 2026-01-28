/* static/js/main.js */
console.log('Cargando GeoMonitor Full Stack...');

const API_URL = '';

// 1. CONFIGURACIÓN DEL MAPA
const map = L.map('map-container').setView([-36.68, -73.03], 11);

L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; CARTO',
    maxZoom: 19
}).addTo(map);

// Variables Globales
let capaMarcadores = L.layerGroup().addTo(map);
let datosCache = []; 
let marcadorActual = null;
let rolUsuario = 'Invitado';

// 2. CARGA INICIAL Y GESTIÓN DE CAPAS
document.addEventListener("DOMContentLoaded", function() {
    
    // --- [NUEVO] LÓGICA MENÚ MÓVIL ---
    const btnMenu = document.getElementById('btn-menu-movil'); 
    const panelLateral = document.querySelector('aside');

    if (btnMenu && panelLateral) {
        btnMenu.addEventListener('click', () => {
            if (panelLateral.style.display === 'flex') {
                panelLateral.style.display = 'none';
            } else {
                panelLateral.style.display = 'flex';
            }
        });
    }

    // 1. Poner fecha actual en el panel
    const textoFecha = document.getElementById('fecha-actual');
    if (textoFecha) {
        textoFecha.innerText = new Date().toLocaleDateString('es-CL', { 
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
        });
    }

    // 2. Configurar botones de capas de forma segura
    const btnTemp = document.getElementById('btn-temp');
    const btnFisico = document.getElementById('btn-fisico');
    const btnBio = document.getElementById('btn-bio');

    if(btnTemp) btnTemp.addEventListener('change', () => pintarMapa('temperatura'));
    if(btnFisico) btnFisico.addEventListener('change', () => pintarMapa('fisicos'));
    if(btnBio) btnBio.addEventListener('change', () => pintarMapa('biologicos'));

    // 3. Cargar datos del servidor
    cargarDatos();
});

function cargarDatos() {
    // 1. Cambio a buscar en mapa.php
    console.log("Solicitando datos a: mapa.php"); 
    
    fetch('mapa.php')
        .then(response => {
            // Verifica si la respuesta es correcta antes de procesar
            if (!response.ok) throw new Error("Error al conectar con mapa.php");
            return response.json();
        })
        .then(data => {
            console.log("Datos recibidos:", data); 
              
            if(data.datos || Array.isArray(data)) {
                datosCache = data.datos ? data.datos : data; 
                pintarMapa('temperatura'); 
            } else {
                console.warn("La respuesta no tiene el formato esperado.");
            }
        })
        .catch(error => {
            console.error('Error al cargar datos:', error);
            alert("No se pudieron cargar los datos del mapa. Revisa la consola.");
        });
}

function pintarMapa(modo) {
    console.log(`Pintando capa: ${modo}`);
    capaMarcadores.clearLayers();

    datosCache.forEach(punto => {
        let lat = punto.coords ? punto.coords.lat : punto.lat;
        let lng = punto.coords ? punto.coords.lng : punto.lng;

        if(!lat || !lng) return; 

        let color = '#3388ff';
        let popupHTML = '';
        
        // Lógica de colores
        if (modo === 'temperatura') {
            if (punto.temperatura >= 17) color = '#D32F2F'; 
            else if (punto.temperatura <= 12) color = '#29B6F6'; 
            else color = '#FBC02D'; 

            popupHTML = `
                <div style="text-align:center; font-family:Arial;">
                    <h5 style="margin:0; color:#555">🌡️ Temperatura</h5>
                    <hr style="margin:5px 0">
                    <h2 style="margin:5px; color:${color}">${punto.temperatura} °C</h2>
                    <small>Coord: ${lat.toFixed(2)}, ${lng.toFixed(2)}</small>
                </div>`;
        } 
        else if (modo === 'fisicos') {
            color = '#9C27B0';
            popupHTML = `
                <div style="font-family:Arial;">
                    <h5 style="margin:0; color:#9C27B0">🌊 Datos Físicos</h5>
                    <hr style="margin:5px 0">
                    <b>Salinidad:</b> ${punto.salinidad} PSU<br>
                    <b>Corriente:</b> ${punto.velocidad} m/s<br>
                    <b>Altura Mar:</b> ${punto.altura} m
                </div>`;
        }
        else if (modo === 'biologicos') {
            color = '#4CAF50';
            popupHTML = `
                <div style="font-family:Arial;">
                    <h5 style="margin:0; color:#4CAF50">🌿 Datos Biológicos</h5>
                    <hr style="margin:5px 0">
                    <b>Clorofila:</b> ${punto.clorofila || '--'} mg/m³<br>
                    <b>Oxígeno:</b> ${punto.oxigeno || '--'} ml/L
                </div>`;
        }

        const marker = L.circleMarker([lat, lng], {
            radius: 10,
            fillColor: color,
            color: "#fff",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9,
            interactive: true 
        });

        marker.bindPopup(popupHTML);
        capaMarcadores.addLayer(marker);
    });
}

// 3. SONDA VIRTUAL
map.on('click', function(e) {
    document.getElementById('map-container').style.cursor = 'wait';
    
        fetch(`${API_URL}/api/v1/consulta-punto`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat: e.latlng.lat, lng: e.latlng.lng })
    })
    .then(res => res.json())
    .then(resp => {
        document.getElementById('map-container').style.cursor = 'default';
        if (resp.encontrado) {
            mostrarPopupSonda(resp.datos, e.latlng.lat, e.latlng.lng);
        } else {
            console.log("No hay datos cercanos.");
                    }
    })
    .catch(err => {
        console.error(err);
        document.getElementById('map-container').style.cursor = 'default';
    });
});

function mostrarPopupSonda(d, lat, lng) {
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
        </div>`;
    marcadorActual = L.marker([lat, lng]).addTo(map).bindPopup(html).openPopup();
}

// 4. INGRESO MANUAL
function abrirModal() { document.getElementById('modal-ingreso').style.display = 'block'; }
function cerrarModal() { document.getElementById('modal-ingreso').style.display = 'none'; }

window.onclick = function(event) {
    const modal = document.getElementById('modal-ingreso');
    if (event.target == modal) modal.style.display = "none";
}

function guardarDatosManuales() {
    const temp = document.getElementById('input-temp').value;
    const sal = document.getElementById('input-sal').value;
    
    if (!temp) {
        alert("⚠️ Debes ingresar al menos la Temperatura.");
        return;
    }

    const datosEnvio = {
        temperatura: parseFloat(temp),
        salinidad: sal ? parseFloat(sal) : 0.0,
       
    };

    fetch(`${API_URL}/api/v1/ingreso-manual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datosEnvio)
    })
    .then(res => res.json())
    .then(data => {
        if (data.mensaje === 'OK' || data.exito) {
            alert("✅ Datos guardados");
            cerrarModal();
            cargarDatos(); 
        } else {
            alert("❌ Error: " + (data.error || 'Desconocido'));
        }
    })
    .catch(err => alert("Error de conexión: " + err));
}

// 5. LOGIN Y SEGURIDAD
function loginReal() {
    const email = prompt("📧 Correo:", "admin@geochile.cl");
    if (!email) return;
    const password = prompt("🔑 Contraseña:", "1234"); 
    if (!password) return;

    // Ajuste de sintaxis en el fetch
    fetch('login.php'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    }
    .then(res => {
        // Si el servidor responde con error (404, 500), lanzamos una alerta técnica
        if (!res.ok) throw new Error("El servidor respondió con un error (HTML). Revisa login.php");
        return res.json();
    })
    .then(data => {
        // IMPORTANTE: Verifica si en PHP usas 'exito' o 'success'
        if (data.exito) { 
            alert(`🔓 Hola, tu rol es: ${data.rol}`);
            // Aquí puedes activar tus paneles
            if (typeof aplicarPermisos === "function") aplicarPermisos(data.rol);
        } else {
            alert("❌ Credenciales incorrectas: " + (data.error || ""));
        }
    })
    .catch(err => {
        console.error("Detalle del error:", err);
        alert("Error de conexión: Asegúrate de que login.php existe y no tiene errores.");
    });
}

function cerrarSesion() {
    if(confirm("¿Cerrar sesión?")) window.location.reload();
}

function aplicarPermisos(rol) {
        
    const panelBotones = document.getElementById('panel-botones');
    const panelUsuario = document.getElementById('panel-usuario');
    const lblUsuario = document.getElementById('lbl-usuario');
    
    if(lblUsuario) lblUsuario.innerText = rol;
    if(panelBotones) panelBotones.style.display = 'none';
    if(panelUsuario) panelUsuario.style.display = 'flex';

    const btnIngreso = document.getElementById('btn-ingreso');
    if (btnIngreso) {
        btnIngreso.style.display = (rol === 'Lector') ? 'none' : 'block';
    }

    if (rol === 'Admin') {
    const btnAdmin = document.getElementById('btn-admin-users');
    if (btnAdmin) btnAdmin.style.display = 'block';
}

function aplicarPermisos(rol) {

    const panelBotones = document.getElementById('panel-botones');
    const panelUsuario = document.getElementById('panel-usuario');
    const lblUsuario = document.getElementById('lbl-usuario');
    const btnIngreso = document.getElementById('btn-ingreso');
    const btnAdmin = document.getElementById('btn-admin-users');

    if (lblUsuario) lblUsuario.innerText = rol;
    if (panelBotones) panelBotones.style.display = 'none';
    if (panelUsuario) panelUsuario.style.display = 'flex';

    // Lector no puede ingresar datos
    if (btnIngreso) {
        btnIngreso.style.display = (rol === 'Lector') ? 'none' : 'block';
    }

    // SOLO ADMIN ve gestión de usuarios
    if (btnAdmin) {
        btnAdmin.style.display = (rol === 'Admin') ? 'block' : 'none';
    }
}

}