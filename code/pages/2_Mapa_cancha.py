import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

from components.layout import (
    inject_css,
    render_sidebar
)

# ── Configuración de Página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Mapa de cancha",
    page_icon="🗺️",
    layout="wide"
)

inject_css()

BASE = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

render_sidebar(BASE)

# ── Rutas de Archivos ──────────────────────────────────────────────────────────
DATA_PATH = os.path.join(
    BASE,
    "data",
    "events_clean.csv"
)

FIXTURE_PATH = os.path.join(
    BASE,
    "data",
    "fixture.csv"
)

# ── Carga de Datos con Caché ───────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    df = pd.read_csv(DATA_PATH)
    df["tiempo_total"] = df["Mins"] * 60 + df["Secs"]
    
    # Armar df_pases desde X2/Y2
    pases = df[df["Event"] == "pase"].copy()
    pases = pases.rename(columns={
        "Player": "jugador_origen", "X": "x_origen", "Y": "y_origen",
        "X2": "x_destino", "Y2": "y_destino", "Mins": "mins", "Secs": "secs"
    })
    df_pases = pases[["jugador_origen","x_origen","y_origen","x_destino","y_destino","mins","secs","fecha"]].dropna(subset=["x_destino","y_destino"])
    return df, df_pases

# ── Encabezado Personal