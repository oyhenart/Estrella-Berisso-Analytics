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
DATA_PATH = os.path.join(BASE, "data", "events_clean.csv")
FIXTURE_PATH = os.path.join(BASE, "data", "fixture.csv")

# ── Carga de Datos con Caché (REPARADA) ─────────────────────────────────────────
@st.cache_data
def cargar_datos():
    df = pd.read_csv(DATA_PATH)
    
    # 1. Aseguramos que los tiempos sean numéricos antes de operar
    df["Mins"] = pd.to_numeric(df["Mins"], errors="coerce").fillna(0)
    df["Secs"] = pd.to_numeric(df["Secs"], errors="coerce").fillna(0)
    df["tiempo_total"] = df["Mins"] * 60 + df["Secs"]
    
    # Estandarización preventiva de columnas de control
    if "Resultado" not in df.columns:
        df["Resultado"] = 1
    if "Receptor" not in df.columns:
        df["Receptor"] = "Desconocido"
        
    # Armar dataframe específico de pases
    pases = df[df["Event"] == "pase"].copy()
    pases = pases.rename(columns={
        "Player": "jugador_origen", "X": "x_origen", "Y": "y_origen",
        "X2": "x_destino", "Y2": "y_destino", "Mins": "mins", "Secs": "secs",
        "Receptor": "jugador_destino", "Resultado": "resultado"
    })
    
    # 2. 🚨 EL BLINDAJE: Forzamos a que todas las coordenadas de los pases sean números flotantes
    for col in ["x_origen", "y_origen", "x_destino", "y_destino", "resultado"]:
        pases[col] = pd.to_numeric(pases[col], errors="coerce")
    
    # 3. Limpiamos cualquier fila que se haya quedado sin destino o sin origen numérico
    df_pases = pases.dropna(subset=["x_origen", "y_origen", "x_destino", "y_destino"]).copy()
    
    # Aseguramos tipos nativos finales para que PyArrow no proteste en Streamlit Cloud
    df_pases["x_origen"] = df_pases["x_origen"].astype(float)
    df_pases["y_origen"] = df_pases["y_origen"].astype(float)
    df_pases["x_destino"] = df_pases["x_destino"].astype(float)
    df_pases["y_destino"] = df_pases["y_destino"].astype(float)
    df_pases["resultado"] = df_pases["resultado"].astype(int)
    
    return df, df_pases

# ── Encabezado Personalizado ───────────────────────────────────────────────────
st.markdown("""
<div style='margin-bottom:28px'>
    <p style='font-size:0.72em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:3px; margin:0 0 6px 0'>Análisis Táctico</p>
    <h1 style='font-size:2em; font-weight:800; margin:0; color:#EEEEEE; letter-spacing:-0.5px'>Mapa de eventos y dinámica de pases</h1>
</div>
""", unsafe_allow_html=True)

if not os.path.exists(DATA_PATH) or not os.path.exists(FIXTURE_PATH):
    st.info("⏳ El torneo aún no comenzó o faltan archivos de datos. El mapa estará disponible a partir del primer partido.")
    st.stop()

df, df_pases = cargar_datos()
fixture = pd.read_csv(FIXTURE_PATH)

# Dimensiones reglamentarias de referencia (StatsBomb / Porcentual)
W, H = 100, 100
AG_X = 12.7; AG_Y = 44.8
AC_X = 4.2;  AC_Y = 20.4
ARCO = 8.1;  CR   = 7.0

# Gama cromática para eventos generales y discriminación de pases
colores = {
    "pase_correcto":  "#22C55E", # Verde estallado
    "pase_incorrecto":"#EF4444", # Rojo alerta
    "recuperacion":   "#34D399",
    "perdida":        "#F87171",
    "conduccion":     "#A78BFA",
    "tiro libre":     "#FCD34D",
    "remate":         "#FB923C",
    "centro":         "#67E8F9",
    "gol":            "#E23E3E",
    "despeje":        "#9CA3AF",
    "corner":         "#F9A8D4",
    "falta recibida": "#6EE7B7",
    "falta cometida": "#FCA5A5",
}

# ── Filtros de la Aplicación ───────────────────────────────────────────────────
fechas_disponibles = sorted(df["fecha"].unique().tolist())
opciones_fecha     = ["Todos los partidos"] + [f"Fecha {f}" for f in fechas_disponibles]

col1, col2, col3 = st.columns(3)
with col1:
    fecha_sel = st.selectbox("Partido", opciones_fecha)
with col2:
    condicion_sel = st.selectbox("Condición", ["Local y Visitante", "Local", "Visitante"])
with col3:
    jugadores   = ["Todos"] + sorted(df["Player"].unique().tolist())
    jugador_sel = st.selectbox("Jugador", jugadores)

eventos_disponibles = sorted(df["Event"].unique().tolist())
default_eventos     = ["pase"] if "pase" in eventos_disponibles else eventos_disponibles[:1]
eventos_sel = st.multiselect("Tipo de evento a visualizar", eventos_disponibles, default=default_eventos)

st.divider()

# ── Lógica de Filtrado de Datos ────────────────────────────────────────────────
if fecha_sel != "Todos los partidos":
    num_fecha   = int(fecha_sel.replace("Fecha ", ""))
    df_filtrado = df[df["fecha"] == num_fecha]
    df_pases_f  = df_pases[df_pases["fecha"] == num_fecha]
else:
    num_fecha   = None
    df_filtrado = df.copy()
    df_pases_f  = df_pases.copy()

if condicion_sel != "Local y Visitante" and num_fecha is None:
    fechas_cond = fixture[fixture["condicion"] == condicion_sel]["fecha"].tolist()
    df_filtrado = df_filtrado[df_filtrado["fecha"].isin(fechas_cond)]
    df_pases_f  = df_pases_f[df_pases_f["fecha"].isin(fechas_cond)]

# El dataframe general se filtra por la selección múltiple de eventos
df_filtrado = df_filtrado[df_filtrado["Event"].isin(eventos_sel)]

if jugador_sel != "Todos":
    df_filtrado  = df_filtrado[df_filtrado["Player"] == jugador_sel]
    df_pases_f   = df_pases_f[df_pases_f["jugador_origen"] == jugador_sel]

# =============================================================================
# VISUALIZACIONES DE CANCHA - MPLSOCCER
# =============================================================================

from mplsoccer import Pitch
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# LIMPIEZA DE COORDENADAS
# -----------------------------------------------------------------------------

for col in ["X", "Y", "X2", "Y2"]:
    if col in df_filtrado.columns:
        df_filtrado[col] = pd.to_numeric(
            df_filtrado[col],
            errors="coerce"
        )

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE CANCHA
# -----------------------------------------------------------------------------

def crear_cancha():

    pitch = Pitch(
        pitch_type="opta",
        pitch_color="#1B4332",
        line_color="white",
        linewidth=2,
        line_zorder=10,
        corner_arcs=True
    )

    fig, ax = pitch.draw(
        figsize=(12, 8)
    )

    fig.set_facecolor("#1B4332")

    return pitch, fig, ax


# =============================================================================
# GRÁFICO 1 - MAPA DE EVENTOS
# =============================================================================

st.subheader("📍 Ubicación de eventos en campo de juego")

if not df_filtrado.empty:

    pitch, fig, ax = crear_cancha()

    colores_eventos = {
        "pase": "#4ade80",
        "centro": "#60a5fa",
        "tiro": "#ef4444",
        "remate": "#ef4444",
        "recuperacion": "#facc15",
        "perdida": "#f97316",
        "duelo": "#c084fc",
        "intercepcion": "#22d3ee"
    }

    eventos_presentes = (
        df_filtrado["Event"]
        .dropna()
        .unique()
    )

    for evento in eventos_presentes:

        subset = df_filtrado[
            df_filtrado["Event"] == evento
        ]

        if subset.empty:
            continue

        # --------------------------------------------------
        # PASES Y CENTROS = FLECHAS
        # --------------------------------------------------

        if evento.lower() in ["pase", "centro"]:

            subset_flechas = subset[
                subset["X2"].notna()
                &
                subset["Y2"].notna()
            ]

            if not subset_flechas.empty:

                pitch.arrows(
                    subset_flechas["X"],
                    subset_flechas["Y"],
                    subset_flechas["X2"],
                    subset_flechas["Y2"],
                    ax=ax,
                    color=colores_eventos.get(
                        evento.lower(),
                        "#FFFFFF"
                    ),
                    width=2,
                    alpha=0.75
                )

            pitch.scatter(
                subset["X"],
                subset["Y"],
                ax=ax,
                s=60,
                color=colores_eventos.get(
                    evento.lower(),
                    "#FFFFFF"
                ),
                edgecolors="white",
                linewidth=0.7,
                alpha=0.9,
                label=evento.title()
            )

        # --------------------------------------------------
        # RESTO DE EVENTOS
        # --------------------------------------------------

        else:

            pitch.scatter(
                subset["X"],
                subset["Y"],
                ax=ax,
                s=80,
                color=colores_eventos.get(
                    evento.lower(),
                    "#FFFFFF"
                ),
                edgecolors="white",
                linewidth=0.8,
                alpha=0.85,
                label=evento.title()
            )

    ax.legend(
        loc="upper left",
        fontsize=8,
        facecolor="#1B4332",
        edgecolor="white",
        labelcolor="white"
    )

    st.pyplot(
        fig,
        use_container_width=True
    )

else:

    st.info(
        "No hay eventos para mostrar."
    )


# =============================================================================
# GRÁFICO 2 - MAPA DE CALOR
# =============================================================================

st.divider()

st.subheader("🔥 Mapa de calor")

if not df_filtrado.empty:

    pitch, fig, ax = crear_cancha()

    # Menos subdivisiones para jugadores individuales
    bins_x = 8
    bins_y = 6

    bin_stat = pitch.bin_statistic(
        df_filtrado["X"],
        df_filtrado["Y"],
        statistic="count",
        bins=(bins_x, bins_y)
    )

    pitch.heatmap(
        bin_stat,
        ax=ax,
        cmap="Reds",
        alpha=0.65,
        edgecolors="#1B4332"
    )

    st.pyplot(
        fig,
        use_container_width=True
    )

else:

    st.info(
        "No hay eventos para generar el mapa de calor."
    )


# =============================================================================
# GRÁFICO 3 - RED DE PASES
# =============================================================================

st.divider()

st.subheader("🕸️ Red de pases")

st.warning(
    """
    Próxima versión:

    • Reconstrucción automática de conexiones
    • Detección espacial de receptor
    • Flechas direccionales
    • Grosor según frecuencia
    • Nodos por jugador
    • Integración completa con mplsoccer

    Actualmente la red antigua fue desactivada porque dependía de
    columnas 'Resultado' y 'Receptor' que no existen en el modelo
    de datos de FC Python.
    """
)
