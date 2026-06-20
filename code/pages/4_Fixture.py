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

ESCUDOS_DIR = os.path.join(BASE, "static", "escudos")

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


def buscar_escudo(nombre):
    """Busca el escudo de un equipo tolerando mayúsculas/minúsculas y extensión."""
    if not nombre or not os.path.isdir(ESCUDOS_DIR):
        return None
    candidatos = [f"{nombre}.png", f"{nombre}.jpg", f"{nombre}.jpeg", f"{nombre}.webp"]
    archivos_existentes = os.listdir(ESCUDOS_DIR)
    archivos_lower = {a.lower(): a for a in archivos_existentes}
    for candidato in candidatos:
        ruta = os.path.join(ESCUDOS_DIR, candidato)
        if os.path.exists(ruta):
            return ruta
        if candidato.lower() in archivos_lower:
            return os.path.join(ESCUDOS_DIR, archivos_lower[candidato.lower()])
    return None


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

    condicion = (
        "🏠 Local"
        if proximo["condicion"] == "Local"
        else "✈️ Visitante"
    )

    escudo_rival_proximo = buscar_escudo(rival_proximo)

    col_escudo, col_card = st.columns([1, 6])

    with col_escudo:
        if escudo_rival_proximo:
            st.image(escudo_rival_proximo, width=90)

    with col_card:
        st.markdown(
            f"""
            <div style="
                background:#1F2937;
                padding:25px;
                border-radius:15px;
                color:white;
                text-align:center;
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

else:

    st.info(
        "No hay partidos pendientes."
    )

# =========================
# HISTORIAL VS EL RIVAL
# =========================

st.divider()

if proximo is not None:

    rival_actual = proximo["rival"]

    st.subheader(
        f"📊 Historial vs {rival_actual}"
    )

    enfrentamientos = df[
        (df["rival"] == rival_actual) &
        (df["estado"] == "Jugado")
    ]

    if enfrentamientos.empty:

        st.info(
            f"Todavía no hay partidos jugados contra {rival_actual}. "
            "Va a ser el primer enfrentamiento registrado."
        )

    else:

        g_h = len(
            enfrentamientos[
                enfrentamientos["goles_favor"] >
                enfrentamientos["goles_contra"]
            ]
        )

        e_h = len(
            enfrentamientos[
                enfrentamientos["goles_favor"] ==
                enfrentamientos["goles_contra"]
            ]
        )

        p_h = len(
            enfrentamientos[
                enfrentamientos["goles_favor"] <
                enfrentamientos["goles_contra"]
            ]
        )

        gf_h = int(enfrentamientos["goles_favor"].sum())
        gc_h = int(enfrentamientos["goles_contra"].sum())

        ch1, ch2, ch3, ch4 = st.columns(4)

        ch1.metric("Enfrentamientos", len(enfrentamientos))
        ch2.metric("Récord (G-E-P)", f"{g_h}-{e_h}-{p_h}")
        ch3.metric("Goles a favor", gf_h)
        ch4.metric("Goles en contra", gc_h)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        for _, row in enfrentamientos.sort_values("fecha").iterrows():

            gf_p = int(row["goles_favor"])
            gc_p = int(row["goles_contra"])
            resultado = f"{gf_p} - {gc_p}"

            colf1, colf2, colf3 = st.columns([1, 3, 2])

            with colf1:
                st.markdown(f"Fecha {int(row['fecha'])}")

            with colf2:
                cond_p = "🏠 Local" if row["condicion"] == "Local" else "✈️ Visitante"
                st.markdown(f"{cond_p}")

            with colf3:
                if gf_p > gc_p:
                    st.success(resultado)
                elif gf_p == gc_p:
                    st.warning(resultado)
                else:
                    st.error(resultado)

else:

    st.stop()

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
