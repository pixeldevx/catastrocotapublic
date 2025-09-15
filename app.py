import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
import json
from streamlit_supabase_connection import SupabaseConnection

# --- Configuración de la página ---
st.set_page_config(layout="wide", page_title="Visor 3D de Edificios")
st.title("🏙️ Visor 3D de Edificios desde Supabase")

# --- Conexión y carga de datos ---
@st.cache_data
def load_data():
    # Inicializa la conexión con Supabase usando los secretos
    conn = st.connection("supabase", type=SupabaseConnection)
    
    # Consulta para traer los polígonos como GeoJSON y el número de pisos
    # ST_AsGeoJSON convierte el tipo 'geometry' a un texto JSON que GeoPandas entiende
    query = conn.query("pisos, geometria:geometria", table="edificios", ttl=600).select("pisos", geometria=f"geometria:geojson").execute()

    # Los datos vienen en una lista de diccionarios
    df = pd.DataFrame(query.data)

    # El GeoJSON viene como un string, hay que convertirlo
    df['geometry'] = df['geometria'].apply(lambda x: gpd.GeoSeries.from_geojson(json.dumps(x)).iloc[0])

    # Convertir el DataFrame de Pandas a un GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry='geometry')

    # Si tus geometrías no están en WGS84, conviértelas
    gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    
    return gdf

data = load_data()

if not data.empty:
    # --- Procesamiento para visualización ---
    # Calcular la altura real (ej: 3 metros por piso)
    data['altura_metros'] = data['total_piso'] * 3

    # --- Configuración del mapa 3D con Pydeck ---
    st.subheader("Mapa Interactivo 3D")

    # Define el punto de vista inicial del mapa
    initial_view_state = pdk.ViewState(
        latitude=data.unary_union.centroid.y,
        longitude=data.unary_union.centroid.x,
        zoom=15,
        pitch=50, # Ángulo para la vista 3D
        bearing=0
    )

    # Define la capa de polígonos extruidos
    polygon_layer = pdk.Layer(
        "PolygonLayer",
        data=data,
        id="edificios",
        get_polygon="geometry.coordinates",
        filled=True,
        stroked=True,
        get_elevation="altura_metros",  # La columna que define la altura
        elevation_scale=1,
        get_fill_color="[200, 30, 0, 160]", # Color RGBA
        get_line_color=[255, 255, 255],
        pickable=True, # Permite interactuar con los polígonos
        extruded=True, # ¡Esta es la opción clave para la extrusión 3D!
    )

    # Crea el objeto Deck (el mapa)
    r = pdk.Deck(
        layers=[polygon_layer],
        initial_view_state=initial_view_state,
        map_style="mapbox://styles/mapbox/light-v9",
        tooltip={"text": "Pisos: {pisos}"} # Muestra el número de pisos al pasar el mouse
    )

    # Muestra el mapa en Streamlit
    st.pydeck_chart(r)

    # Muestra la tabla de datos como referencia
    st.subheader("Datos de los Edificios")
    st.dataframe(data[['pisos', 'altura_metros']])
else:
    st.warning("No se encontraron datos de edificios en la base de datos.")