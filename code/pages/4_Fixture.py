import streamlit as st
import pandas as pd
import os

from components.layout import (
    inject_css,
    render_sidebar,
    render_header
)

st.set_page_config(
    page_title="Fixture",
    page_icon="🗓️",
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
    "Torneo Promocional Amateur 2026",
    "Centro de planificación táctica"
)

# =========================
# DATOS SIMULADOS DE RIVALES
# =========================

rivales_data = {

    "Everton": {

        "sistema": "1-4-4-2",

        "forma": "alta",

        "ataque": [
            "Juego directo sobre delantero referencia",
            "Centros tempranos desde banda derecha",
            "Segunda jugada tras pelotazo"
        ],

        "debilidades": [
            "Espacios detrás de los laterales",
            "Mal repliegue tras pérdida",
            "Problemas defendiendo cambios de orientación"
        ],

        "alertas_abp": {
            "lanzador": "N°10 - Pierna derecha",
            "rematadores": [
                "N°2",
                "N°9",
                "N°6"
            ]
        },

        "videos": [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
    },

    "CRIBA": {

        "sistema": "1-4-3-3",

        "forma": "media",

        "ataque": [
            "Asociaciones interiores",
            "Extremos muy profundos",
            "Laterales proyectados"
        ],

        "debilidades": [
            "Transiciones defensivas lentas",
            "Central izquierdo vulnerable en velocidad"
        ],

        "alertas_abp": {
            "lanzador": "N°8",
            "rematadores": [
                "N°4",
                "N°9"
            ]
        },

        "videos": [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
    }
}


# =========================
# FUNCIONES
# =========================

@st.cache_data(ttl=0)
def cargar_fixture():
    return pd.read_csv(
        os.path.join(
            BASE,
            "data",
            "fixture.csv"
        )
    )


def color_forma(forma):

    if forma == "alta":
        return "#16a34a"

    elif forma == "media":
        return "#f59e0b"

    return "#dc2626"


# =========================
# CARGA DE DATOS
# =========================

df = cargar_fixture()

jugados = df[
    df["estado"] == "Jugado"
]

pendientes = df[
    df["estado"] != "Jugado"
]

if len(pendientes) > 0:
    proximo = pendientes.iloc[0]
else:
    proximo = None


# =========================
# KPIS DEL TORNEO
# =========================

if len(jugados) > 0:

    ganados = len(
        jugados[
            jugados["goles_favor"] >
            jugados["goles_contra"]
        ]
    )

    empatados = len(
        jugados[
            jugados["goles_favor"] ==
            jugados["goles_contra"]
        ]
    )

    perdidos = len(
        jugados[
            jugados["goles_favor"] <
            jugados["goles_contra"]
        ]
    )

    gf = int(
        jugados["goles_favor"].sum()
    )

    gc = int(
        jugados["goles_contra"].sum()
    )

    puntos = (
        ganados * 3 +
        empatados
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Partidos jugados",
        len(jugados)
    )

    col2.metric(
        "Puntos",
        puntos
    )

    col3.metric(
        "Diferencia de gol",
        gf - gc
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Ganados",
        ganados
    )

    col5.metric(
        "Empatados",
        empatados
    )

    col6.metric(
        "Perdidos",
        perdidos
    )

else:

    st.info(
        "⏳ El torneo aún no comenzó."
    )

# =========================
# PARTIDO DE LA SEMANA
# =========================

st.divider()

st.subheader(
    "🎯 Partido de la Semana"
)

if proximo is not None:

    rival_proximo = proximo["rival"]

    info_rival = rivales_data.get(
        rival_proximo,
        None
    )

    color = "#6b7280"

    if info_rival:
        color = color_forma(
            info_rival["forma"]
        )

    condicion = (
        "🏠 Local"
        if proximo["condicion"] == "Local"
        else "✈️ Visitante"
    )

    st.markdown(
        f"""
        <div style="
            background:{color};
            padding:25px;
            border-radius:15px;
            color:white;
            text-align:center;
            margin-bottom:20px;
        ">
            <h2>
                Estrella de Berisso vs {rival_proximo}
            </h2>
            <h4>
                Fecha {int(proximo['fecha'])}
            </h4>
            <h4>
                {condicion}
            </h4>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# ANALISIS DEL RIVAL
# =========================

st.divider()

if proximo is not None:

    rival_actual = proximo["rival"]

    st.subheader(
        f"🧠 Informe de {rival_actual}"
    )

    if rival_actual in rivales_data:

        rival = rivales_data[
            rival_actual
        ]

    else:

        st.warning(
            f"No existe un informe cargado para {rival_actual}"
        )

        st.info(
            "Cargar sistema táctico, patrones, ABP y videos para este rival."
        )

        st.stop()

else:

    st.info(
        "No hay partidos pendientes."
    )

    st.stop()

# =========================
# ABP
# =========================

st.divider()

st.subheader(
    "🎯 Alertas Balón Parado"
)

abp = rival["alertas_abp"]

col1, col2 = st.columns(2)

with col1:

    st.info(
        f"Lanzador Principal: {abp['lanzador']}"
    )

with col2:

    st.warning(
        "Rematadores Principales"
    )

    for jugador in abp["rematadores"]:
        st.markdown(
            f"- {jugador}"
        )

# =========================
# REPOSITORIO DE VIDEO
# =========================

st.divider()

st.subheader(
    "🎥 Repositorio de Video"
)

for video in rival["videos"]:

    st.video(video)

# =========================
# PLAN DE PARTIDO
# =========================

st.divider()

st.subheader(
    "📋 Plan de Partido"
)

st.text_area(
    "Objetivos tácticos de la semana",
    placeholder="""
✓ Presionar salida del central izquierdo

✓ Buscar espalda de los laterales

✓ Evitar faltas laterales

✓ Atacar segundo palo en corners
""",
    height=200
)

# =========================
# FIXTURE COMPLETO
# =========================

st.divider()

st.subheader(
    "🗓️ Fixture Completo"
)

for _, row in df.iterrows():

    col1, col2, col3, col4 = st.columns(
        [1, 3, 3, 2]
    )

    with col1:

        st.markdown(
            f"**Fecha {int(row['fecha'])}**"
        )

    with col2:

        if row["condicion"] == "Local":

            st.markdown(
                f"🏠 **Estrella de Berisso** vs {row['rival']}"
            )

        else:

            st.markdown(
                f"✈️ {row['rival']} vs **Estrella de Berisso**"
            )

    with col3:

        if row["estado"] == "Jugado":

            gf = int(
                row["goles_favor"]
            )

            gc = int(
                row["goles_contra"]
            )

            resultado = (
                f"{gf} - {gc}"
            )

            if gf > gc:

                st.success(
                    resultado
                )

            elif gf == gc:

                st.warning(
                    resultado
                )

            else:

                st.error(
                    resultado
                )

        else:

            st.info(
                "Pendiente"
            )

    with col4:

        if row["condicion"] == "Local":

            st.markdown(
                "🟢 Local"
            )

        else:

            st.markdown(
                "🔵 Visitante"
            )

    st.divider()
