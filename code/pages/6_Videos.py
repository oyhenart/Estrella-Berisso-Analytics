import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Videos", page_icon="🎬", layout="wide")

st.markdown("""
<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@st.cache_data(ttl=0)
def cargar_videos():
    return pd.read_csv(os.path.join(BASE, "data", "videos.csv"))

# --- Sidebar ---
import os as _os
_base = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_escudo = _os.path.join(_base, "static", "escudo.png")
if _os.path.exists(_escudo):
    st.sidebar.image(_escudo, width=72)
st.sidebar.markdown("""
<div style='padding: 6px 0 20px 0'>
    <div style='font-size:1.05em; font-weight:700; color:#EEEEEE; line-height:1.3'>Club Atlético<br>Estrella de Berisso</div>
    <div style='font-size:0.72em; color:#555; text-transform:uppercase; letter-spacing:2px; margin-top:3px'>La Cebra</div>
    <div style='margin: 16px 0; height:1px; background:linear-gradient(to right, #E63946, transparent)'></div>
    <div style='font-size:0.7em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:2px'>IAO Football Analytics</div>
    <div style='font-size:0.68em; color:#444; margin-top:4px; font-style:italic'>Transformo datos en decisiones.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style='margin-bottom:28px'>
    <p style='font-size:0.72em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:3px; margin:0 0 6px 0'>Multimedia</p>
    <h1 style='font-size:2em; font-weight:800; margin:0; color:#EEEEEE; letter-spacing:-0.5px'>Videos del equipo</h1>
</div>
""", unsafe_allow_html=True)

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
