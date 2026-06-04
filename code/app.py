import streamlit as st
import pandas as pd
import os

from components.layout import inject_css, render_sidebar, render_header

st.set_page_config(
    page_title="Estrella FC · Dashboard",
    page_icon="⚽",
    layout="wide"
)

inject_css()

BASE = os.path.dirname(os.path.abspath(__file__))
render_sidebar(BASE)
render_header("Torneo Promocional Amateur 2026", "Panel de análisis")

DATA_PATH    = os.path.join(BASE, "data", "events_clean.csv")
FIXTURE_PATH = os.path.join(BASE, "data", "fixture.csv")


@st.cache_data
def cargar_datos():
    df = pd.read_csv(DATA_PATH)
    df["tiempo_total"] = df["Mins"] * 60 + df["Secs"]
    return df


@st.cache_data
def cargar_fixture():
    return pd.read_csv(FIXTURE_PATH)


if not os.path.exists(DATA_PATH):
    st.info(
        "⏳ El torneo aún no comenzó. "
        "Las estadísticas estarán disponibles a partir del primer partido."
    )
    st.stop()

df      = cargar_datos()
fixture = cargar_fixture()

# ── Filtros ────────────────────────────────────────────────────────────────────

fechas_disponibles = sorted(df["fecha"].unique().tolist())
opciones_fecha = ["Todos los partidos"] + [f"Fecha {f}" for f in fechas_disponibles]

col1, col2 = st.columns(2)
with col1:
    fecha_sel = st.selectbox("Partido", opciones_fecha)
with col2:
    condicion_sel = st.selectbox("Condición", ["Local y Visitante", "Local", "Visitante"])

if fecha_sel != "Todos los partidos":
    num_fecha   = int(fecha_sel.replace("Fecha ", ""))
    df_filtrado = df[df["fecha"] == num_fecha]
else:
    num_fecha   = None
    df_filtrado = df.copy()

if condicion_sel != "Local y Visitante" and num_fecha is None:
    fechas_cond = fixture[fixture["condicion"] == condicion_sel]["fecha"].tolist()
    df_filtrado = df_filtrado[df_filtrado["fecha"].isin(fechas_cond)]

st.divider()

# ── KPIs ───────────────────────────────────────────────────────────────────────

total_pases          = len(df_filtrado[df_filtrado["Event"] == "pase"])
total_recuperaciones = len(df_filtrado[df_filtrado["Event"] == "recuperacion"])
total_remates        = len(df_filtrado[df_filtrado["Event"] == "remate"])
total_goles          = len(df_filtrado[df_filtrado["Event"] == "gol"])
total_perdidas       = len(df_filtrado[df_filtrado["Event"] == "perdida"])
total_jugadores      = df_filtrado["Player"].nunique()
total_eventos        = len(df_filtrado)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Eventos",           total_eventos)
c2.metric("Pases",             total_pases)
c3.metric("Recuperaciones",    total_recuperaciones)
c4.metric("Remates / Goles",   f"{total_remates} / {total_goles}")

st.caption(
    f"{total_jugadores} jugadores registrados · "
    f"{total_perdidas} pérdidas registradas"
)

st.divider()

# ── Tabla de participación ─────────────────────────────────────────────────────

st.subheader("Participación por jugador")

resumen = (
    df_filtrado
    .groupby("Player")["Event"]
    .count()
    .sort_values(ascending=False)
    .reset_index()
)
resumen.columns = ["Jugador", "Total eventos"]
resumen["% del total"] = (
    resumen["Total eventos"] / resumen["Total eventos"].sum() * 100
).round(1)

st.dataframe(resumen, use_container_width=True, hide_index=True)