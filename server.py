# server.py - VERSIÓN MAESTRA: CIENTÍFICA + AUTH
from http.server import SimpleHTTPRequestHandler, HTTPServer
import json
import psycopg2
import math 

PUERTO = 3000 
DB_CONFIG = { 
    "dbname": "geochile_db", 
    "user": "postgres", 
    "password": "Camycata", 
    "host": "localhost", 
    "port": "5432" 
}

class GeoChileHandler(SimpleHTTPRequestHandler):

    def obtener_conexion(self):
        try: return psycopg2.connect(**DB_CONFIG)
        except: return None

    def responder_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))

    # --- GET (Archivos y Bitácora) ---
    def do_GET(self):
        if self.path == '/': 
            self.path = '/index.html'
            SimpleHTTPRequestHandler.do_GET(self)
        
        # 1. BITÁCORA (Historial)
        # 2. CARGA INICIAL DEL MAPA (Datos Masivos)
        elif self.path == '/api/v1/mediciones':
            conn = self.obtener_conexion()
            datos = []
            if conn:
                try:
                    cur = conn.cursor()
                    # AHORA PEDIMOS TODO (incluyendo u, v, altura)
                    cur.execute("""
                        SELECT latitud, longitud, temperatura, salinidad, 
                               altura_mar, corriente_u, corriente_v, clorofila, oxigeno_disuelto, nivel_alerta 
                        FROM t_medicion LIMIT 200
                    """)
                    rows = cur.fetchall()
                    for r in rows:
                        # Calculamos velocidad
                        u = float(r[5] or 0)
                        v = float(r[6] or 0)
                        vel = math.sqrt(u**2 + v**2)

                        datos.append({
                            "coords": {"lat": float(r[0]), "lng": float(r[1])},
                            "temperatura": r[2],
                            "salinidad": r[3],
                            "altura": r[4],    # Enviamos altura
                            "velocidad": vel,  # Enviamos velocidad calculada
                            "clorofila": r[7],
                            "oxigeno": r[8],
                            "nivel_alerta": r[9]
                        })
                    conn.close()
                except Exception as e: 
                    print(f"Error carga mapa: {e}")
                    datos = [] 
            self.responder_json({"datos": datos})
        
        # 2. ARCHIVOS ESTÁTICOS (CSS, JS)
        else: SimpleHTTPRequestHandler.do_GET(self)

    # --- POST (Guardar, Clics y Login) ---
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(length))

        # 1. INGRESO MANUAL CIENTÍFICO
        if self.path == '/api/v1/ingreso-manual':
            conn = self.obtener_conexion()
            if conn:
                try:
                    cur = conn.cursor()
                    sql = """
                        INSERT INTO t_medicion 
                        (latitud, longitud, temperatura, salinidad, clorofila, oxigeno_disuelto, 
                         altura_mar, corriente_u, corriente_v, nivel_alerta, fecha) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """
                    cur.execute(sql, (
                        body['coords']['lat'], body['coords']['lng'], body['temperatura'], 
                        body.get('salinidad', 0.0), body.get('clorofila', 0.0), body.get('oxigeno', 0.0),
                        body.get('altura', 0.0), 
                        body.get('u', 0.0), 
                        body.get('v', 0.0), 
                        body['nivel_alerta']
                    ))
                    conn.commit(); conn.close()
                    self.responder_json({"mensaje": "OK"}, 201)
                except Exception as e: self.responder_json({"error": str(e)}, 500)

        # 2. SONDA VIRTUAL (Clic en mapa)
        elif self.path == '/api/v1/consulta-punto':
            lat = float(body.get('lat')); lng = float(body.get('lng'))
            conn = self.obtener_conexion()
            datos = None
            if conn:
                try:
                    cur = conn.cursor()
                    sql = """
                        SELECT latitud, longitud, temperatura, salinidad, clorofila, oxigeno_disuelto, 
                               altura_mar, corriente_u, corriente_v, nivel_alerta,
                               (POWER(latitud - %s, 2) + POWER(longitud - %s, 2)) as distancia
                        FROM t_medicion ORDER BY distancia ASC LIMIT 1
                    """
                    cur.execute(sql, (lat, lng))
                    r = cur.fetchone()
                    
                    if r and r[10] < 0.25: # Filtro de distancia (aprox 25km)
                        u = float(r[7] or 0)
                        v = float(r[8] or 0)
                        velocidad = math.sqrt(u**2 + v**2)

                        datos = {
                            "coords": {"lat": float(r[0]), "lng": float(r[1])},
                            "temperatura": r[2], "salinidad": r[3], "clorofila": r[4], "oxigeno": r[5], 
                            "altura": r[6],
                            "velocidad": round(velocidad, 2),
                            "nivel_alerta": r[9]
                        }
                    conn.close()
                except Exception as e: print(e)
            
            if datos: self.responder_json({"encontrado": True, "datos": datos})
            else: self.responder_json({"encontrado": False})

        # 3. LOGIN (Recuperado)
        elif self.path == '/api/v1/auth/login':
            email = body.get('email')
            # Login simple para demostración
            if email == "admin@geochile.cl":
                self.responder_json({"exito": True, "rol": "Admin"})
            else:
                self.responder_json({"exito": True, "rol": "Investigador"})

# --- ARRANQUE ---
if __name__ == "__main__":
    try:
        server = HTTPServer(('', PUERTO), GeoChileHandler)
        print(f"🚀 GEOCHILE FULL STACK CORRIENDO EN PUERTO {PUERTO}")
        print("   (Incluye: Sonda, Ingreso Manual, Bitácora y Corrientes U/V)")
        server.serve_forever()
    except: print("Puerto ocupado.")