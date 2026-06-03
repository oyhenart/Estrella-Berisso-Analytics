import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Estrella FC - Dashboard",
    page_icon="⚽",
    layout="wide",
)

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE, "data", "events_clean.csv")
FIXTURE_PATH = os.path.join(BASE, "data", "fixture.csv")

@st.cache_data
def cargar_datos():
    df = pd.read_csv(DATA_PATH)
    df["tiempo_total"] = df["Mins"] * 60 + df["Secs"]
    return df

@st.cache_data(ttl=0)
def cargar_fixture():
    return pd.read_csv(FIXTURE_PATH)

# --- Sidebar ---
st.sidebar.markdown("""
<div style='text-align:center; padding: 24px 0 16px 0'>
    <div style='font-size:2em; font-weight:900; letter-spacing:3px; color:#E63946'>IAO</div>
    <div style='font-size:0.65em; color:#666; letter-spacing:4px; text-transform:uppercase; margin-top:4px'>Football Analytics</div>
    <div style='border-top: 1px solid #E63946; margin: 14px 16px; opacity:0.3'></div>
    <div style='font-size:0.68em; color:#555; font-style:italic'>"Transformo datos en decisiones."</div>
</div>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div style='margin-bottom: 8px'>
    <span style='font-size:0.75em; letter-spacing:4px; text-transform:uppercase; color:#E63946; font-weight:600'>Torneo Promocional Amateur 2026</span>
</div>
<div style='font-size:2.2em; font-weight:900; letter-spacing:-1px; margin-bottom:24px'>
    Estrella de Berisso — Panel de análisis
</div>
""", unsafe_allow_html=True)

if not os.path.exists(DATA_PATH):
    st.markdown("""
    <div style='background:#1A1A1A; border-left: 3px solid #E63946; padding: 20px 24px; border-radius: 4px; margin-top: 16px'>
        <div style='color:#E63946; font-size:0.75em; letter-spacing:3px; text-transform:uppercase; margin-bottom:6px'>Estado</div>
        <div style='font-size:1.1em; color:#F0F0F0'>El torneo aún no comenzó. Las estadísticas estarán disponibles a partir del primer partido.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df = cargar_datos()
fixture = cargar_fixture()

# --- Filtros ---
fechas_disponibles = sorted(df["fecha"].unique().tolist())
opciones_fecha = ["Todos los partidos"] + [f"Fecha {f}" for f in fechas_disponibles]

col_f, col_c = st.columns(2)
with col_f:
    fecha_sel = st.selectbox("Partido", opciones_fecha)
with col_c:
    condicion_sel = st.selectbox("Condición", ["Local y Visitante", "Local", "Visitante"])

if fecha_sel != "Todos los partidos":
    num_fecha = int(fecha_sel.replace("Fecha ", ""))
    df_filtrado = df[df["fecha"] == num_fecha]
else:
    num_fecha = None
    df_filtrado = df.copy()

if condicion_sel != "Local y Visitante" and num_fecha is None:
    fechas_cond = fixture[fixture["condicion"] == condicion_sel]["fecha"].tolist()
    df_filtrado = df_filtrado[df_filtrado["fecha"].isin(fechas_cond)]

st.markdown("<div style='margin: 24px 0 8px 0; border-top: 1px solid #222'></div>", unsafe_allow_html=True)

# --- Métricas custom ---
total_eventos = len(df_filtrado)
total_jugadores = df_filtrado["Player"].nunique()
total_pases = len(df_filtrado[df_filtrado["Event"] == "pase"])
total_goles = len(df_filtrado[df_filtrado["Event"] == "gol"])
total_recuperaciones = len(df_filtrado[df_filtrado["Event"] == "recuperacion"])
total_remates = len(df_filtrado[df_filtrado["Event"] == "remate"])

def metric_card(label, value, accent=False):
    border = "#E63946" if accent else "#2A2A2A"
    val_color = "#E63946" if accent else "#F0F0F0"
    return f"""
    <div style='background:#141414; border:1px solid {border}; border-radius:6px; padding:20px 24px; height:100%'>
        <div style='font-size:0.65em; letter-spacing:3px; text-transform:uppercase; color:#666; margin-bottom:10px'>{label}</div>
        <div style='font-size:2.4em; font-weight:900; color:{val_color}; letter-spacing:-1px'>{value}</div>
    </div>
    """

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.markdown(metric_card("Eventos", total_eventos, accent=True), unsafe_allow_html=True)
c2.markdown(metric_card("Jugadores", total_jugadores), unsafe_allow_html=True)
c3.markdown(metric_card("Pases", total_pases), unsafe_allow_html=True)
c4.markdown(metric_card("Recuperaciones", total_recuperaciones), unsafe_allow_html=True)
c5.markdown(metric_card("Remates", total_remates), unsafe_allow_html=True)
c6.markdown(metric_card("Goles", total_goles, accent=total_goles > 0), unsafe_allow_html=True)

st.markdown("<div style='margin: 28px 0 20px 0'></div>", unsafe_allow_html=True)

# --- Tabla de jugadores ---
st.markdown("""
<div style='font-size:0.65em; letter-spacing:4px; text-transform:uppercase; color:#E63946; margin-bottom:12px; font-weight:600'>
    Participación por jugador
</div>
""", unsafe_allow_html=True)

resumen = df_filtrado.groupby("Player")["Event"].count().sort_values(ascending=False).reset_index()
resumen.columns = ["Jugador", "Total eventos"]
resumen["% del total"] = (resumen["Total eventos"] / resumen["Total eventos"].sum() * 100).round(1).astype(str) + "%"

st.dataframe(
    resumen,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Jugador": st.column_config.TextColumn("Jugador", width="medium"),
        "Total eventos": st.column_config.ProgressColumn(
            "Total eventos",
            min_value=0,
            max_value=int(resumen["Total eventos"].max()),
            format="%d",
        ),
        "% del total": st.column_config.TextColumn("% del total", width="small"),
    }
)