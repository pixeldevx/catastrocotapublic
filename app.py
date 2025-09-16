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
    # --- Limpieza de Geometrías ---
    data = data[~data.geometry.is_empty & data.geometry.notna()]
    data['geometry'] = data.geometry.buffer(0)

    # Si después de la limpieza aún hay datos, procede a visualizarlos.
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
        
        # ¡NUEVO! Condicional para asegurar que cada edificio tenga al menos 1 piso.
        # Esto crea una nueva columna 'pisos_visibles' para no alterar los datos originales.
        data['pisos_visibles'] = data['total_piso'].apply(lambda x: 1 if x == 0 else x)
        
        # El cálculo de la altura ahora usa la nueva columna.
        data['altura_metros'] = data['pisos_visibles'] * 3

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
            get_elevation="altura_metros", # Usa la altura calculada
            elevation_scale=1,
            get_fill_color="[200, 30, 0, 160]",
            get_line_color=[255, 255, 255],
            pickable=True,
            extruded=True,
        )

        # Adapta el tooltip para mostrar el número de pisos real y el visible
        r = pdk.Deck(
            layers=[polygon_layer],
            initial_view_state=initial_view_state,
            map_style=map_style_options[selected_style],
            tooltip={"html": "<b>Pisos originales:</b> {total_piso} <br/> <b>Pisos visualizados:</b> {pisos_visibles}"}
        )

        st.pydeck_chart(r)
    else:
        st.warning("No quedaron geometrías válidas después de la limpieza.")
else:
    st.warning("No se encontraron datos de edificios o hubo un error en la conexión.")