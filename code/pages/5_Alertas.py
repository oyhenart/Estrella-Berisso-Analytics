import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Alertas", page_icon="🚨", layout="wide")

@st.cache_data
def cargar_alertas():
    import os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(BASE, "data", "sanciones_lesiones.csv"))
    if not df.empty:
        df["fecha_regreso"] = pd.to_datetime(df["fecha_regreso"], errors="coerce")
    return df

st.title("🚨 Sanciones y Lesiones")

df = cargar_alertas()

if df.empty:
    st.info("✅ Sin novedades. No hay jugadores sancionados ni lesionados en este momento.")
    st.stop()

hoy = pd.Timestamp(date.today())

# Separar activos vs recuperados
df["activo"] = df["fecha_regreso"].isna() | (df["fecha_regreso"] >= hoy)
activos = df[df["activo"]].copy()
recuperados = df[~df["activo"]].copy()

# --- Métricas ---
lesiones = activos[activos["tipo"].str.lower() == "lesión"]
sanciones = activos[activos["tipo"].str.lower() == "sanción"]

col1, col2, col3 = st.columns(3)
col1.metric("Bajas activas", len(activos))
col2.metric("Lesionados", len(lesiones))
col3.metric("Sancionados", len(sanciones))

st.divider()

# --- Bajas activas ---
if not activos.empty:
    st.subheader("Bajas activas")
    for _, row in activos.iterrows():
        icono = "🤕" if row["tipo"].lower() == "lesión" else "🟥"
        regreso = row["fecha_regreso"].strftime("%d/%m/%Y") if pd.notna(row["fecha_regreso"]) else "Sin fecha definida"
        col1, col2, col3, col4 = st.columns([2, 2, 4, 2])
        col1.markdown(f"{icono} **{str(row['nombre']).title()}**")
        col2.markdown(row["tipo"])
        col3.markdown(row["motivo"])
        col4.markdown(f"📅 Regresa: **{regreso}**")
    st.divider()

# --- Recuperados ---
if not recuperados.empty:
    with st.expander("Ver jugadores recuperados"):
        for _, row in recuperados.iterrows():
            regreso = row["fecha_regreso"].strftime("%d/%m/%Y") if pd.notna(row["fecha_regreso"]) else "-"
            st.markdown(f"✅ **{str(row['nombre']).title()}** — {row['tipo']} ({row['motivo']}) — Regresó: {regreso}")
