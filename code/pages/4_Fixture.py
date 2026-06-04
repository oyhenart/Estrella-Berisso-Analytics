import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Fixture", page_icon="🗓️", layout="wide")

st.markdown("""
<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@st.cache_data(ttl=0)
def cargar_fixture():
    return pd.read_csv(os.path.join(BASE, "data", "fixture.csv"))

# --- Sidebar ---
escudo_path = os.path.join(BASE, "static", "escudo.png")
if os.path.exists(escudo_path):
    st.sidebar.image(escudo_path, width=72)
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
    <p style='font-size:0.72em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:3px; margin:0 0 6px 0'>Torneo Promocional Amateur 2026</p>
    <h1 style='font-size:2em; font-weight:800; margin:0; color:#EEEEEE; letter-spacing:-0.5px'>Fixture y resultados</h1>
</div>
""", unsafe_allow_html=True)

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