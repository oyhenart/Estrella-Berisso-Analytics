import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

from components.layout import (
    inject_css,
    render_sidebar,
    render_header
)

st.set_page_config(
    page_title="Estadísticas · Estrella FC",
    page_icon="📊",
    layout="wide"
)

inject_css()

BASE = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

render_sidebar(BASE)

render_header(
    "Análisis",
    "Estadísticas por jugador"
)

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


@st.cache_data
def cargar_datos():
    df = pd.read_csv(DATA_PATH)
    df["tiempo_total"] = (
        df["Mins"] * 60
        + df["Secs"]
    )
    return df


@st.cache_data
def cargar_fixture():
    return pd.read_csv(FIXTURE_PATH)


if not os.path.exists(DATA_PATH):
    st.info("⏳ El torneo aún no comenzó.")
    st.stop()

df = cargar_datos()
fixture = cargar_fixture()

# =====================
# FILTROS
# =====================

col1, col2, col3 = st.columns(3)

with col1:

    fechas = sorted(
        df["fecha"].unique().tolist()
    )

    fecha_sel = st.selectbox(
        "Partido",
        ["Todos los partidos"]
        + [f"Fecha {x}" for x in fechas]
    )

with col2:

    condicion_sel = st.selectbox(
        "Condición",
        ["Local y Visitante",
         "Local",
         "Visitante"]
    )

with col3:

    jugador_sel = st.selectbox(
        "Jugador",
        ["Todos"]
        + sorted(
            df["Player"].unique().tolist()
        )
    )

if fecha_sel != "Todos los partidos":

    num_fecha = int(
        fecha_sel.replace(
            "Fecha ",
            ""
        )
    )

    df_filtrado = df[
        df["fecha"] == num_fecha
    ]

else:

    num_fecha = None
    df_filtrado = df.copy()

if (
    condicion_sel != "Local y Visitante"
    and num_fecha is None
):

    fechas_cond = fixture[
        fixture["condicion"] == condicion_sel
    ]["fecha"].tolist()

    df_filtrado = df_filtrado[
        df_filtrado["fecha"].isin(
            fechas_cond
        )
    ]

if jugador_sel != "Todos":

    df_filtrado = df_filtrado[
        df_filtrado["Player"]
        == jugador_sel
    ]

st.divider()

# =====================
# KPIs
# =====================

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Pases",
    len(
        df_filtrado[
            df_filtrado["Event"] == "pase"
        ]
    )
)

c2.metric(
    "Recuperaciones",
    len(
        df_filtrado[
            df_filtrado["Event"]
            == "recuperacion"
        ]
    )
)

c3.metric(
    "Faltas",
    len(
        df_filtrado[
            df_filtrado["Event"]
            == "falta cometida"
        ]
    )
)

c4.metric(
    "Remates",
    len(
        df_filtrado[
            df_filtrado["Event"]
            == "remate"
        ]
    )
)

c5.metric(
    "Goles",
    len(
        df_filtrado[
            df_filtrado["Event"]
            == "gol"
        ]
    )
)

st.divider()

# =====================
# GRAFICOS
# =====================

HIGHLIGHT = "#E23E3E"
NEUTRAL = "#374151"

col_izq, col_der = st.columns(2)

with col_izq:

    st.subheader(
        "Eventos por tipo"
    )

    conteo = (
        df_filtrado["Event"]
        .value_counts()
        .reset_index()
    )

    conteo.columns = [
        "Evento",
        "Cantidad"
    ]

    colors = [
        HIGHLIGHT if i == 0 else NEUTRAL
        for i in range(len(conteo))
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=conteo["Cantidad"],
            y=conteo["Evento"],
            orientation="h",
            marker_color=colors
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=350
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with col_der:

    st.subheader(
        "Participación por jugador"
    )

    part = (
        df_filtrado
        .groupby("Player")["Event"]
        .count()
        .sort_values(
            ascending=False
        )
        .reset_index()
    )

    part.columns = [
        "Jugador",
        "Eventos"
    ]

    colors = [
        HIGHLIGHT if i == 0 else NEUTRAL
        for i in range(len(part))
    ]

    fig2 = go.Figure()

    fig2.add_trace(
        go.Bar(
            x=part["Jugador"],
            y=part["Eventos"],
            marker_color=colors
        )
    )

    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=350
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

st.divider()

# =====================
# ACTIVIDAD TEMPORAL
# =====================

st.subheader(
    "Actividad durante el partido"
)

actividad = (
    df_filtrado
    .groupby("Mins")["Event"]
    .count()
    .reset_index()
)

fig3 = go.Figure()

fig3.add_trace(
    go.Bar(
        x=actividad["Mins"],
        y=actividad["Event"]
    )
)

fig3.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=300
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

st.divider()

st.subheader(
    "Detalle de eventos"
)

st.dataframe(
    df_filtrado[
        [
            "fecha",
            "Player",
            "Event",
            "Mins",
            "Secs",
            "X",
            "Y"
        ]
    ],
    use_container_width=True,
    hide_index=True
)
