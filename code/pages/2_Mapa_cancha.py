# Imports
import streamlit as st
import pandas as pd
import numpy as np
import os

from mplsoccer import Pitch
import matplotlib.pyplot as plt

from components.layout import (
    inject_css,
    render_sidebar
)

# ── Configuración de Página ─────────────────────────────────────────

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

# ── Rutas de Archivos ──────────────────────────────────────────────

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

# ── Carga de Datos ────────────────────────────────────────────────

@st.cache_data
def cargar_datos():

    df = pd.read_csv(DATA_PATH)

    df["Mins"] = pd.to_numeric(
        df["Mins"],
        errors="coerce"
    ).fillna(0)

    df["Secs"] = pd.to_numeric(
        df["Secs"],
        errors="coerce"
    ).fillna(0)

    df["tiempo_total"] = (
        df["Mins"] * 60
        + df["Secs"]
    )

    for col in ["X", "Y", "X2", "Y2"]:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    return df

# ── Encabezado ────────────────────────────────────────────────────

st.markdown(
    """
    <div style='margin-bottom:28px'>
        <p style='font-size:0.72em;
                  font-weight:600;
                  color:#E63946;
                  text-transform:uppercase;
                  letter-spacing:3px;
                  margin:0 0 6px 0'>
            Análisis Táctico
        </p>

        <h1 style='font-size:2em;
                   font-weight:800;
                   margin:0;
                   color:#EEEEEE;
                   letter-spacing:-0.5px'>
            Mapa de eventos y dinámica de pases
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

if not os.path.exists(DATA_PATH):

    st.info(
        "No se encontró events_clean.csv"
    )

    st.stop()

if not os.path.exists(FIXTURE_PATH):

    st.info(
        "No se encontró fixture.csv"
    )

    st.stop()

df = cargar_datos()

fixture = pd.read_csv(
    FIXTURE_PATH
)

df = cargar_datos()

fixture = pd.read_csv(
    FIXTURE_PATH
)

# ── Clasificación Automática de Pases ─────────────────────────────

def clasificar_pases(df):

    df = df.copy()

    df["pase_ok"] = False

    eventos_continuidad = {
        "pase",
        "centro",
        "conduccion",
        "corner",
        "remate",
        "tiro libre",
        "falta recibida"
    }

    eventos_corte = {
        "perdida",
        "despeje",
        "recuperacion"
    }

    tolerancia = 8

    for i in range(len(df)):

        fila = df.iloc[i]

        if str(fila["Event"]).lower() != "pase":
            continue

        if pd.isna(fila["X2"]) or pd.isna(fila["Y2"]):
            continue

        destino_x = fila["X2"]
        destino_y = fila["Y2"]

        limite = min(i + 4, len(df))

        for j in range(i + 1, limite):

            siguiente = df.iloc[j]

            if pd.isna(siguiente["X"]) or pd.isna(siguiente["Y"]):
                continue

            distancia = np.sqrt(
                (destino_x - siguiente["X"])**2 +
                (destino_y - siguiente["Y"])**2
            )

            if distancia > tolerancia:
                continue

            evento_sig = str(
                siguiente["Event"]
            ).lower()

            if evento_sig in eventos_continuidad:

                df.at[
                    df.index[i],
                    "pase_ok"
                ] = True

                break

            if evento_sig in eventos_corte:
                break

    return df

# ── Filtros ───────────────────────────────────────────────────────

fechas_disponibles = sorted(
    df["fecha"].unique().tolist()
)

opciones_fecha = (
    ["Todos los partidos"]
    +
    [f"Fecha {f}" for f in fechas_disponibles]
)

col1, col2, col3 = st.columns(3)

with col1:

    fecha_sel = st.selectbox(
        "Partido",
        opciones_fecha
    )

with col2:

    condicion_sel = st.selectbox(
        "Condición",
        [
            "Local y Visitante",
            "Local",
            "Visitante"
        ]
    )

with col3:

    jugador_sel = st.selectbox(
        "Jugador",
        ["Todos"]
        +
        sorted(
            df["Player"]
            .dropna()
            .unique()
            .tolist()
        )
    )

# Filtro de eventos
eventos_disponibles = sorted(
    df["Event"]
    .dropna()
    .unique()
    .tolist()
)

default_eventos = (
    ["pase"]
    if "pase" in eventos_disponibles
    else eventos_disponibles[:1]
)

eventos_sel = st.multiselect(
    "Eventos",
    eventos_disponibles,
    default=default_eventos
)

st.divider()

# ── Aplicar Filtros ───────────────────────────────────────────────

if fecha_sel != "Todos los partidos":

    num_fecha = int(
        fecha_sel.replace(
            "Fecha ",
            ""
        )
    )

    df_filtrado = df[
        df["fecha"] == num_fecha
    ].copy()

else:

    df_filtrado = df.copy()

if (
    condicion_sel != "Local y Visitante"
    and fecha_sel == "Todos los partidos"
):

    fechas_cond = fixture[
        fixture["condicion"]
        == condicion_sel
    ]["fecha"].tolist()

    df_filtrado = df_filtrado[
        df_filtrado["fecha"]
        .isin(fechas_cond)
    ]

df_filtrado = df_filtrado[
    df_filtrado["Event"]
    .isin(eventos_sel)
]

if jugador_sel != "Todos":

    df_filtrado = df_filtrado[
        df_filtrado["Player"]
        == jugador_sel
    ]

df_filtrado = clasificar_pases(
    df_filtrado
)

# ── Configuración de Cancha ───────────────────────────────────────

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

    fig.set_facecolor(
        "#1B4332"
    )

    return pitch, fig, ax

# ── Limpieza Final de Coordenadas ────────────────────────────────

for col in ["X", "Y", "X2", "Y2"]:

    if col in df_filtrado.columns:

        df_filtrado[col] = pd.to_numeric(
            df_filtrado[col],
            errors="coerce"
        )

# =============================================================================
# MAPA DE EVENTOS
# =============================================================================

st.subheader(
    "📍 Ubicación de eventos"
)

if not df_filtrado.empty:

    pitch, fig, ax = crear_cancha()

    colores_eventos = {

        "recuperacion": "#34D399",
        "perdida": "#F87171",
        "conduccion": "#A78BFA",
        "tiro libre": "#FCD34D",
        "remate": "#FB923C",
        "despeje": "#9CA3AF",
        "corner": "#F9A8D4",
        "falta recibida": "#6EE7B7",
        "falta cometida": "#FCA5A5"
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

        # ------------------------------------------------------
        # PASES
        # ------------------------------------------------------

        if evento.lower() == "pase":

            subset_flechas = subset[
                subset["X2"].notna()
                &
                subset["Y2"].notna()
            ]

            pases_ok = subset_flechas[
                subset_flechas["pase_ok"]
            ]

            pases_bad = subset_flechas[
                ~subset_flechas["pase_ok"]
            ]

            if not pases_ok.empty:

                pitch.arrows(
                    pases_ok["X"],
                    pases_ok["Y"],
                    pases_ok["X2"],
                    pases_ok["Y2"],
                    ax=ax,
                    color="#22C55E",
                    width=2,
                    alpha=0.85
                )

            if not pases_bad.empty:

                pitch.arrows(
                    pases_bad["X"],
                    pases_bad["Y"],
                    pases_bad["X2"],
                    pases_bad["Y2"],
                    ax=ax,
                    color="#EF4444",
                    width=2,
                    alpha=0.85
                )

            continue

        # ------------------------------------------------------
        # CENTROS
        # ------------------------------------------------------

        if evento.lower() == "centro":

            subset_flechas = subset[
                subset["X2"].notna()
                &
                subset["Y2"].notna()
            ]

            pitch.arrows(
                subset_flechas["X"],
                subset_flechas["Y"],
                subset_flechas["X2"],
                subset_flechas["Y2"],
                ax=ax,
                color="#67E8F9",
                width=2,
                alpha=0.9
            )

            continue

        # ------------------------------------------------------
        # RESTO
        # ------------------------------------------------------

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
            alpha=0.9,
            label=evento
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
# MAPA DE CALOR
# =============================================================================

st.divider()

if jugador_sel != "Todos":

    st.subheader(
        f"🔥 Mapa de calor - {jugador_sel}"
    )

else:

    st.subheader(
        "🔥 Mapa de calor del equipo"
    )

st.subheader(
    "🔥 Mapa de calor"
)

if not df_filtrado.empty:

    pitch, fig, ax = crear_cancha()

    bin_stat = pitch.bin_statistic(
        df_filtrado["X"],
        df_filtrado["Y"],
        statistic="count",
        bins=(8, 6)
    )

    pitch.heatmap(
        bin_stat,
        ax=ax,
        cmap="Reds",
        alpha=0.55,
        zorder=1
    )

    # Redibujar líneas arriba del heatmap
    pitch.draw(
        ax=ax
    )

    st.pyplot(
        fig,
        use_container_width=True
    )

else:

    st.info(
        "No hay eventos para generar el mapa de calor."
    )

# Red de pases
def detectar_conexiones(df):

    conexiones = []

    pases = df[
        (df["Event"] == "pase")
        &
        (df["pase_ok"] == True)
    ]

    for i in range(len(pases)):

        fila = pases.iloc[i]

        jugador_origen = fila["Player"]

        destino_x = fila["X2"]
        destino_y = fila["Y2"]

        limite = min(
            fila.name + 4,
            len(df)
        )

        siguientes = df.loc[
            fila.name + 1 :
            limite
        ]

        mejor_jugador = None
        mejor_dist = 999

        for _, sig in siguientes.iterrows():

            if pd.isna(sig["X"]):
                continue

            distancia = np.sqrt(
                (destino_x - sig["X"])**2 +
                (destino_y - sig["Y"])**2
            )

            if distancia < mejor_dist:

                mejor_dist = distancia
                mejor_jugador = sig["Player"]

        if (
            mejor_jugador is not None
            and mejor_jugador != jugador_origen
        ):

            conexiones.append(
                (
                    jugador_origen,
                    mejor_jugador
                )
            )

    return pd.DataFrame(
        conexiones,
        columns=[
            "origen",
            "destino"
        ]
    )

#Red de pases completa
# =============================================================================
# RED DE PASES
# =============================================================================

st.divider()

st.subheader("🕸️ Red de pases")

if not df_filtrado.empty:

    conexiones = detectar_conexiones(df_filtrado)

    if conexiones.empty:

        st.info(
            "No se detectaron conexiones de pase."
        )

    else:

        pitch, fig, ax = crear_cancha()

        # ---------------------------------------------------------
        # POSICIÓN PROMEDIO DE CADA JUGADOR
        # ---------------------------------------------------------

        posiciones = (
            df_filtrado
            .groupby("Player")
            .agg({
                "X": "mean",
                "Y": "mean"
            })
            .reset_index()
        )

        # ---------------------------------------------------------
        # FRECUENCIA DE CONEXIONES
        # ---------------------------------------------------------

        conexiones_count = (
            conexiones
            .groupby(
                ["origen", "destino"]
            )
            .size()
            .reset_index(name="cantidad")
        )

        # ---------------------------------------------------------
        # DIBUJAR CONEXIONES
        # ---------------------------------------------------------

        for _, fila in conexiones_count.iterrows():

            origen = fila["origen"]
            destino = fila["destino"]
            cantidad = fila["cantidad"]

            pos_origen = posiciones[
                posiciones["Player"] == origen
            ]

            pos_destino = posiciones[
                posiciones["Player"] == destino
            ]

            if (
                pos_origen.empty
                or pos_destino.empty
            ):
                continue

            x1 = pos_origen["X"].iloc[0]
            y1 = pos_origen["Y"].iloc[0]

            x2 = pos_destino["X"].iloc[0]
            y2 = pos_destino["Y"].iloc[0]

            pitch.lines(
                x1,
                y1,
                x2,
                y2,
                ax=ax,
                lw=max(
                    1,
                    cantidad * 1.5
                ),
                color="#4ADE80",
                alpha=0.75,
                zorder=2
            )

        # ---------------------------------------------------------
        # DIBUJAR NODOS
        # ---------------------------------------------------------

        pitch.scatter(
            posiciones["X"],
            posiciones["Y"],
            ax=ax,
            s=600,
            color="#2563EB",
            edgecolors="white",
            linewidth=2,
            zorder=3
        )

        # ---------------------------------------------------------
        # NOMBRE DEL JUGADOR
        # ---------------------------------------------------------

        for _, fila in posiciones.iterrows():

            ax.text(
                fila["X"],
                fila["Y"],
                fila["Player"],
                color="white",
                fontsize=8,
                ha="center",
                va="center",
                weight="bold",
                zorder=4
            )

        st.pyplot(
            fig,
            use_container_width=True
        )
