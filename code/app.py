import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Estrella FC · Dashboard",
    page_icon="⚽",
    layout="wide",
)

# Ocultar elementos genéricos de Streamlit
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

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
escudo_path = os.path.join(BASE, "static", "escudo.png")
if os.path.exists(escudo_path):
    st.sidebar.image(escudo_path, width=64)
st.sidebar.markdown("""
<div style='padding: 4px 0 20px 0'>
    <div style='font-size:0.95em; font-weight:700; color:#F9FAFB; line-height:1.4'>
        Club Atlético<br>Estrella de Berisso
    </div>
    <div style='font-size:0.68em; color:#6B7280; text-transform:uppercase; letter-spacing:2px; margin-top:3px'>La Cebra</div>
    <div style='margin: 14px 0; height:1px; background:linear-gradient(to right, #E23E3E55, transparent)'></div>
    <div style='font-size:0.65em; font-weight:600; color:#9CA3AF; text-transform:uppercase; letter-spacing:2px'>IAO Football Analytics</div>
    <div style='font-size:0.63em; color:#4B5563; margin-top:4px; font-style:italic'>Transformo datos en decisiones.</div>
</div>
""", unsafe_allow_html=True)

# Navegación manual en sidebar
st.sidebar.markdown("<div style='margin-top:8px; height:1px; background:#1F2937'></div>", unsafe_allow_html=True)
pages = {
    "⚽ Inicio": "/",
    "📊 Estadísticas": "/Estadisticas",
    "🗺️ Mapa de cancha": "/Mapa_cancha",
    "👥 Plantilla": "/Plantilla",
    "🗓️ Fixture": "/Fixture",
    "🚨 Alertas": "/Alertas",
    "🎬 Videos": "/Videos",
}
for label, _ in pages.items():
    st.sidebar.markdown(f"<div style='padding:6px 8px; font-size:0.85em; color:#9CA3AF'>{label}</div>", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div style='margin-bottom:24px'>
    <p style='font-size:0.68em; font-weight:600; color:#E23E3E; text-transform:uppercase; letter-spacing:3px; margin:0 0 4px 0'>
        Torneo Promocional Amateur 2026
    </p>
    <h1 style='font-size:1.9em; font-weight:800; margin:0; color:#F9FAFB; letter-spacing:-0.5px'>
        Panel de análisis
    </h1>
</div>
""", unsafe_allow_html=True)

if not os.path.exists(DATA_PATH):
    st.info("⏳ El torneo aún no comenzó. Las estadísticas estarán disponibles a partir del primer partido.")
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

st.markdown("<div style='margin:16px 0; height:1px; background:#1F2937'></div>", unsafe_allow_html=True)

# --- KPIs compactos ---
total_pases = len(df_filtrado[df_filtrado["Event"] == "pase"])
total_recuperaciones = len(df_filtrado[df_filtrado["Event"] == "recuperacion"])
total_remates = len(df_filtrado[df_filtrado["Event"] == "remate"])
total_goles = len(df_filtrado[df_filtrado["Event"] == "gol"])
total_perdidas = len(df_filtrado[df_filtrado["Event"] == "perdida"])
total_jugadores = df_filtrado["Player"].nunique()
total_eventos = len(df_filtrado)

def kpi(label, value, sub=None, highlight=False):
    accent = "#E23E3E" if highlight else "#374151"
    val_color = "#E23E3E" if highlight else "#F9FAFB"
    sub_html = f"<div style='font-size:0.72em; color:#6B7280; margin-top:4px'>{sub}</div>" if sub else ""
    return f"""
    <div style='background:#1F2937; border-left:3px solid {accent}; border-radius:4px; padding:14px 18px;'>
        <div style='font-size:0.62em; color:#6B7280; text-transform:uppercase; letter-spacing:2px; margin-bottom:6px'>{label}</div>
        <div style='font-size:1.9em; font-weight:800; color:{val_color}; letter-spacing:-0.5px; line-height:1'>{value}</div>
        {sub_html}
    </div>
    """

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi("Eventos totales", total_eventos, sub=f"{total_jugadores} jugadores", highlight=True), unsafe_allow_html=True)
c2.markdown(kpi("Pases", total_pases, sub=f"{total_perdidas} pérdidas registradas"), unsafe_allow_html=True)
c3.markdown(kpi("Recuperaciones", total_recuperaciones), unsafe_allow_html=True)
c4.markdown(kpi("Remates · Goles", f"{total_remates} · {total_goles}", highlight=total_goles > 0), unsafe_allow_html=True)

st.markdown("<div style='margin:24px 0 16px 0'></div>", unsafe_allow_html=True)

# --- Tabla ---
st.markdown("<p style='font-size:0.68em; font-weight:600; color:#9CA3AF; text-transform:uppercase; letter-spacing:3px; margin-bottom:10px'>Participación por jugador</p>", unsafe_allow_html=True)

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
        "% del total": st.column_config.TextColumn("%", width="small"),
    }
)