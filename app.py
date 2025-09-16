import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# --- Configuración de la página ---
st.set_page_config(layout="wide", page_title="Visor 3D de Edificios")
st.title("🏙️ Visor 3D de Edificios desde Supabase")

@st.cache_data
def load_data():
    try:
        creds = st.secrets["db_credentials"]
        host, dbname, user, password, port = creds["host"], creds["dbname"], creds["user"], creds["password"], creds["port"]
        db_url = f"postgresql+psycopg2://{user}:{quote_plus(password)}@{host}:{port}/{dbname}"
        engine = create_engine(db_url)
        sql_query = "SELECT total_piso, geometry FROM edificios"
        gdf = gpd.read_postgis(sql_query, engine, geom_col='geometry')
        return gdf
    except Exception as e:
        st.error(f"Error al conectar o cargar los datos: {e}")
        return gpd.GeoDataFrame()

data = load_data()

if not data.empty:
    st.header("Depuración de Datos")
    
    # --- PASO 1 DE DEPURACIÓN: VERIFICAR DATOS CARGADOS ---
    st.subheader("Paso 1: ¿Se cargaron datos?")
    st.write(f"Filas encontradas después de la carga inicial: {len(data)}")
    st.dataframe(data.head())
    
    # --- Limpieza de Geometrías ---
    data = data[~data.geometry.is_empty & data.geometry.notna()]
    data['geometry'] = data.geometry.buffer(0)
    
    st.write(f"Filas restantes después de la limpieza: {len(data)}")
    
    # --- PASO 2 DE DEPURACIÓN: VERIFICAR EL CENTRO DEL MAPA ---
    st.subheader("Paso 2: ¿Dónde se está centrando el mapa?")
    if not data.empty:
        lat = data.unary_union.centroid.y
        lon = data.unary_union.centroid.x
        st.write(f"Coordenadas del centroide: Latitud={lat}, Longitud={lon}")
        
        # --- PASO 3 DE DEPURACIÓN: INSPECCIONAR COLUMNAS CLAVE ---
        st.subheader("Paso 3: ¿Son correctos los datos para la altura y la forma?")
        data['altura_metros'] = data['total_piso'] * 3
        st.dataframe(data[['total_piso', 'altura_metros', 'geometry']].head())
    
        # --- Código de visualización (sin cambios) ---
        st.header("Visualización del Mapa")
        initial_view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=15, pitch=50)
        polygon_layer = pdk.Layer(...) # El resto de tu código pydeck aquí
        
        # ... (el resto de tu código de visualización)

    else:
        st.error("No quedaron datos válidos después de la limpieza.")

else:
    st.warning("No se encontraron datos de edificios o hubo un error en la conexión.")