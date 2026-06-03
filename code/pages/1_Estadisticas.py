import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Estadísticas · Estrella FC", page_icon="📊", layout="wide")

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

# --- Header ---
st.markdown("""
<div style='margin-bottom:28px'>
    <p style='font-size:0.72em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:3px; margin:0 0 6px 0'>Análisis</p>
    <h1 style='font-size:2em; font-weight:800; margin:0; color:#EEEEEE; letter-spacing:-0.5px'>Estadísticas por jugador</h1>
</div>
""", unsafe_allow_html=True)

if not os.path.exists(DATA_PATH):
    st.info("⏳ El torneo aún no comenzó.")
    st.stop()

df = cargar_datos()
fixture = cargar_fixture()

# --- Filtros ---
fechas_disponibles = sorted(df["fecha"].unique().tolist())
opciones_fecha = ["Todos los partidos"] + [f"Fecha {f}" for f in fechas_disponibles]

col1, col2, col3 = st.columns(3)
with col1:
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

st.markdown("<div style='margin:20px 0; height:1px; background:#222'></div>", unsafe_allow_html=True)

# --- Métricas ---
def card(label, value, highlight=False):
    top_border = "border-top: 2px solid #E63946;" if highlight else "border-top: 2px solid #2A2A2A;"
    val_color = "#E63946" if highlight else "#EEEEEE"
    return f"""
    <div style='background:#1C1C1C; {top_border} border-radius:6px; padding:18px 20px;'>
        <div style='font-size:0.68em; color:#666; text-transform:uppercase; letter-spacing:2px; margin-bottom:8px'>{label}</div>
        <div style='font-size:2em; font-weight:800; color:{val_color}; letter-spacing:-0.5px'>{value}</div>
    </div>
    """

c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(card("Pases", len(df_filtrado[df_filtrado["Event"] == "pase"]), highlight=True), unsafe_allow_html=True)
c2.markdown(card("Faltas cometidas", len(df_filtrado[df_filtrado["Event"] == "falta cometida"])), unsafe_allow_html=True)
c3.markdown(card("Recuperaciones", len(df_filtrado[df_filtrado["Event"] == "recuperacion"])), unsafe_allow_html=True)
c4.markdown(card("Remates", len(df_filtrado[df_filtrado["Event"] == "remate"])), unsafe_allow_html=True)
c5.markdown(card("Goles", len(df_filtrado[df_filtrado["Event"] == "gol"])), unsafe_allow_html=True)

st.markdown("<div style='margin:28px 0 20px 0'></div>", unsafe_allow_html=True)

# --- Gráficos ---
col_izq, col_der = st.columns(2)

COLORS = ["#E63946","#457B9D","#A8DADC","#F1FAEE","#E9C46A","#F4A261","#2A9D8F","#264653","#6A4C93","#1982C4","#8AC926"]

with col_izq:
    st.markdown("<p style='font-size:0.72em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:3px; margin-bottom:12px'>Eventos por tipo</p>", unsafe_allow_html=True)
    conteo = df_filtrado["Event"].value_counts().reset_index()
    conteo.columns = ["Evento", "Cantidad"]
    fig = px.bar(conteo, x="Cantidad", y="Evento", orientation="h",
                 color="Evento", color_discrete_sequence=COLORS)
    fig.update_layout(
        showlegend=False, yaxis_title="", xaxis_title="",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#EEEEEE"), margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_der:
    st.markdown("<p style='font-size:0.72em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:3px; margin-bottom:12px'>Participación por jugador</p>", unsafe_allow_html=True)
    if jugador_sel == "Todos":
        part = df_filtrado.groupby("Player")["Event"].count().sort_values(ascending=False).reset_index()
        part.columns = ["Jugador", "Eventos"]
        fig2 = px.bar(part, x="Jugador", y="Eventos", color="Jugador",
                      color_discrete_sequence=COLORS)
        fig2.update_layout(
            showlegend=False, xaxis_title="", yaxis_title="",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#EEEEEE"), margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"),
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
        fig2 = px.pie(comp, values="Eventos", names="Grupo",
                      color_discrete_sequence=["#E63946", "#2A2A2A"],
                      hole=0.4)
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#EEEEEE"),
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<div style='margin:8px 0; height:1px; background:#222'></div>", unsafe_allow_html=True)

# --- Actividad por minuto ---
st.markdown("<p style='font-size:0.72em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:3px; margin:20px 0 12px 0'>Actividad durante el partido</p>", unsafe_allow_html=True)
df_act = df_filtrado.copy()
df_act["minuto"] = df_act["Mins"].astype(int)
actividad = df_act.groupby(["minuto", "Event"]).size().reset_index(name="count")
fig3 = px.bar(actividad, x="minuto", y="count", color="Event",
              color_discrete_sequence=COLORS,
              labels={"minuto": "Minuto", "count": "Eventos", "Event": "Tipo"})
fig3.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#EEEEEE"), margin=dict(l=0, r=0, t=0, b=0),
    xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("<div style='margin:8px 0; height:1px; background:#222'></div>", unsafe_allow_html=True)

# --- Detalle ---
st.markdown("<p style='font-size:0.72em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:3px; margin:20px 0 12px 0'>Detalle de eventos</p>", unsafe_allow_html=True)
st.dataframe(
    df_filtrado[["fecha", "Player", "Event", "Mins", "Secs", "X", "Y"]]
    .rename(columns={"fecha": "Fecha", "Player": "Jugador", "Event": "Evento"})
    .reset_index(drop=True),
    use_container_width=True, hide_index=True,
)