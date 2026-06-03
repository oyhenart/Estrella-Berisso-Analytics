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

st.title("⚽ Estrella FC — Panel de análisis")

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

# Aplicar filtro de fecha
if fecha_sel != "Todos los partidos":
    num_fecha = int(fecha_sel.replace("Fecha ", ""))
    df_filtrado = df[df["fecha"] == num_fecha]
else:
    num_fecha = None
    df_filtrado = df.copy()

# Aplicar filtro de condición usando fixture
if condicion_sel != "Local y Visitante" and num_fecha is None:
    fechas_cond = fixture[fixture["condicion"] == condicion_sel]["fecha"].tolist()
    df_filtrado = df_filtrado[df_filtrado["fecha"].isin(fechas_cond)]
elif condicion_sel != "Local y Visitante" and num_fecha is not None:
    fila = fixture[fixture["fecha"] == num_fecha]
    if not fila.empty and fila.iloc[0]["condicion"] != condicion_sel:
        st.warning(f"La Fecha {num_fecha} es {fila.iloc[0]['condicion']}, no {condicion_sel}.")

st.divider()

# --- Métricas ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total eventos", len(df_filtrado))
col2.metric("Jugadores", df_filtrado["Player"].nunique())
col3.metric("Pases", len(df_filtrado[df_filtrado["Event"] == "pase"]))
col4.metric("Goles", len(df_filtrado[df_filtrado["Event"] == "gol"]))

st.divider()

st.subheader("Eventos por jugador")
resumen = df_filtrado.groupby("Player")["Event"].count().sort_values(ascending=False).reset_index()
resumen.columns = ["Jugador", "Total eventos"]
st.dataframe(resumen, use_container_width=True, hide_index=True)