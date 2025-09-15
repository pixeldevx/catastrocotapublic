import geopandas as gpd
from sqlalchemy import create_engine, URL
import os

# --- 1. CONFIGURACIÓN (MÉTODO ROBUSTO) ---
# Ruta a tu archivo shapefile
SHAPEFILE_PATH = "/Users/pixel/Downloads/construcciones.shp"
TABLE_NAME = "edificios"

# Define los parámetros de conexión por separado
# ¡Reemplaza estos valores con los de tu proyecto de Supabase!
db_params = {
    'drivername': 'postgresql+psycopg2',
    'username': 'postgres.kbcwpzwhnlscogiglthk', 
    'password': 'cristianpixel01@',
    'host': 'aws-0-sa-east-1.pooler.supabase.com',
    'port': '6543',
    'database': 'postgres'
}

# SQLAlchemy construirá la URL de forma segura por nosotros
db_url = URL.create(**db_params)

# --- 2. LEER EL SHAPEFILE (sin cambios) ---
print(f"Leyendo el shapefile desde: {SHAPEFILE_PATH}")
gdf = gpd.read_file(SHAPEFILE_PATH)
# ... (el resto del código para preparar los datos es el mismo) ...
gdf.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in gdf.columns]
if gdf.crs.to_epsg() != 4326:
    gdf = gdf.to_crs(epsg=4326)

# --- 3. CONECTAR Y SUBIR A SUPABASE (usando la nueva configuración) ---
print("Creando conexión segura con la base de datos de Supabase...")
try:
    # Creamos el motor de conexión a partir de la URL segura
    engine = create_engine(db_url)
    
    print(f"Conexión exitosa. Subiendo datos a la tabla '{TABLE_NAME}'...")
    
    gdf.to_postgis(
        name=TABLE_NAME, 
        con=engine, 
        if_exists="replace", 
        index=False 
    )
    
    print("¡Éxito! Los datos del shapefile se han subido a Supabase.")
    
except Exception as e:
    print(f"Ocurrió un error durante la conexión o la subida de datos: {e}")