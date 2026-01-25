import copernicusmarine

print("🔍 RADIOGRAFÍA DEL SATÉLITE BIOLÓGICO...")
metadata = copernicusmarine.describe(
    dataset_id="cmems_mod_glo_bgc_anfc_0.25deg_P1D-m"
)

# Imprimimos la fecha más reciente y la profundidad real
print(f"👉 Fecha más reciente disponible: {metadata['temporal_extent']['end_datetime']}")
print(f"👉 Profundidad superficial real: {metadata['vertical_extent']['minimum_depth']}")