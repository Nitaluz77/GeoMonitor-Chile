import http.server
import socketserver
import json
import psycopg2
import math

# --- CONFIGURACIÓN ---
PUERTO = 3000
DB_CONFIG = { 
    "dbname": "geochile_db", 
    "user": "postgres", 
    "password": "Camycata", 
    "host": "localhost", 
    "port": "5432" 
}

class GeoChileHandler(http.server.SimpleHTTPRequestHandler):

    def obtener_conexion(self):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except Exception as e:
            print(f"❌ Error DB: {e}")
            return None

    def responder_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))

    def do_GET(self):
        # 1. MAPA (Solo datos físicos recientes para visualización)
        if self.path == '/api/v1/mediciones':
            conn = self.obtener_conexion()
            datos = []
            if conn:
                try:
                    cur = conn.cursor()
                    sql = """SELECT temperatura, salinidad, corriente_u, corriente_v, 
                             id_zona FROM datos_fisicos ORDER BY fecha_medicion DESC LIMIT 100"""
                    cur.execute(sql)
                    for r in cur.fetchall():
                        u, v = float(r[2] or 0), float(r[3] or 0)
                        vel = math.sqrt(u**2 + v**2)
                        # Coordenadas fijas de la zona para el mapa
                        datos.append({
                            "coords": {"lat": -36.68, "lng": -73.03}, 
                            "temperatura": r[0], "salinidad": r[1], 
                            "velocidad": round(vel, 2), "altura": 0
                        })
                except: pass
                finally: conn.close()
            self.responder_json({"datos": datos})

        # 2. BITÁCORA DOBLE (FÍSICA + BIOLÓGICA) - ¡NUEVO!
        elif self.path == '/api/v1/bitacora-completa':
            conn = self.obtener_conexion()
            respuesta = {"fisicos": [], "biologicos": []}
            
            if conn:
                try:
                    cur = conn.cursor()
                    
                    # A) Traer Tabla Física (Tope 30)
                    cur.execute("""
                        SELECT fecha_medicion, temperatura, salinidad, corriente_u, corriente_v, nivel_mar 
                        FROM datos_fisicos ORDER BY fecha_medicion DESC LIMIT 30
                    """)
                    columnas_fis = ["fecha", "temp", "salinidad", "u", "v", "nivel_mar"]
                    respuesta["fisicos"] = [dict(zip(columnas_fis, row)) for row in cur.fetchall()]

                    # B) Traer Tabla Biológica (Tope 30)
                    cur.execute("""
                        SELECT fecha_medicion, clorofila, oxigeno_disuelto 
                        FROM datos_bio ORDER BY fecha_medicion DESC LIMIT 30
                    """)
                    columnas_bio = ["fecha", "clorofila", "oxigeno"]
                    respuesta["biologicos"] = [dict(zip(columnas_bio, row)) for row in cur.fetchall()]
                    
                except Exception as e:
                    print(f"Error bitácora: {e}")
                finally:
                    conn.close()
            
            self.responder_json(respuesta)

        # 3. Archivos estáticos
        else:
            if self.path == '/': self.path = '/index.html'
            try: super().do_GET()
            except: pass

    def do_POST(self):
        try:
            length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(length).decode('utf-8'))

            # A) LOGIN
            if self.path == '/api/v1/auth/login':
                # ... (Código de login igual al anterior) ...
                conn = self.obtener_conexion()
                if conn:
                    cur = conn.cursor()
                    cur.execute("SELECT u.password, r.nombre_rol FROM usuario u JOIN rol r ON u.id_rol=r.id_rol WHERE email=%s", (body.get('email'),))
                    user = cur.fetchone()
                    conn.close()
                    if user and body.get('password') == user[0]:
                        self.responder_json({"exito": True, "rol": user[1]})
                    else:
                        self.responder_json({"exito": False})
                else: self.responder_json({"exito": False})

            # B) GUARDAR DATOS (¡AHORA GUARDA EN LAS DOS TABLAS!)
            elif self.path == '/api/v1/ingreso-manual':
                print(f"📝 Guardando: {body}")
                conn = self.obtener_conexion()
                if conn:
                    try:
                        cur = conn.cursor()
                        # 1. Insertar en FÍSICOS
                        sql_fis = """INSERT INTO datos_fisicos (temperatura, salinidad, corriente_u, corriente_v, nivel_mar, id_zona, fecha_medicion) 
                                     VALUES (%s, %s, %s, %s, %s, 1, NOW())"""
                        cur.execute(sql_fis, (body.get('temperatura'), body.get('salinidad'), body.get('u',0), body.get('v',0), body.get('altura',0)))
                        
                        # 2. Insertar en BIOLÓGICOS (Si hay datos)
                        if body.get('clorofila') or body.get('oxigeno'):
                            sql_bio = """INSERT INTO datos_bio (clorofila, oxigeno_disuelto, id_zona, fecha_medicion) 
                                         VALUES (%s, %s, 1, NOW())"""
                            cur.execute(sql_bio, (body.get('clorofila',0), body.get('oxigeno',0)))
                        
                        conn.commit()
                        self.responder_json({"mensaje": "OK"}, 201)
                    except Exception as e:
                        print(f"❌ Error: {e}")
                        conn.rollback()
                        self.responder_json({"error": str(e)}, 500)
                    finally:
                        conn.close()

            # C) Sonda Virtual
            elif self.path == '/api/v1/consulta-punto':
                self.responder_json({"encontrado": True, "datos": {"temperatura": 14.2, "salinidad": 33.5, "velocidad": 0.5, "nivel_alerta": 1}})

        except Exception as e:
            self.responder_json({"error": "Error interno"}, 500)

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("", PUERTO), GeoChileHandler)
    print(f"✅ SERVIDOR LISTO EN PUERTO {PUERTO}")
    try: server.serve_forever()
    except: pass