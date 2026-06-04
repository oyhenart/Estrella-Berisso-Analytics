import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Estadísticas · Estrella FC", page_icon="📊", layout="wide")

st.markdown("""
<style>
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

# Sidebar
escudo_path = os.path.join(BASE, "static", "escudo.png")
if os.path.exists(escudo_path):
    st.sidebar.image(escudo_path, width=64)
st.sidebar.markdown("""
<div style='padding: 4px 0 20px 0'>
    <div style='font-size:0.95em; font-weight:700; color:#F9FAFB; line-height:1.4'>Club Atlético<br>Estrella de Berisso</div>
    <div style='font-size:0.68em; color:#6B7280; text-transform:uppercase; letter-spacing:2px; margin-top:3px'>La Cebra</div>
    <div style='margin: 14px 0; height:1px; background:linear-gradient(to right, #E23E3E55, transparent)'></div>
    <div style='font-size:0.65em; font-weight:600; color:#9CA3AF; text-transform:uppercase; letter-spacing:2px'>IAO Football Analytics</div>
    <div style='font-size:0.63em; color:#4B5563; margin-top:4px; font-style:italic'>Transformo datos en decisiones.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style='margin-bottom:24px'>
    <p style='font-size:0.68em; font-weight:600; color:#E23E3E; text-transform:uppercase; letter-spacing:3px; margin:0 0 4px 0'>Análisis</p>
    <h1 style='font-size:1.9em; font-weight:800; margin:0; color:#F9FAFB; letter-spacing:-0.5px'>Estadísticas por jugador</h1>
</div>
""", unsafe_allow_html=True)

if not os.path.exists(DATA_PATH):
    st.info("⏳ El torneo aún no comenzó.")
    st.stop()

df = cargar_datos()
fixture = cargar_fixture()

col1, col2, col3 = st.columns(3)
with col1:
    fechas_disponibles = sorted(df["fecha"].unique().tolist())
    opciones_fecha = ["Todos los partidos"] + [f"Fecha {f}" for f in fechas_disponibles]
    fecha_sel = st.selectbox("Partido", opciones_fecha)
with col2:
    condicion_sel = st.selectbox("Condición", ["Local y Visitante", "Local", "Visitante"])
with col3:
    jugadores = ["Todos"] + sorted(df["Player"].unique().tolist())
    jugador_sel = st.selectbox("Jugador", jugadores)

if fecha_sel != "Todos los partidos":
    num_fecha = int(fecha_sel.replace("Fecha ", ""))
    df_filtrado = df[df["fecha"] == num_fecha]
else:
    num_fecha = None
    df_filtrado = df.copy()

if condicion_sel != "Local y Visitante" and num_fecha is None:
    fechas_cond = fixture[fixture["condicion"] == condicion_sel]["fecha"].tolist()
    df_filtrado = df_filtrado[df_filtrado["fecha"].isin(fechas_cond)]

if jugador_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Player"] == jugador_sel]

st.markdown("<div style='margin:16px 0; height:1px; background:#1F2937'></div>", unsafe_allow_html=True)

# KPIs
def kpi(label, value, highlight=False):
    accent = "#E23E3E" if highlight else "#374151"
    val_color = "#E23E3E" if highlight else "#F9FAFB"
    return f"""
    <div style='background:#1F2937; border-left:3px solid {accent}; border-radius:4px; padding:14px 18px;'>
        <div style='font-size:0.62em; color:#6B7280; text-transform:uppercase; letter-spacing:2px; margin-bottom:6px'>{label}</div>
        <div style='font-size:1.9em; font-weight:800; color:{val_color}; letter-spacing:-0.5px; line-height:1'>{value}</div>
    </div>
    """

c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(kpi("Pases", len(df_filtrado[df_filtrado["Event"] == "pase"]), highlight=True), unsafe_allow_html=True)
c2.markdown(kpi("Recuperaciones", len(df_filtrado[df_filtrado["Event"] == "recuperacion"])), unsafe_allow_html=True)
c3.markdown(kpi("Faltas cometidas", len(df_filtrado[df_filtrado["Event"] == "falta cometida"])), unsafe_allow_html=True)
c4.markdown(kpi("Remates", len(df_filtrado[df_filtrado["Event"] == "remate"])), unsafe_allow_html=True)
c5.markdown(kpi("Goles", len(df_filtrado[df_filtrado["Event"] == "gol"])), unsafe_allow_html=True)

st.markdown("<div style='margin:24px 0 16px 0'></div>", unsafe_allow_html=True)

NEUTRAL = "#374151"
HIGHLIGHT = "#E23E3E"

col_izq, col_der = st.columns(2)

with col_izq:
    st.markdown("<p style='font-size:0.68em; font-weight:600; color:#9CA3AF; text-transform:uppercase; letter-spacing:3px; margin-bottom:10px'>Eventos por tipo</p>", unsafe_allow_html=True)
    conteo = df_filtrado["Event"].value_counts().reset_index()
    conteo.columns = ["Evento", "Cantidad"]
    # Destacar solo la barra más alta
    colors = [HIGHLIGHT if i == 0 else NEUTRAL for i in range(len(conteo))]
    fig = go.Figure(go.Bar(
        x=conteo["Cantidad"], y=conteo["Evento"],
        orientation="h", marker_color=colors,
        hovertemplate="%{y}: %{x}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF", size=12), margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(gridcolor="#1F2937", zeroline=False),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        height=320,
    )
    st.plotly_chart(fig, use_container_width=True)

with col_der:
    st.markdown("<p style='font-size:0.68em; font-weight:600; color:#9CA3AF; text-transform:uppercase; letter-spacing:3px; margin-bottom:10px'>Participación por jugador</p>", unsafe_allow_html=True)
    if jugador_sel == "Todos":
        part = df_filtrado.groupby("Player")["Event"].count().sort_values(ascending=False).reset_index()
        part.columns = ["Jugador", "Eventos"]
        colors2 = [HIGHLIGHT if i == 0 else NEUTRAL for i in range(len(part))]
        fig2 = go.Figure(go.Bar(
            x=part["Jugador"], y=part["Eventos"],
            marker_color=colors2,
            hovertemplate="%{x}: %{y}<extra></extra>",
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF", size=12), margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),
            yaxis=dict(gridcolor="#1F2937"),
            height=320,
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        df_base = df.copy()
        if condicion_sel != "Local y Visitante" and num_fecha is None:
            fechas_cond = fixture[fixture["condicion"] == condicion_sel]["fecha"].tolist()
            df_base = df_base[df_base["fecha"].isin(fechas_cond)]
        if num_fecha:
            df_base = df_base[df_base["fecha"] == num_fecha]
        df_base["grupo"] = df_base["Player"].apply(lambda x: jugador_sel if x == jugador_sel else "Resto")
        comp = df_base.groupby("grupo")["Event"].count().reset_index()
        comp.columns = ["Grupo", "Eventos"]
        fig2 = go.Figure(go.Pie(
            labels=comp["Grupo"], values=comp["Eventos"],
            hole=0.5,
            marker=dict(colors=[HIGHLIGHT, NEUTRAL]),
            textfont=dict(color="#9CA3AF"),
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF"),
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#9CA3AF")),
            height=320,
        )
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<div style='margin:8px 0; height:1px; background:#1F2937'></div>", unsafe_allow_html=True)

st.markdown("<p style='font-size:0.68em; font-weight:600; color:#9CA3AF; text-transform:uppercase; letter-spacing:3px; margin:16px 0 10px 0'>Actividad durante el partido</p>", unsafe_allow_html=True)
df_act = df_filtrado.copy()
df_act["minuto"] = df_act["Mins"].astype(int)
actividad = df_act.groupby("minuto")["Event"].count().reset_index()
actividad.columns = ["Minuto", "Eventos"]
fig3 = go.Figure(go.Bar(
    x=actividad["Minuto"], y=actividad["Eventos"],
    marker_color=NEUTRAL,
    hovertemplate="Min %{x}: %{y} eventos<extra></extra>",
))
fig3.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#9CA3AF", size=12), margin=dict(l=0, r=0, t=0, b=0),
    xaxis=dict(gridcolor="#1F2937", title="Minuto"),
    yaxis=dict(gridcolor="#1F2937", title="Eventos"),
    height=260,
)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("<div style='margin:8px 0; height:1px; background:#1F2937'></div>", unsafe_allow_html=True)
st.markdown("<p style='font-size:0.68em; font-weight:600; color:#9CA3AF; text-transform:uppercase; letter-spacing:3px; margin:16px 0 10px 0'>Detalle de eventos</p>", unsafe_allow_html=True)
st.dataframe(
    df_filtrado[["fecha", "Player", "Event", "Mins", "Secs", "X", "Y"]]
    .rename(columns={"fecha": "Fecha", "Player": "Jugador", "Event": "Evento"})
    .reset_index(drop=True),
    use_container_width=True, hide_index=True,
)