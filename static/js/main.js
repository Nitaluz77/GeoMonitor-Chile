// static/js/main.js
console.log('Cargando mapa Oceanografico...');

// Configuración Global
const API_URL = 'http://localhost:3000'; // Asegúrate que coincida con tu backend

// 1. INICIALIZAR MAPA (Solo una vez)
// Coordenadas ajustadas para encajonar a Chile
var limitesChile = [
    [-58.0, -85.0], // Sur-Oeste 
    [-17.0, -60.0]  // Nor-Este
];

const map = L.map('map-container', {
    maxBounds: limitesChile,
    maxBoundsViscosity: 0.8, // FALTABA LA COMA AQUÍ
    minZoom: 4,
    maxZoom: 11
}).setView([-36.675, -73.543], 5); // Centrado un poco al mar

// 2. CAPAS DEL MAPA
// Capa Base (Océano)
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}', { 
    attribution: 'Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA, CHS, OSU, UNH, CSUMB, National Geographic, DeLorme, NAVTEQ and Esri',
    maxZoom: 13
}).addTo(map);

// Capa de Etiquetas (Labels transparentes)
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Reference/MapServer/tile/{z}/{y}/{x}', {
    pane: 'shadowPane', // Truco para que las letras queden sutiles sobre los marcadores
    opacity: 0.7
}).addTo(map);

// Marcador Fijo en Talcahuano
L.marker([-36.7167, -73.1167]).addTo(map)
    .bindPopup('<b>Base Talcahuano</b><br>Centro de Monitoreo.');


// 3. CARGAR DATOS (Puntos)
function cargarMapa() {
    // Usamos API_URL para evitar errores de ruta relativa
    fetch(`${API_URL}/api/v1/mediciones`)
        .then(res => res.json())
        .then(data => {
            if (data.datos) {
                // Limpiamos capas anteriores si es necesario (opcional)
                // layerGroup.clearLayers(); 

                data.datos.forEach(d => {
                    // Verificamos que existan coordenadas
                    if (d.coords && d.coords.lat) {
                        let color = d.nivel_alerta === 'Critico' ? '#D32F2F' : '#1976D2';
                        
                        L.circleMarker([d.coords.lat, d.coords.lng], {
                            color: color, 
                            fillColor: color, 
                            fillOpacity: 0.7, 
                            radius: 10
                        }).addTo(map).bindPopup(`
                            <div style="text-align:center;">
                                <strong style="color:${color}">Zona ${d.nivel_alerta}</strong><hr>
                                Temp: <b>${d.temperatura}°C</b>
                            </div>
                        `);
                    }
                });
            }
        })
        .catch(err => console.log("Esperando servidor...", err));
}

// 4. FUNCIONES DE VENTANAS (MODALS)
window.abrirModal = function() { document.getElementById('modal-ingreso').style.display = 'flex'; }
window.cerrarModal = function() { document.getElementById('modal-ingreso').style.display = 'none'; }

window.abrirRegistro = function() { document.getElementById('modal-registro').style.display = 'flex'; }
window.cerrarRegistro = function() { document.getElementById('modal-registro').style.display = 'none'; }

window.verBitacora = function() { alert("Consulta de Bitácora en desarrollo..."); }

// 5. FUNCIONES DE USUARIO
window.loginReal = function() {
    // NOTA: Si prefieres usar SweetAlert en lugar de prompt, cámbialo aquí.
    let email = prompt(" Usuario:");
    if(!email) return;
    let pass = prompt(" Contraseña:");
    if(!pass) return;

    fetch(`${API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ email: email, password: pass })
    })
    .then(res => res.json())
    .then(data => {
        if(data.exito || data.success) { // Aceptamos ambos por compatibilidad
            // Ocultar botones de acceso
            document.getElementById('panel-botones').style.display = 'none';
            
            // Mostrar info usuario
            const panelUser = document.getElementById('panel-usuario');
            if(panelUser) panelUser.style.display = 'block';
            
            // Actualizar nombre
            const lblUser = document.getElementById('lbl-usuario'); // Ajustado al HTML anterior
            if(lblUser) lblUser.innerText = "Usuario: " + (data.rol || "Investigador");
            
            alert("Bienvenido/a.");
        } else {
            alert("❌ Error de credenciales.");
        }
    })
    .catch(e => alert("Error conectando al servidor"));
}

window.cerrarSesion = function() {
    location.reload(); // Es lo más seguro para limpiar todo
}

// 6. GUARDAR DATOS
window.guardarDato = function() { // Renombrado a guardarDato para coincidir con el HTML
    let lat = parseFloat(document.getElementById('lat').value);
    let lng = parseFloat(document.getElementById('lng').value);
    let temp = parseFloat(document.getElementById('temp').value);
    let alerta = document
}