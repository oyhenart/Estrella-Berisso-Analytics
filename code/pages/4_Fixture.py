import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Fixture", page_icon="🗓️", layout="wide")

# Definimos la base del proyecto a nivel global
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@st.cache_data
def cargar_fixture():
    # Corregido el sangrado para que esté dentro de la función
    df = pd.read_csv(os.path.join(BASE, "data", "fixture.csv"))
    return df

st.title("🗓️ Fixture — Torneo Promocional Amateur 2026")

df = cargar_fixture()

# --- Métricas ---
jugados = df[df["estado"] == "Jugado"]
pendientes = df[df["estado"] == "Pendiente"]

if len(jugados) > 0:
    ganados = len(jugados[(jugados["goles_favor"] > jugados["goles_contra"])])
    empatados = len(jugados[(jugados["goles_favor"] == jugados["goles_contra"])])
    perdidos = len(jugados[(jugados["goles_favor"] < jugados["goles_contra"])])
    gf = jugados["goles_favor"].sum()
    gc = jugados["goles_contra"].sum()
    puntos = ganados * 3 + empatados

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Partidos jugados", len(jugados))
    col2.metric("Puntos", puntos)
    col3.metric("Ganados", ganados)
    col4.metric("Empatados", empatados)
    col5.metric("Perdidos", perdidos)
    col6.metric("Diferencia de goles", int(gf - gc))
else:
    st.info("⏳ El torneo aún no comenzó. Aquí aparecerán los resultados y la tabla de posiciones.")

st.divider()

# --- Tabla de fixture ---
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
                resultado = f"✅ {gf} - {gc}"
            elif gf == gc:
                resultado = f"🟡 {gf} - {gc}"
            else:
                resultado = f"❌ {gf} - {gc}"
            st.markdown(resultado)
        else:
            st.markdown("🕐 Pendiente")

    with col4:
        badge = "🟢 Local" if row["condicion"] == "Local" else "🔵 Visitante"
        st.markdown(badge)

    st.divider()
