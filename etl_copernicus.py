import copernicusmarine
import xarray as xr
import psycopg2
import os
import sys
import math
from datetime import date


# 1. CONFIGURACIÓN
USER_COP = "nitaluz77@hotmail.com"
PASS_COP = "CamilaCata1@"

DB_CONFIG = { 
    "dbname": "railway",
    "user": "postgres",
    "password": "KEkNqLjIOIcOExyUYAoHjIEtyCzHpZAM",
    "host": "nozomi.proxy.rlwy.net",
    "port": "23725"
}

PRODUCT_PHY = "cmems_mod_glo_phy_anfc_0.083deg_P1D-m"
PRODUCT_BIO = "cmems_mod_glo_bgc-nut_anfc_0.25deg_P1D-m"


# 2. RED DE MONITOREO NACIONAL (Calibrada mar adentro para satélite de 0.25°)
ZONAS = [
    {"id": 1, "nombre": "Arica", "lat": -18.50, "lon": -70.70},          # Movido 40km al Oeste
    {"id": 2, "nombre": "Iquique", "lat": -20.20, "lon": -70.50},        # Movido 35km al Oeste
    {"id": 3, "nombre": "Antofagasta", "lat": -23.65, "lon": -70.80},    # Movido 40km al Oeste
    {"id": 4, "nombre": "Caldera", "lat": -27.10, "lon": -71.20},        # Movido 40km al Oeste
    {"id": 5, "nombre": "Coquimbo", "lat": -30.00, "lon": -71.70},       # Movido 35km al Oeste
    {"id": 6, "nombre": "Valparaíso", "lat": -33.10, "lon": -72.00},     # Movido 40km al Oeste
    {"id": 7, "nombre": "San Antonio", "lat": -33.60, "lon": -72.00},    # Movido 40km al Oeste
    {"id": 8, "nombre": "Talcahuano", "lat": -36.70, "lon": -73.50},     # Movido 45km al Oeste
    {"id": 9, "nombre": "Valdivia", "lat": -39.90, "lon": -73.90},       # Movido 50km al Oeste
    {"id": 10, "nombre": "Puerto Montt", "lat": -41.70, "lon": -74.00},  # Movido al Océano Pacífico (fuera del seno)
    {"id": 11, "nombre": "Chiloé", "lat": -42.50, "lon": -74.30},        # Océano Pacífico (Cucao exterior)
    {"id": 12, "nombre": "Puerto Aysén", "lat": -45.40, "lon": -75.00},  # Mar abierto (evitando fiordos)
    {"id": 13, "nombre": "Laguna San Rafael", "lat": -47.00, "lon": -75.00}, # Golfo de Penas (Agua profunda)
    {"id": 14, "nombre": "Punta Arenas", "lat": -53.50, "lon": -72.50},  # Entrada occidental del Estrecho
    {"id": 15, "nombre": "Puerto Williams", "lat": -56.00, "lon": -67.50} # Pasaje de Drake (Mar de Hoces)
]

# 3. FUNCIONES DE BASE DE DATOS Y AYUDANTES
def conectar_db():
    try: return psycopg2.connect(**DB_CONFIG)
    except Exception as e: print(f"❌ Error DB: {e}"); return None

def buscar_variable(nombres_en_archivo, opciones):
    for op in opciones:
        if op in nombres_en_archivo: return op
    return None

# 4. MOTOR ETL (NIVEL NACIONAL)
def procesar_oceanografia():
    print("🌊 INICIANDO RED DE MONITOREO NACIONAL CHILE (15 ESTACIONES) 🌊")
    conn = conectar_db()
    if not conn: return

    from datetime import date, timedelta 

    # Fecha para la FÍSICA (Hoy)
    hoy_str = date.today().strftime("%Y-%m-%dT00:00:00")
    
    # BIOLÓGICA → última fecha válida
    DATA_MAX = "2025-11-30T00:00:00"
    ayer_str = DATA_MAX

    PROF_EXACTA = 0.4940253794193268
    for zona in ZONAS:
        print(f"\n📍 Analizando: {zona['nombre']}...")
        
        try:
            # --- FASE A: FÍSICA (CAJA DE 20KM) ---
            print("   📡 Descargando Grilla Física...")
            copernicusmarine.subset(
                dataset_id=PRODUCT_PHY,
                minimum_latitude=zona['lat'] - 0.1, maximum_latitude=zona['lat'] + 0.1,
                minimum_longitude=zona['lon'] - 0.1, maximum_longitude=zona['lon'] + 0.1,
                start_datetime=hoy_str, end_datetime=hoy_str,
                minimum_depth=PROF_EXACTA, maximum_depth=PROF_EXACTA,
                raise_if_updating=True, disable_progress_bar=True,
                output_filename="phy.nc",
                username=USER_COP, password=PASS_COP,                
            )
            
            ds_phy = xr.open_dataset("phy.nc").load()
            ds_phy.close()

            vars_phy = list(ds_phy.data_vars)
            nom_t = buscar_variable(vars_phy, ['thetao', 'to', 'temperature', 'temp'])
            nom_s = buscar_variable(vars_phy, ['so', 'sal', 'salinity'])
            nom_u = buscar_variable(vars_phy, ['uo', 'u'])
            nom_v = buscar_variable(vars_phy, ['vo', 'v'])
            nom_z = buscar_variable(vars_phy, ['zos', 'sla'])

            temp = float(ds_phy[nom_t].isel(time=0, depth=0).mean(skipna=True).item()) if nom_t else 0.0
            sal = float(ds_phy[nom_s].isel(time=0, depth=0).mean(skipna=True).item()) if nom_s else 33.0
            u = float(ds_phy[nom_u].isel(time=0, depth=0).mean(skipna=True).item()) if nom_u else 0.0
            v = float(ds_phy[nom_v].isel(time=0, depth=0).mean(skipna=True).item()) if nom_v else 0.0
            nivel = float(ds_phy[nom_z].isel(time=0).mean(skipna=True).item()) if nom_z else 0.0

            if math.isnan(temp): temp = 0.0
            if math.isnan(sal): sal = 0.0
            if math.isnan(u): u = 0.0
            if math.isnan(v): v = 0.0
            if math.isnan(nivel): nivel = 0.0

            # --- FASE B: BIOLÓGICA (CAJA DE 50KM) ---
            print("   🧬 Descargando Grilla Biológica...")
            
            copernicusmarine.subset(
                dataset_id=PRODUCT_BIO,
                minimum_latitude=zona['lat'] - 0.25, maximum_latitude=zona['lat'] + 0.25,
                minimum_longitude=zona['lon'] - 0.25, maximum_longitude=zona['lon'] + 0.25,
                start_datetime=hoy_str, end_datetime=hoy_str, 
                minimum_depth=PROF_EXACTA, maximum_depth=PROF_EXACTA,
                raise_if_updating=True, disable_progress_bar=True,
                output_filename="bio.nc",
                username=USER_COP, password=PASS_COP,                
            )

            ds_bio = xr.open_dataset("bio.nc").load()
            ds_bio.close()

            vars_bio = list(ds_bio.data_vars)
            nom_chl = buscar_variable(vars_bio, ['chl', 'chlorophyll'])
            nom_o2 = buscar_variable(vars_bio, ['o2', 'oxigen', 'dissolved_oxygen'])

            chl = float(ds_bio[nom_chl].isel(time=0, depth=0).mean(skipna=True).item()) if nom_chl else 0.0
            o2 = float(ds_bio[nom_o2].isel(time=0, depth=0).mean(skipna=True).item()) if nom_o2 else 0.0

            if math.isnan(chl): chl = 0.0
            if math.isnan(o2): o2 = 0.0

            # --- FASE C: CARGA (DATA FUSION) ---
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO datos_fisicos (temperatura, salinidad, corriente_u, corriente_v, nivel_mar, id_zona, fecha_medicion)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (temp, sal, u, v, nivel, zona['id']))
            
            cur.execute("""
                INSERT INTO datos_bio (clorofila, oxigeno_disuelto, id_zona, fecha_medicion)
                VALUES (%s, %s, %s, NOW())
            """, (chl, o2, zona['id']))

            conn.commit()
            print(f"   ✅ EXITO: T={temp:.1f}°C | S={sal:.1f} | Chl={chl:.2f} | O2={o2:.1f}")

            if os.path.exists("phy.nc"): os.remove("phy.nc")
            if os.path.exists("bio.nc"): os.remove("bio.nc")

        except Exception as e:
            print(f"   ❌ Error en {zona['nombre']}: {e}")
            conn.rollback()

    conn.close()
    print("\n🏁 FINALIZADO: Todo Chile Actualizado.")

if __name__ == "__main__":
    procesar_oceanografia()