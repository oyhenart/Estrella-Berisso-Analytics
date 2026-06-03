import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Videos", page_icon="🎬", layout="wide")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@st.cache_data(ttl=0)
def cargar_videos():
    return pd.read_csv(os.path.join(BASE, "data", "videos.csv"))

st.title("🎬 Videos del equipo")

df = cargar_videos()

if df.empty:
    st.info("⏳ Aún no hay videos cargados. Se irán agregando partido a partido.")
    st.stop()

# --- Filtro por fecha ---
fechas = ["Todas"] + sorted(df["fecha"].unique().tolist(), key=lambda x: int(x))
fecha_sel = st.selectbox("Filtrar por fecha", fechas)

if fecha_sel != "Todas":
    df = df[df["fecha"] == int(fecha_sel)]

st.divider()

# --- Videos ---
for _, row in df.iterrows():
    st.subheader(f"Fecha {int(row['fecha'])} — {row['rival']}")
    st.caption(row["descripcion"])
    st.components.v1.iframe(
        f"https://www.youtube.com/embed/{row['youtube_id']}",
        height=450,
    )
    st.divider()