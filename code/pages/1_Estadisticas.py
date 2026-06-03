import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Estadísticas", page_icon="📊", layout="wide")

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

st.title("📊 Estadísticas por jugador")

if not os.path.exists(DATA_PATH):
    st.info("⏳ El torneo aún no comenzó. Las estadísticas estarán disponibles a partir del primer partido.")
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

# Aplicar filtros
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

st.divider()

# --- Métricas ---
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Pases", len(df_filtrado[df_filtrado["Event"] == "pase"]))
col2.metric("Faltas cometidas", len(df_filtrado[df_filtrado["Event"] == "falta cometida"]))
col3.metric("Recuperaciones", len(df_filtrado[df_filtrado["Event"] == "recuperacion"]))
col4.metric("Remates", len(df_filtrado[df_filtrado["Event"] == "remate"]))
col5.metric("Goles", len(df_filtrado[df_filtrado["Event"] == "gol"]))

st.divider()

col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("Eventos por tipo")
    conteo = df_filtrado["Event"].value_counts().reset_index()
    conteo.columns = ["Evento", "Cantidad"]
    fig = px.bar(conteo, x="Cantidad", y="Evento", orientation="h",
                 color="Evento", color_discrete_sequence=px.colors.qualitative.Safe)
    fig.update_layout(showlegend=False, yaxis_title="", xaxis_title="Cantidad")
    st.plotly_chart(fig, use_container_width=True)

with col_der:
    st.subheader("Participación por jugador")
    if jugador_sel == "Todos":
        part = df_filtrado.groupby("Player")["Event"].count().sort_values(ascending=False).reset_index()
        part.columns = ["Jugador", "Eventos"]
        fig2 = px.bar(part, x="Jugador", y="Eventos", color="Jugador",
                      color_discrete_sequence=px.colors.qualitative.Safe)
        fig2.update_layout(showlegend=False, xaxis_title="", yaxis_title="Eventos")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        df_base = df.copy()
        if condicion_sel != "Local y Visitante" and num_fecha is None:
            fechas_cond = fixture[fixture["condicion"] == condicion_sel]["fecha"].tolist()
            df_base = df_base[df_base["fecha"].isin(fechas_cond)]
        if num_fecha:
            df_base = df_base[df_base["fecha"] == num_fecha]
        df_base["grupo"] = df_base["Player"].apply(
            lambda x: jugador_sel if x == jugador_sel else "Resto del equipo")
        comp = df_base.groupby("grupo")["Event"].count().reset_index()
        comp.columns = ["Grupo", "Eventos"]
        fig2 = px.pie(comp, values="Eventos", names="Grupo",
                      color_discrete_sequence=["#2ecc71", "#bdc3c7"])
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

st.subheader("Actividad durante el partido")
df_act = df_filtrado.copy()
df_act["minuto"] = df_act["Mins"].astype(int)
actividad = df_act.groupby(["minuto", "Event"]).size().reset_index(name="count")
fig3 = px.bar(actividad, x="minuto", y="count", color="Event",
              color_discrete_sequence=px.colors.qualitative.Safe,
              labels={"minuto": "Minuto", "count": "Eventos", "Event": "Tipo"})
fig3.update_layout(xaxis_title="Minuto del partido", yaxis_title="Cantidad de eventos")
st.plotly_chart(fig3, use_container_width=True)

st.divider()

st.subheader("Detalle de eventos")
st.dataframe(
    df_filtrado[["fecha", "Player", "Event", "Mins", "Secs", "X", "Y"]]
    .rename(columns={"fecha": "Fecha", "Player": "Jugador", "Event": "Evento"})
    .reset_index(drop=True),
    use_container_width=True, hide_index=True,
)