import streamlit as st
import pandas as pd
import os

from components.layout import (
    inject_css,
    render_sidebar,
    render_header
)

st.set_page_config(page_title="Videos", page_icon="🎬", layout="wide")

inject_css()

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
render_sidebar(BASE)

render_header(
    "Multimedia",
    "Videos del equipo"
)

@st.cache_data(ttl=0)
def cargar_videos():
    return pd.read_csv(os.path.join(BASE, "data", "videos.csv"))

df = cargar_videos()

if df.empty:
    st.info("⏳ Aún no hay videos cargados. Se irán agregando partido a partido.")
    st.stop()

# Ordenamos el DataFrame completo por fecha de manera descendente (Última primero)
df = df.sort_values(by="fecha", ascending=False)

# --- Filtro por fecha (Orden descendente con reverse=True) ---
fechas_unicas = sorted(df["fecha"].unique().tolist(), key=lambda x: int(x), reverse=True)
fechas = ["Todas"] + [str(f) for f in fechas_unicas]
fecha_sel = st.selectbox("Filtrar por fecha", fechas)

if fecha_sel != "Todas":
    df = df[df["fecha"] == int(fecha_sel)]

st.divider()

# --- Videos (Ya van a salir ordenados de última a primera fecha) ---
for _, row in df.iterrows():

    with st.container(border=True):

        st.subheader(
            f"Fecha {int(row['fecha'])} — {row['rival']}"
        )

        st.caption(
            row["descripcion"]
        )

        st.components.v1.iframe(
            f"https://www.youtube.com/embed/{row['youtube_id']}",
            height=450,
        )

    st.write("")
