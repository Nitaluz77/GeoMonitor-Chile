# server.py - VERSIÓN FINAL CORREGIDA
from http.server import SimpleHTTPRequestHandler, HTTPServer
import json
import os

# --- 1. CONFIGURACIÓN ---
PUERTO = 3000  # <--- CAMBIADO A 3000 PARA COINCIDIR CON TU JS

DB_CONFIG = {
    "dbname": "geochile_db",
    "user": "postgres",     
    "password": "Camycata", # Asegúrate que esta sea tu clave real de Postgres
    "host": "localhost",
    "port": "5432"
}

# Variable para saber si tenemos conexión
TIENE_BD = False
try:
    import psycopg2
    TIENE_BD = True
    print("✅ Librería psycopg2 detectada.")
except ImportError:
    print("⚠️ AVISO: Librería 'psycopg2' no instalada. Usando MODO RESPALDO (Memoria).")

# Memoria de Respaldo (Por si falla la BD)
MEMORIA_RESPALDO = [
    {"coords": {"lat": -36.6, "lng": -73.1}, "temperatura": 14.2, "nivel_alerta": "Normal"},
    {"coords": {"lat": -36.7, "lng": -73.2}, "temperatura": 18.5, "nivel_alerta": "Critico"}
]

class GeoChileHandler(SimpleHTTPRequestHandler):

    # Conexión segura a BD
    def obtener_conexion(self):
        if not TIENE_BD: return None
        try:
            return psycopg2.connect(**DB_CONFIG)
        except Exception as e:
            print(f"Error Conexión BD: {e}")
            return None

    def responder_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') # Permite conexiones externas
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))

    # --- PETICIONES GET (Ver cosas) ---
    def do_GET(self):
        # A. API: Datos del mapa
        if self.path == '/api/v1/mediciones':
            conn = self.obtener_conexion()
            datos = []
            
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT latitud, longitud, temperatura, nivel_alerta FROM t_medicion")
                    rows = cur.fetchall()
                    for r in rows:
                        datos.append({
                            "coords": {"lat": float(r[0]), "lng": float(r[1])},
                            "temperatura": float(r[2]),
                            "nivel_alerta": r[3]
                        })
                    conn.close()
                    print("📡 Enviando datos desde PostgreSQL")
                except:
                    print("⚠️ Error leyendo BD, usando respaldo")
                    datos = MEMORIA_RESPALDO
            else:
                datos = MEMORIA_RESPALDO
            
            self.responder_json({"datos": datos})
        
        # B. WEB: Servir archivos (HTML, CSS, JS)
        else:
            # Esto busca el archivo index.html si entras a la raíz
            if self.path == '/':
                self.path = '/index.html'
            return SimpleHTTPRequestHandler.do_GET(self)

    # --- PETICIONES POST (Guardar cosas) ---
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(length))

        # 1. INGRESO MANUAL
        if self.path == '/api/v1/ingreso-manual':
            conn = self.obtener_conexion()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO t_medicion (latitud, longitud, temperatura, nivel_alerta) VALUES (%s, %s, %s, %s)",
                        (body['coords']['lat'], body['coords']['lng'], body['temperatura'], body['nivel_alerta'])
                    )
                    conn.commit()
                    conn.close()
                    self.responder_json({"mensaje": "Guardado OK"}, 201)
                except Exception as e:
                    self.responder_json({"error": str(e)}, 500)
            else:
                # Guardar en memoria temporal
                MEMORIA_RESPALDO.append({
                    "coords": body['coords'],
                    "temperatura": body['temperatura'],
                    "nivel_alerta": body['nivel_alerta']
                })
                print("💾 Guardado en MEMORIA TEMPORAL (Sin BD)")
                self.responder_json({"mensaje": "Guardado en Memoria"}, 201)

        # 2. LOGIN REAL
        elif self.path == '/api/v1/auth/login':
            email = body.get('email')
            password = body.get('password')
            conn = self.obtener_conexion()
            
            usuario_encontrado = None

            if conn:
                try:
                    cur = conn.cursor()
                    # Nota: En producción las contraseñas deben ir encriptadas (hash)
                    cur.execute("SELECT rol FROM t_usuario WHERE email = %s AND password_hash = %s", (email, password))
                    row = cur.fetchone()
                    conn.close()
                    if row: usuario_encontrado = row[0]
                except:
                    pass
            
            # Respaldo Hardcoded (por si no hay usuarios en la BD aún)
            if not usuario_encontrado:
                if email == "admin@geochile.cl" and password == "1234":
                    usuario_encontrado = "Admin Maestro"

            if usuario_encontrado:
                self.responder_json({"exito": True, "rol": usuario_encontrado})
            else:
                self.responder_json({"exito": False, "mensaje": "Credenciales incorrectas"})

        # 3. REGISTRO
        elif self.path == '/api/v1/auth/register':
            email = body.get('email')
            password = body.get('password')
            conn = self.obtener_conexion()
            
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO t_usuario (email, password_hash, rol) VALUES (%s, %s, 'Investigador')", (email, password))
                    conn.commit()
                    conn.close()
                    self.responder_json({"mensaje": "Usuario Creado"}, 201)
                except Exception as e:
                    print(e)
                    self.responder_json({"error": "Error al crear"}, 400)
            else:
                 self.responder_json({"error": "Sin conexión a BD"}, 500)

if __name__ == "__main__":
    print(f"🚀 GEOCHILE MONITOR ACTIVO")
    print(f"🌍 Abre tu navegador en: http://localhost:{PUERTO}")
    server = HTTPServer(('localhost', PUERTO), GeoChileHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass