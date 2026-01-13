import copernicusmarine
import os
from datetime import date, timedelta

# --- 1. CREDENCIALES ---
USUARIO = "tu_usuario"   # <--- ¡OJO! Reemplaza esto con tu usuario real
PASSWORD = "tu_password" # <--- ¡OJO! Reemplaza esto con tu contraseña real

# --- 2. FECHAS Y RUTA ---
fecha_hoy = date.today().strftime("%Y-%m-%d")
fecha_mañana = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
CARPETA_ACTUAL = os.getcwd()

print(f"📍 Guardando archivos en: {CARPETA_ACTUAL}")

def descargar_datos():
    try:
        # --- A. FÍSICA (Sin filtrar variables para evitar error) ---
        print("\n⬇️ Descargando FÍSICA (Todo el paquete)...")
        copernicusmarine.subset(
            dataset_id="cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
            # variables=["thetao", "so", ...], <--- BORRADO PARA EVITAR ERROR
            minimum_longitude=-85.0, maximum_longitude=-68.0,
            minimum_latitude=-58.0, maximum_latitude=-17.0,
            start_datetime=f"{fecha_hoy}T00:00:00",
            end_datetime=f"{fecha_mañana}T23:59:59",
            minimum_depth=0, maximum_depth=1,
            output_filename="fisica_chile.nc",
            output_directory=CARPETA_ACTUAL,
            overwrite_output_data=True, # <--- Nuevo comando
            username=USUARIO,
            password=PASSWORD
        )

        # --- B. BIOLOGÍA (Usando dataset de Pronóstico/Forecast) ---
        print("\n⬇️ Descargando BIOLOGÍA (Todo el paquete)...")
        copernicusmarine.subset(
            dataset_id="cmems_mod_glo_bgc_anfc_0.25deg_P1D-m", # <--- CAMBIADO A ANFC (Pronóstico)
            # variables=["chl", "o2"], <--- BORRADO PARA EVITAR ERROR
            minimum_longitude=-85.0, maximum_longitude=-68.0,
            minimum_latitude=-58.0, maximum_latitude=-17.0,
            start_datetime=f"{fecha_hoy}T00:00:00",
            end_datetime=f"{fecha_mañana}T23:59:59",
            minimum_depth=0, maximum_depth=1,
            output_filename="biologia_chile.nc",
            output_directory=CARPETA_ACTUAL,
            overwrite_output_data=True,
            username=USUARIO,
            password=PASSWORD
        )

        print("\n✅ ¡LISTO! Archivos descargados correctamente.")
    
    except Exception as e:
        print("\n❌ HUBO UN ERROR:")
        print(e)

if __name__ == "__main__":
    descargar_datos()