import streamlit as st
import pandas as pd
import os

from components.layout import (
    inject_css,
    render_sidebar,
    render_header
)

st.set_page_config(page_title="Fixture", page_icon="🗓️", layout="wide")

inject_css()

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
render_sidebar(BASE)

render_header(
    "Torneo Promocional Amateur 2026",
    "Fixture y resultados"
)

@st.cache_data(ttl=0)
def cargar_fixture():
    return pd.read_csv(os.path.join(BASE, "data", "fixture.csv"))

df = cargar_fixture()

jugados = df[df["estado"] == "Jugado"]
pendientes = df[df["estado"] == "Pendiente"]

if len(jugados) > 0:
    ganados = len(jugados[(jugados["goles_favor"] > jugados["goles_contra"])])
    empatados = len(jugados[(jugados["goles_favor"] == jugados["goles_contra"])])
    perdidos = len(jugados[(jugados["goles_favor"] < jugados["goles_contra"])])
    gf = jugados["goles_favor"].sum()
    gc = jugados["goles_contra"].sum()
    puntos = ganados * 3 + empatados
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Partidos jugados",
        len(jugados)
    )
    col2.metric(
        "Puntos",
        puntos
    )
    col3.metric(
        "Diferencia de gol",
        int(gf - gc)
    )
    col4, col5, col6 = st.columns(3)
    col4.metric(
        "Ganados",
        ganados
    )
    col5.metric(
        "Empatados",
        empatados
    )
    col6.metric(
        "Perdidos",
        perdidos
    )
else:
    st.info("⏳ El torneo aún no comenzó. Aquí aparecerán los resultados y la tabla de posiciones.")

st.divider()

st.subheader("Fechas")

for _, row in df.iterrows():
    col1, col2, col3, col4 = st.columns([1, 3, 3, 2])
    with col1:
        st.markdown(f"**Fecha {int(row['fecha'])}**")
    with col2:
        if row["condicion"] == "Local":
            st.markdown(f"🏠 **Estrella de Berisso** vs {row['rival']}")
        else:
            st.markdown(f"✈️ {row['rival']} vs **Estrella de Berisso**")
    with col3:
        if row["estado"] == "Jugado":
            gf = int(row["goles_favor"])
            gc = int(row["goles_contra"])
            if gf > gc:
                st.success(resultado)
            elif gf == gc:
                st.warning(resultado)
            else:
                st.error(resultado)
        else:
            st.markdown("🕐 Pendiente")
    with col4:
        badge = "🟢 Local" if row["condicion"] == "Local" else "🔵 Visitante"
        st.markdown(badge)
    st.divider()
