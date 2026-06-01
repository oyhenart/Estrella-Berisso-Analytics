import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Plantilla", page_icon="👥", layout="wide")

@st.cache_data
def cargar_jugadores():
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(BASE, "data", "Jugadores.csv"))
    df["nombre"] = df["nombre"].str.strip().str.title()
    df["posicion"] = df["posicion"].str.strip().str.title()
    return df

df = cargar_jugadores()

st.title("👥 Plantilla")

posiciones = ["Todas"] + sorted(df["posicion"].unique().tolist())
pos_sel = st.selectbox("Filtrar por posición", posiciones)

if pos_sel != "Todas":
    df_filtrado = df[df["posicion"] == pos_sel]
else:
    df_filtrado = df

st.divider()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total jugadores", len(df))
col2.metric("Arqueros", len(df[df["posicion"].str.lower() == "arquero"]))
col3.metric("Defensores", len(df[df["posicion"].str.lower() == "defensor"]))
col4.metric("Mediocampistas + Delanteros",
            len(df[df["posicion"].str.lower().isin(["mediocampista", "delantero"])]))

st.divider()

FOTOS_DIR = os.path.join(BASE, "static", "fotos")
COLS = 5

jugadores = df_filtrado.reset_index(drop=True)
for i in range(0, len(jugadores), COLS):
    cols = st.columns(COLS)
    for j, col in enumerate(cols):
        idx = i + j
        if idx >= len(jugadores):
            break
        row = jugadores.iloc[idx]
        foto_path = os.path.join(FOTOS_DIR, str(row["fotos"]))
        with col:
            if os.path.exists(foto_path):
                st.image(foto_path, use_container_width=True)
            else:
                st.image(os.path.join(FOTOS_DIR, "sin_perfil.jpg"), use_container_width=True)
            st.markdown(
                f"""
                <div style='text-align:center; padding: 4px 0'>
                    <span style='font-size:1.4em; font-weight:700'>#{int(row['camiseta'])}</span><br>
                    <span style='font-size:1em; font-weight:600'>{row['nombre']}</span><br>
                    <span style='font-size:0.8em; color: #aaa'>{row['posicion']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
