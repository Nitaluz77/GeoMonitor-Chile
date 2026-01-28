import http.server
import socketserver
import json
import psycopg2
import math
import re
import os

# --- CONFIGURACIÓN ---
PUERTO = int(os.environ.get("PORT", 3000))
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

    # --- ARCHIVOS ESTÁTICOS ---
    if self.path == '/' or self.path.endswith(('.html', '.css', '.js', '.png', '.jpg', '.ico')):
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

    # --- DESDE AQUÍ ES API ---
    conn = self.obtener_conexion()

    # 1. MAPA
    if self.path == '/api/v1/mediciones':
        datos = []
        if conn:
            try:
                cur = conn.cursor()
                sql = """
                    SELECT d.temperatura, d.salinidad, d.corriente_u, d.corriente_v, d.nivel_mar, 
                           z.latitud_centro, z.longitud_centro, b.clorofila, b.oxigeno_disuelto
                    FROM datos_fisicos d
                    JOIN zona_marina z ON d.id_zona = z.id_zona
                    LEFT JOIN datos_bio b ON d.id_zona = b.id_zona 
                       AND d.fecha_medicion = b.fecha_medicion
                    ORDER BY d.fecha_medicion DESC
                    LIMIT 100
                """
                cur.execute(sql)
                for r in cur.fetchall():
                    u, v = float(r[2] or 0), float(r[3] or 0)
                    datos.append({
                        "coords": {"lat": float(r[5]), "lng": float(r[6])},
                        "temperatura": float(r[0]),
                        "salinidad": float(r[1]),
                        "velocidad": round((u**2 + v**2) ** 0.5, 2),
                        "altura": float(r[4] or 0),
                        "clorofila": float(r[7]) if r[7] else 0.0,
                        "oxigeno": float(r[8]) if r[8] else 0.0
                    })
            except Exception as e:
                print(e)
            finally:
                conn.close()

        return self.responder_json({"datos": datos})

    # 2. BITÁCORA
    elif self.path == '/api/v1/bitacora-completa':
        respuesta = {"fisicos": [], "biologicos": []}
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT fecha_medicion, temperatura, salinidad,
                           corriente_u, corriente_v, nivel_mar
                    FROM datos_fisicos
                    ORDER BY fecha_medicion DESC
                    LIMIT 20
                """)
                for r in cur.fetchall():
                    respuesta["fisicos"].append({
                        "fecha": r[0], "temp": r[1],
                        "salinidad": r[2], "u": r[3],
                        "v": r[4], "nivel_mar": r[5]
                    })

                cur.execute("""
                    SELECT fecha_medicion, clorofila, oxigeno_disuelto
                    FROM datos_bio
                    ORDER BY fecha_medicion DESC
                    LIMIT 20
                """)
                for r in cur.fetchall():
                    respuesta["biologicos"].append({
                        "fecha": r[0],
                        "clorofila": r[1],
                        "oxigeno": r[2]
                    })
            except Exception as e:
                print(e)
            finally:
                conn.close()

        return self.responder_json(respuesta)

    # 3. USUARIOS
    elif self.path == '/api/v1/usuarios':
        lista = []
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id_usuario, nombre, email, id_rol
                    FROM usuario
                    ORDER BY id_usuario ASC
                """)
                for r in cur.fetchall():
                    lista.append({
                        "id": r[0], "nombre": r[1],
                        "email": r[2], "id_rol": r[3]
                    })
            except Exception as e:
                print(e)
            finally:
                conn.close()

        return self.responder_json({"usuarios": lista})

    # --- RUTA NO ENCONTRADA ---
    self.send_error(404, "Ruta no encontrada")


def do_POST(self):
    try:
        content_length = int(self.headers.get('Content-Length', 0))
        raw_body = self.rfile.read(content_length).decode('utf-8')
        body = json.loads(raw_body) if raw_body else {}

        # A) LOGIN
        if self.path == '/api/v1/auth/login':
            conn = self.obtener_conexion()
            if not conn:
                self.responder_json({"exito": False, "error": "DB no disponible"})
                return

            cur = conn.cursor()
            cur.execute(
                "SELECT password, id_rol FROM usuario WHERE email=%s",
                (body.get('email'),)
            )
            user = cur.fetchone()
            conn.close()

            if not user:
                self.responder_json({"exito": False})
                return

            password_db, id_rol = user

            if str(body.get('password')) != str(password_db):
                self.responder_json({"exito": False})
                return

            roles = {1: "Admin", 2: "Investigador", 3: "Lector"}

            self.responder_json({
                "exito": True,
                "rol": roles.get(id_rol, "Invitado")
            })
            return

        # B)INGRESO MANUAL
        elif self.path == '/api/v1/ingreso-manual':
            conn = self.obtener_conexion()
            if not conn:
                self.responder_json({"exito": False})
                return

            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO datos_fisicos 
                (temperatura, salinidad, corriente_u, corriente_v, nivel_mar, id_zona, fecha_medicion)
                VALUES (%s,%s,%s,%s,%s,1,NOW())
                """,
                (
                    body.get('temperatura'),
                    body.get('salinidad'),
                    body.get('u'),
                    body.get('v'),
                    body.get('altura')
                )
            )

            if body.get('clorofila'):
                cur.execute(
                    """
                    INSERT INTO datos_bio 
                    (clorofila, oxigeno_disuelto, id_zona, fecha_medicion)
                    VALUES (%s,%s,1,NOW())
                    """,
                    (body.get('clorofila'), body.get('oxigeno'))
                )

            conn.commit()
            conn.close()
            self.responder_json({"exito": True})
            return

        # C) CREAR USUARIO
        elif self.path == '/api/v1/usuarios':
            conn = self.obtener_conexion()
            if not conn:
                self.responder_json({"exito": False})
                return

            cur = conn.cursor()
            cur.execute(
                "INSERT INTO usuario (nombre, email, password, id_rol) VALUES (%s,%s,%s,%s)",
                (
                    body.get('nombre'),
                    body.get('email'),
                    body.get('password'),
                    body.get('id_rol')
                )
            )
            conn.commit()
            conn.close()
            self.responder_json({"exito": True})
            return

        # D) RUTA NO EXISTE
        self.send_response(404)
        self.end_headers()

    except Exception as e:
        print("ERROR POST:", e)
        self.responder_json({"exito": False, "error": "Error servidor"}, 500)

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
    import os
    socketserver.TCPServer.allow_reuse_address = True

    PUERTO = int(os.environ.get("PORT", 3000))
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    server = socketserver.TCPServer(("0.0.0.0", PUERTO), GeoChileHandler)
    print(f"✅ SERVIDOR LISTO EN PUERTO {PUERTO}")
    server.serve_forever()
