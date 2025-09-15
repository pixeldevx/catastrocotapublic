import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# --- Configuración de la página ---
st.set_page_config(layout="wide", page_title="Visor 3D de Edificios")
st.title("🏙️ Visor 3D de Edificios desde Supabase")

# --- Conexión y carga de datos ---
@st.cache_data
def load_data():
    # --- ¡ESTA ES LA SECCIÓN MODIFICADA! ---
    try:
        # 1. Lee las credenciales desde los secretos de Streamlit
        creds = st.secrets["db_credentials"]
        host = creds["host"]
        dbname = creds["dbname"]
        user = creds["user"]
        password = creds["password"]
        port = creds["port"]

        # 2. Construye la URL de conexión de forma segura (codifica la contraseña)
        db_url = f"postgresql+psycopg2://{user}:{quote_plus(password)}@{host}:{port}/{dbname}"
        
        # 3. Crea el motor de conexión con SQLAlchemy
        engine = create_engine(db_url)
        
        # 4. Define la consulta SQL para obtener los datos
        sql_query = "SELECT pisos, geometria FROM edificios"
        
        # 5. Carga los datos directamente en un GeoDataFrame usando GeoPandas
        gdf = gpd.read_postgis(sql_query, engine, geom_col='geometria')
        
        return gdf

    except Exception as e:
        st.error(f"Error al conectar o cargar los datos: {e}")
        return gpd.GeoDataFrame() # Devuelve un GeoDataFrame vacío si hay error

data = load_data()

if not data.empty:
    # --- Panel de control en la barra lateral ---
    st.sidebar.header("Opciones de Visualización")
    map_style_options = {
        "Claro": "mapbox://styles/mapbox/light-v9",
        "Oscuro": "mapbox://styles/mapbox/dark-v9",
        "Calles": "mapbox://styles/mapbox/streets-v11",
        "Satélite": "mapbox://styles/mapbox/satellite-v9",
    }
    selected_style = st.sidebar.selectbox("Elige un estilo de mapa base:", list(map_style_options.keys()))

    # --- Procesamiento para visualización ---
    data['altura_metros'] = data['pisos'] * 3

    # --- Configuración del mapa 3D con Pydeck ---
    st.subheader("Mapa Interactivo 3D")

    initial_view_state = pdk.ViewState(
        latitude=data.unary_union.centroid.y,
        longitude=data.unary_union.centroid.x,
        zoom=15,
        pitch=50,
        bearing=0
    )

    polygon_layer = pdk.Layer(
        "PolygonLayer",
        data=data,
        get_polygon="geometry.coordinates",
        filled=True,
        stroked=True,
        get_elevation="altura_metros",
        elevation_scale=1,
        get_fill_color="[200, 30, 0, 160]",
        get_line_color=[255, 255, 255],
        pickable=True,
        extruded=True, 
    )

    r = pdk.Deck(
        layers=[polygon_layer],
        initial_view_state=initial_view_state,
        map_style=map_style_options[selected_style],
        tooltip={"text": "Pisos: {pisos}"}
    )

    st.pydeck_chart(r)
else:
    st.warning("No se encontraron datos de edificios o hubo un error en la conexión.")