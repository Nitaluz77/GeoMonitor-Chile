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


PUERTO = int(os.environ.get("PORT", 3000))

class GeoChileHandler(http.server.SimpleHTTPRequestHandler):

    def obtener_conexion(self):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except Exception as e:
            print("❌ DB Error:", e)
            return None

    def responder_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))
    
    def do_GET(self):
        if self.path == "/" or self.path.endswith((".html", ".css", ".js", ".png", ".jpg", ".ico")):
            if self.path == "/":
                self.path = "/index.html"
            return super().do_GET()

        conn = self.obtener_conexion()

        if self.path == "/api/v1/mediciones":
            datos = []
            if conn:
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
                cur.execute("spl")
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
                conn.close()
            return self.responder_json({"datos": datos})

        self.send_error(404)
    
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8"))

            conn = self.obtener_conexion()

            if self.path == "/api/v1/auth/login":
                cur = conn.cursor()
                cur.execute(
                    "SELECT password, id_rol FROM usuario WHERE email=%s",
                    (body.get("email"),)
                )
                user = cur.fetchone()
                conn.close()

                if not user:
                    return self.responder_json({"exito": False})

                if body.get("password") != user[0]:
                    return self.responder_json({"exito": False})

                return self.responder_json({"exito": True})
                    # CONSULTA POR PUNTO (SONDA VIRTUAL)
            elif self.path == '/api/v1/consulta-punto':
                if not conn:
                 self.responder_json({"encontrado": False})
                return

            lat = body.get('lat')
            lng = body.get('lng')

            if lat is None or lng is None:
                self.responder_json({"encontrado": False})
                return

            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT 
                        d.temperatura,
                        d.salinidad,
                        d.corriente_u,
                        d.corriente_v,
                        z.latitud_centro,
                        z.longitud_centro
                    FROM datos_fisicos d
                    JOIN zona_marina z ON d.id_zona = z.id_zona
                    ORDER BY
                        POWER(z.latitud_centro - %s, 2) +
                        POWER(z.longitud_centro - %s, 2)
                    ASC
                    LIMIT 1
                """, (lat, lng))

                r = cur.fetchone()
                conn.close()

                if not r:
                    self.responder_json({"encontrado": False})
                    return

                u, v = float(r[2] or 0), float(r[3] or 0)

                self.responder_json({
                    "encontrado": True,
                    "datos": {
                        "temperatura": float(r[0]),
                        "salinidad": float(r[1]),
                        "velocidad": round((u**2 + v**2) ** 0.5, 2),
                        "lat": float(r[4]),
                        "lng": float(r[5])
                    }
                })
            except Exception as e:
                print("❌ Error consulta punto:", e)
                self.responder_json({"encontrado": False})


            self.send_error(404)

        except Exception as e:
            print("🔥 ERROR:", e)
            self.responder_json({"error": "Servidor"}, 500)


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("0.0.0.0", PUERTO), GeoChileHandler)
    print(f"✅ SERVIDOR LISTO EN PUERTO {PUERTO}")
    server.serve_forever()
