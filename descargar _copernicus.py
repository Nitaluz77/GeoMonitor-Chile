import copernicusmarine
import os
from datetime import date, timedelta

USUARIO = "nitaluz77@hotmail.com"  
PASSWORD = "CamilaCata1@" 

# --- FECHAS ---
fecha_hoy = date.today().strftime("%Y-%m-%d")
fecha_mañana = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

# --- OBTENER LA RUTA EXACTA DONDE ESTAMOS ---
CARPETA_ACTUAL = os.getcwd() 

print(f"📍 Vamos a guardar los archivos en: {CARPETA_ACTUAL}")

def descargar_datos():
    # 1. FÍSICA
    print("\n⬇️ Descargando FÍSICA...")
    copernicusmarine.subset(
        dataset_id="cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
        variables=["thetao", "so", "zos", "uo", "vo"],
        minimum_longitude=-85.0, maximum_longitude=-68.0,
        minimum_latitude=-58.0, maximum_latitude=-17.0,
        start_datetime=f"{fecha_hoy}T00:00:00",
        end_datetime=f"{fecha_mañana}T23:59:59",
        minimum_depth=0, maximum_depth=1,
        output_filename="fisica_chile.nc",
        output_directory=CARPETA_ACTUAL, 
        force_download=True,
        username=USUARIO,
        password=PASSWORD
    )

    # 2. BIOLOGÍA
    print("\n⬇️ Descargando BIOLOGÍA...")
    copernicusmarine.subset(
        dataset_id="cmems_mod_glo_bgc_my_0.25deg_P1D-m",
        variables=["chl", "o2"],
        minimum_longitude=-85.0, maximum_longitude=-68.0,
        minimum_latitude=-58.0, maximum_latitude=-17.0,
        start_datetime=f"{fecha_hoy}T00:00:00",
        end_datetime=f"{fecha_mañana}T23:59:59",
        minimum_depth=0, maximum_depth=1,
        output_filename="biologia_chile.nc",
        output_directory=CARPETA_ACTUAL, 
        force_download=True,
        username=USUARIO,
        password=PASSWORD
    )

    print("\n✅ ¡LISTO!")
    print(f"Busca este archivo: {os.path.join(CARPETA_ACTUAL, 'fisica_chile.nc')}")

if __name__ == "__main__":
    descargar_datos()