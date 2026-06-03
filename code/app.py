import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Estrella FC · Dashboard",
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
escudo_path = os.path.join(BASE, "static", "escudo.png")
if os.path.exists(escudo_path):
    st.sidebar.image(escudo_path, width=72)

st.sidebar.markdown("""
<div style='padding: 6px 0 20px 0'>
    <div style='font-size:1.05em; font-weight:700; color:#EEEEEE; line-height:1.3'>
        Club Atlético<br>Estrella de Berisso
    </div>
    <div style='font-size:0.72em; color:#555; text-transform:uppercase; letter-spacing:2px; margin-top:3px'>La Cebra</div>
    <div style='margin: 16px 0; height:1px; background:linear-gradient(to right, #E63946, transparent)'></div>
    <div style='font-size:0.7em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:2px'>IAO Football Analytics</div>
    <div style='font-size:0.68em; color:#444; margin-top:4px; font-style:italic'>Transformo datos en decisiones.</div>
</div>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div style='margin-bottom:28px'>
    <p style='font-size:0.72em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:3px; margin:0 0 6px 0'>
        Torneo Promocional Amateur 2026
    </p>
    <h1 style='font-size:2em; font-weight:800; margin:0; color:#EEEEEE; letter-spacing:-0.5px'>
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

st.markdown("<div style='margin:20px 0; height:1px; background:#222'></div>", unsafe_allow_html=True)

# --- Métricas ---
total_eventos     = len(df_filtrado)
total_jugadores   = df_filtrado["Player"].nunique()
total_pases       = len(df_filtrado[df_filtrado["Event"] == "pase"])
total_recuperaciones = len(df_filtrado[df_filtrado["Event"] == "recuperacion"])
total_remates     = len(df_filtrado[df_filtrado["Event"] == "remate"])
total_goles       = len(df_filtrado[df_filtrado["Event"] == "gol"])

def card(label, value, highlight=False):
    top_border = "border-top: 2px solid #E63946;" if highlight else "border-top: 2px solid #2A2A2A;"
    val_color = "#E63946" if highlight else "#EEEEEE"
    return f"""
    <div style='background:#1C1C1C; {top_border} border-radius:6px; padding:18px 20px;'>
        <div style='font-size:0.68em; color:#666; text-transform:uppercase; letter-spacing:2px; margin-bottom:8px'>{label}</div>
        <div style='font-size:2em; font-weight:800; color:{val_color}; letter-spacing:-0.5px'>{value}</div>
    </div>
    """

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.markdown(card("Eventos", total_eventos, highlight=True), unsafe_allow_html=True)
c2.markdown(card("Jugadores", total_jugadores), unsafe_allow_html=True)
c3.markdown(card("Pases", total_pases), unsafe_allow_html=True)
c4.markdown(card("Recuperaciones", total_recuperaciones), unsafe_allow_html=True)
c5.markdown(card("Remates", total_remates), unsafe_allow_html=True)
c6.markdown(card("Goles", total_goles, highlight=total_goles > 0), unsafe_allow_html=True)

st.markdown("<div style='margin:28px 0 16px 0'></div>", unsafe_allow_html=True)

# --- Tabla ---
st.markdown("""
<p style='font-size:0.72em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:3px; margin-bottom:12px'>
    Participación por jugador
</p>
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