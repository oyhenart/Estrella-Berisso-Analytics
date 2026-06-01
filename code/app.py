import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Estrella FC - Dashboard",
    page_icon="⚽",
    layout="wide",
)

DATA_PATH = "data/events_clean.csv"

@st.cache_data
def cargar_datos():
    df = pd.read_csv(DATA_PATH)
    df["tiempo_total"] = df["Mins"] * 60 + df["Secs"]
    pases = []
    for i in range(len(df) - 1):
        if df.iloc[i]["Event"] == "Pase" and df.iloc[i + 1]["Event"] == "Recepción":
            pases.append({
                "jugador_origen": df.iloc[i]["Player"],
                "jugador_destino": df.iloc[i + 1]["Player"],
                "x_origen": df.iloc[i]["X"], "y_origen": df.iloc[i]["Y"],
                "x_destino": df.iloc[i + 1]["X"], "y_destino": df.iloc[i + 1]["Y"],
                "mins": df.iloc[i]["Mins"], "secs": df.iloc[i]["Secs"],
            })
    return df, pd.DataFrame(pases)

st.title("⚽ Estrella FC — Panel de análisis")

if not os.path.exists(DATA_PATH):
    st.info("⏳ El torneo aún no comenzó. Las estadísticas estarán disponibles a partir del primer partido.")
    st.stop()

df, df_pases = cargar_datos()
st.session_state["df"] = df
st.session_state["df_pases"] = df_pases

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total eventos", len(df))
col2.metric("Jugadores", df["Player"].nunique())
col3.metric("Pases registrados", len(df[df["Event"] == "Pase"]))
col4.metric("Goles", len(df[df["Event"] == "Gol"]))

st.divider()

st.subheader("Eventos por jugador")
resumen = df.groupby("Player")["Event"].count().sort_values(ascending=False).reset_index()
resumen.columns = ["Jugador", "Total eventos"]
st.dataframe(resumen, use_container_width=True, hide_index=True)