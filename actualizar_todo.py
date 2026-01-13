import descargar_copernicus
import etl_copernicus
import time

print("--- INICIANDO ACTUALIZACIÓN GEOCHILE ---")

# 1. Ejecutar la descarga
print("\n1. Conectando con Satélites Copernicus...")
descargar_copernicus.descargar_datos()

# 2. Esperar un segundo por seguridad
time.sleep(2)

# 3. Ejecutar el procesado
print("\n2. Guardando en Base de Datos...")
etl_copernicus.procesar_copernicus()

print("\n🎉 ¡SISTEMA ACTUALIZADO! Refresca tu página web.")