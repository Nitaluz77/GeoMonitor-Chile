import http.server
import socketserver
import json
import psycopg2
import math
import re

# --- CONFIGURACIÓN ---
PUERTO = 3000
DB_CONFIG = { 
    "dbname": "railway",
    "user": "postgres",
    "password": "KEkNqLjIOIcOExyUYAoHjIEtyCzHpZAM",
    "host": "nozomi.proxy.rlwy.net",
    "port": "23725"
}

class GeoChileHandler(http.server.SimpleHTTPRequestHandler):
    
    def obtener_conexion(self):
        try: return psycopg2.connect(**DB_CONFIG)
        except Exception as e: print(f"❌ DB Error: {e}"); return None

    def responder_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))

    def do_GET(self):
        conn = self.obtener_conexion()
        
        # 1. MAPA (Datos completos con Coordenadas Reales)
        if self.path == '/api/v1/mediciones':
            datos = []
            if conn:
                try:
                    cur = conn.cursor()
                    # Query Blindada
                    sql = """
                        SELECT d.temperatura, d.salinidad, d.corriente_u, d.corriente_v, d.nivel_mar, 
                               z.latitud_centro, z.longitud_centro, b.clorofila, b.oxigeno_disuelto
                        FROM datos_fisicos d
                        JOIN zona_marina z ON d.id_zona = z.id_zona
                        LEFT JOIN datos_bio b ON d.id_zona = b.id_zona AND d.fecha_medicion = b.fecha_medicion
                        ORDER BY d.fecha_medicion DESC LIMIT 100
                    """
                    cur.execute(sql)
                    for r in cur.fetchall():
                        u, v = float(r[2] or 0), float(r[3] or 0)
                        datos.append({
                            "coords": {"lat": float(r[5]), "lng": float(r[6])}, # Coordenadas de la BD
                            "temperatura": float(r[0]), 
                            "salinidad": float(r[1]), 
                            "velocidad": round(math.sqrt(u**2 + v**2), 2), 
                            "altura": float(r[4] or 0),
                            "clorofila": float(r[7]) if r[7] is not None else 0.0,
                            "oxigeno": float(r[8]) if r[8] is not None else 0.0
                        })
                except Exception as e: print(e)
                finally: conn.close()
            self.responder_json({"datos": datos})

        # 2. BITÁCORA (¡ESTO FALTABA!)
        elif self.path == '/api/v1/bitacora-completa':
            respuesta = {"fisicos": [], "biologicos": []}
            if conn:
                try:
                    cur = conn.cursor()
                    # Tabla Física
                    cur.execute("SELECT fecha_medicion, temperatura, salinidad, corriente_u, corriente_v, nivel_mar FROM datos_fisicos ORDER BY fecha_medicion DESC LIMIT 20")
                    for r in cur.fetchall():
                         respuesta["fisicos"].append({"fecha": r[0], "temp": r[1], "salinidad": r[2], "u": r[3], "v": r[4], "nivel_mar": r[5]})
                    
                    # Tabla Biológica
                    cur.execute("SELECT fecha_medicion, clorofila, oxigeno_disuelto FROM datos_bio ORDER BY fecha_medicion DESC LIMIT 20")
                    for r in cur.fetchall():
                        respuesta["biologicos"].append({"fecha": r[0], "clorofila": r[1], "oxigeno": r[2]})
                except Exception as e: print(e)
                finally: conn.close()
            self.responder_json(respuesta)

        # 3. USUARIOS
        elif self.path == '/api/v1/usuarios':
            lista = []
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT id_usuario, nombre, email, id_rol FROM usuario ORDER BY id_usuario ASC")
                    for r in cur.fetchall():
                        lista.append({"id": r[0], "nombre": r[1], "email": r[2], "id_rol": r[3]})
                except: pass
                finally: conn.close()
            self.responder_json({"usuarios": lista})

        # Archivos estáticos
        else:
            if self.path == '/': self.path = '/index.html'
            try: super().do_GET()
            except: pass

    def do_POST(self):
        try:
            length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(length).decode('utf-8'))
            conn = self.obtener_conexion()

            # LOGIN
            if self.path == '/api/v1/auth/login':
                if conn:
                    cur = conn.cursor()
                    cur.execute("SELECT password, id_rol FROM usuario WHERE email=%s", (body.get('email'),))
                    user = cur.fetchone()
                    conn.close()
                    # Convertimos ID Rol a Nombre para el Frontend
                    rol_nombre = "Invitado"
                    if user and str(body.get('password')) == str(user[0]):
                        rid = user[1]
                        if rid == 1: rol_nombre = "Admin"
                        elif rid == 2: rol_nombre = "Investigador"
                        elif rid == 3: rol_nombre = "Lector"
                        self.responder_json({"exito": True, "rol": rol_nombre})
                    else:
                        self.responder_json({"exito": False})
            
            # GUARDAR DATOS
            elif self.path == '/api/v1/ingreso-manual':
                if conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO datos_fisicos (temperatura, salinidad, corriente_u, corriente_v, nivel_mar, id_zona, fecha_medicion) VALUES (%s,%s,%s,%s,%s,1,NOW())", 
                                (body.get('temperatura'), body.get('salinidad'), body.get('u'), body.get('v'), body.get('altura')))
                    if body.get('clorofila'):
                        cur.execute("INSERT INTO datos_bio (clorofila, oxigeno_disuelto, id_zona, fecha_medicion) VALUES (%s,%s,1,NOW())", 
                                    (body.get('clorofila'), body.get('oxigeno')))
                    conn.commit()
                    conn.close()
                    self.responder_json({"exito": True})

            # CREAR USUARIO
            elif self.path == '/api/v1/usuarios':
                if conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO usuario (nombre, email, password, id_rol) VALUES (%s,%s,%s,%s)", 
                                (body.get('nombre'), body.get('email'), body.get('password'), body.get('id_rol')))
                    conn.commit()
                    conn.close()
                    self.responder_json({"exito": True})
            
            # DELETE
            elif '/api/v1/usuarios/' in self.path: 
                 pass 

        except Exception as e: self.responder_json({"error": str(e)}, 500)

    def do_DELETE(self):
        match = re.search(r'/api/v1/usuarios/(\d+)', self.path)
        if match:
            uid = match.group(1)
            conn = self.obtener_conexion()
            if conn:
                cur = conn.cursor()
                if uid == '1': self.responder_json({"exito": False, "error": "No borrar superadmin"})
                else:
                    cur.execute("DELETE FROM usuario WHERE id_usuario=%s", (uid,))
                    conn.commit()
                    self.responder_json({"exito": True})
                conn.close()

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("", PUERTO), GeoChileHandler)
    print(f"✅ SERVIDOR LISTO EN PUERTO {PUERTO}")
    server.serve_forever()