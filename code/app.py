# ==========================
# 1) IMPORTS + UI HELPERS
# ==========================

import streamlit as st
import pandas as pd
import os
from datetime import date

from components.layout import (
    inject_css,
    render_sidebar,
    render_header
)

st.set_page_config(
    page_title="Estrella FC · Dashboard",
    page_icon="⚽",
    layout="wide"
)

inject_css()

BASE = os.path.dirname(os.path.abspath(__file__))

render_sidebar(BASE)

render_header(
    "Torneo Promocional Amateur 2026",
    "Panel de análisis"
)


# ─────────────────────────
# COMPONENTES VISUALES
# ─────────────────────────

def card(label, value, sub=None, accent=False):

    glow = """
    box-shadow:
    0 10px 28px rgba(0,0,0,.28);
    """

    accent_bg = """
    background:
    linear-gradient(
        180deg,
        rgba(226,62,62,.08),
        #111827
    );
    """ if accent else ""

    sub_html = ""

    if sub:
        sub_html = f"""
        <div style="
            margin-top:10px;
            color:#9CA3AF;
            font-size:.78rem;
        ">
        {sub}
        </div>
        """

    return f"""
    <div style="
        background:#111827;
        border:1px solid rgba(255,255,255,.04);
        border-radius:14px;
        padding:22px;
        min-height:132px;

        {glow}
        {accent_bg}

    ">

        <div style="
            color:#6B7280;
            font-size:.70rem;
            text-transform:uppercase;
            letter-spacing:2px;
        ">
        {label}
        </div>

        <div style="
            margin-top:12px;
            font-size:2.15rem;
            font-weight:800;
            color:#F8FAFC;
            line-height:1;
        ">
        {value}
        </div>

        {sub_html}

    </div>
    """


def section(title):

    st.markdown(
        f"""
        <div style="
            margin-bottom:14px;

            color:#6B7280;

            font-size:.70rem;

            font-weight:700;

            text-transform:uppercase;

            letter-spacing:3px;
        ">
        {title}
        </div>
        """,
        unsafe_allow_html=True
    )


def divider():

    st.markdown(
        """
        <div style="
            margin:30px 0;

            height:1px;

            background:
            linear-gradient(
                to right,
                rgba(255,255,255,.06),
                transparent
            );
        ">
        </div>
        """,
        unsafe_allow_html=True
    )


def insight(text, level="neutral"):

    colors = {
        "good":"#22C55E",
        "warn":"#EAB308",
        "bad":"#EF4444",
        "neutral":"#3B82F6"
    }

    return f"""
    <div style="
        background:#111827;

        border-left:4px solid {colors[level]};

        border-radius:10px;

        padding:14px 16px;

        margin-bottom:10px;

        color:#D1D5DB;

        font-size:.86rem;

        line-height:1.55;
    ">
    {text}
    </div>
    """
    # ==========================
# 2) ESTADO COMPETITIVO
# ==========================

jugados = fixture[fixture["estado"] == "Jugado"]
pendientes = fixture[fixture["estado"] == "Pendiente"]

ganados = len(
    jugados[
        jugados["goles_favor"]
        >
        jugados["goles_contra"]
    ]
)

empatados = len(
    jugados[
        jugados["goles_favor"]
        ==
        jugados["goles_contra"]
    ]
)

perdidos = len(
    jugados[
        jugados["goles_favor"]
        <
        jugados["goles_contra"]
    ]
)

puntos = ganados * 3 + empatados

gf = (
    int(jugados["goles_favor"].sum())
    if not jugados.empty
    else 0
)

gc = (
    int(jugados["goles_contra"].sum())
    if not jugados.empty
    else 0
)


def racha_visual(df):

    if df.empty:
        return "Sin datos"

    salida = ""

    colores = {
        "W":"#22C55E",
        "D":"#F59E0B",
        "L":"#EF4444"
    }

    for _, r in df.tail(3).iterrows():

        if r["goles_favor"] > r["goles_contra"]:
            res = "W"

        elif r["goles_favor"] == r["goles_contra"]:
            res = "D"

        else:
            res = "L"

        salida += f"""
        <span style="
            background:{colores[res]};
            color:#111827;

            padding:6px 10px;

            border-radius:8px;

            font-size:.78rem;

            font-weight:800;

            margin-right:6px;
        ">
        {res}
        </span>
        """

    return salida


section("Estado competitivo")


if jugados.empty:

    st.markdown(
        insight(
            "Todavía no hay partidos cargados para generar indicadores.",
            "neutral"
        ),
        unsafe_allow_html=True
    )

else:

    total_posibles = len(jugados) * 3

    efectividad = round(
        puntos / total_posibles * 100
    )

    momento = (
        "Positivo"
        if efectividad >= 55
        else "En construcción"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            card(
                "Momento",
                f"{efectividad}%",
                sub=f"{momento}",
                accent=efectividad >= 55
            ),
            unsafe_allow_html=True
        )

    with c2:

        st.markdown(
            card(
                "Producción ofensiva",
                gf,
                sub=f"{round(gf/max(len(jugados),1),1)} por partido"
            ),
            unsafe_allow_html=True
        )

    with c3:

        st.markdown(
            card(
                "Solidez defensiva",
                gc,
                sub=f"{round(gc/max(len(jugados),1),1)} recibidos"
            ),
            unsafe_allow_html=True
        )

    with c4:

        st.markdown(
            f"""
            <div style="
                background:#111827;

                border-radius:14px;

                padding:22px;

                min-height:132px;

                border:1px solid rgba(255,255,255,.04);

                box-shadow:
                0 10px 28px rgba(0,0,0,.28);
            ">

            <div style="
                color:#6B7280;

                font-size:.70rem;

                text-transform:uppercase;

                letter-spacing:2px;
            ">
            Tendencia
            </div>

            <div style="
                margin-top:18px;
            ">
                {racha_visual(jugados)}
            </div>

            <div style="
                margin-top:14px;

                color:#9CA3AF;

                font-size:.80rem;
            ">
            {ganados}G ·
            {empatados}E ·
            {perdidos}P
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


divider()
# ==========================
# 3) CARGA DE DATOS
# ==========================

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

ALERTAS_PATH = os.path.join(
    BASE,
    "data",
    "sanciones_lesiones.csv"
)


@st.cache_data
def cargar_eventos():

    if not os.path.exists(DATA_PATH):

        return pd.DataFrame()

    df = pd.read_csv(DATA_PATH)

    if (
        "Mins" in df.columns
        and
        "Secs" in df.columns
    ):

        df["tiempo_total"] = (
            df["Mins"] * 60
            +
            df["Secs"]
        )

    return df


@st.cache_data(ttl=0)
def cargar_fixture():

    if not os.path.exists(FIXTURE_PATH):

        return pd.DataFrame()

    return pd.read_csv(FIXTURE_PATH)


@st.cache_data(ttl=0)
def cargar_alertas():

    if not os.path.exists(ALERTAS_PATH):

        return pd.DataFrame()

    df = pd.read_csv(ALERTAS_PATH)

    if (
        not df.empty
        and
        "fecha_regreso" in df.columns
    ):

        df["fecha_regreso"] = pd.to_datetime(
            df["fecha_regreso"],
            dayfirst=True,
            errors="coerce"
        )

    return df


# ─────────────────────────
# CARGA GLOBAL
# ─────────────────────────

fixture = cargar_fixture()

alertas = cargar_alertas()

df = cargar_eventos()

hoy = pd.Timestamp(
    date.today()
)


# ─────────────────────────
# VALIDACIÓN MÍNIMA
# ─────────────────────────

if fixture.empty:

    st.warning(
        "No se encontró fixture.csv"
    )

    st.stop()
    # ==========================
# 4) PRÓXIMO PARTIDO
# ==========================

section("Próximo partido")


if pendientes.empty:

    st.markdown(
        insight(
            "No hay partidos pendientes cargados.",
            "neutral"
        ),
        unsafe_allow_html=True
    )

else:

    partido = pendientes.iloc[0]

    condicion = str(
        partido["condicion"]
    )

    rival = str(
        partido["rival"]
    )

    fecha = int(
        partido["fecha"]
    )

    icono = (
        "🏠"
        if condicion == "Local"
        else "✈️"
    )

    color = (
        "#22C55E"
        if condicion == "Local"
        else "#60A5FA"
    )

    col_match, col_info = st.columns(
        [1.4, 1]
    )

    with col_match:

        st.markdown(
            f"""
            <div style="

                background:#111827;

                border-radius:14px;

                padding:26px;

                min-height:180px;

                border:1px solid rgba(255,255,255,.04);

                box-shadow:
                0 10px 28px rgba(0,0,0,.28);

            ">

                <div style="
                    color:#6B7280;

                    text-transform:uppercase;

                    letter-spacing:2px;

                    font-size:.72rem;

                    margin-bottom:10px;
                ">
                    Fecha {fecha}
                </div>

                <div style="
                    font-size:2rem;

                    font-weight:800;

                    color:#F9FAFB;
                ">
                    {icono}
                    vs
                    <span style="
                    color:#E23E3E">
                    {rival}
                    </span>
                </div>

                <div style="
                    margin-top:18px;
                ">

                    <span style="

                        background:{color}20;

                        color:{color};

                        padding:8px 14px;

                        border-radius:10px;

                        font-size:.82rem;

                        font-weight:700;

                    ">
                        {condicion}
                    </span>

                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with col_info:

        st.markdown(
            """
            <div style="

                background:#111827;

                border-radius:14px;

                padding:22px;

                min-height:180px;

                border:1px solid rgba(255,255,255,.04);

                box-shadow:
                0 10px 28px rgba(0,0,0,.28);

            ">

            <div style="
                color:#6B7280;

                text-transform:uppercase;

                letter-spacing:2px;

                font-size:.72rem;

                margin-bottom:16px;
            ">
            Atención previa
            </div>

            <div style="
                color:#D1D5DB;

                line-height:1.8;

                font-size:.88rem;
            ">

            • Confirmar disponibilidad<br>

            • Preparar video rival<br>

            • Revisar tendencia reciente

            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


divider()
# ==========================
# 5) DISPONIBILIDAD
# ==========================

section("Disponibilidad del plantel")


bajas_tipos = [
    "lesión",
    "lesion",
    "sanción",
    "sancion",
    "roja directa"
]

if alertas.empty:

    st.markdown(
        insight(
            "No hay registros de alertas cargados.",
            "neutral"
        ),
        unsafe_allow_html=True
    )

else:

    bajas = alertas[
        alertas["tipo"]
        .str
        .lower()
        .isin(
            bajas_tipos
        )
    ]

    bajas_activas = bajas[
        (
            bajas["fecha_regreso"].isna()
        )
        |
        (
            bajas["fecha_regreso"]
            >=
            hoy
        )
    ]

    amarillas = alertas[
        alertas["tipo"]
        .str
        .lower()
        ==
        "amarilla"
    ]

    riesgo = []

    if not amarillas.empty:

        for jugador, grupo in amarillas.groupby(
            "nombre"
        ):

            sanciones = len(
                bajas[
                    bajas["nombre"]
                    ==
                    jugador
                ]
            )

            umbral = [
                5,
                4,
                3,
                2
            ][
                min(
                    sanciones,
                    3
                )
            ]

            if len(grupo) >= umbral - 1:

                riesgo.append(
                    jugador.title()
                )

    disponibles = max(
        0,
        20
        -
        len(
            bajas_activas
        )
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown(
            card(
                "Disponibles",
                disponibles,
                "aptos"
            ),
            unsafe_allow_html=True
        )

    with c2:

        st.markdown(
            card(
                "Bajas",
                len(
                    bajas_activas
                ),
                "no disponibles",
                accent=(
                    len(
                        bajas_activas
                    ) > 0
                )
            ),
            unsafe_allow_html=True
        )

    with c3:

        st.markdown(
            card(
                "Riesgo",
                len(
                    riesgo
                ),
                "suspensión"
            ),
            unsafe_allow_html=True
        )

    st.markdown(
        "<div style='height:18px'></div>",
        unsafe_allow_html=True
    )

    detalle = ""

    for _, row in bajas_activas.iterrows():

        icon = (
            "🤕"
            if (
                row["tipo"]
                .lower()
                in [
                    "lesión",
                    "lesion"
                ]
            )
            else "🟥"
        )

        regreso = (
            row["fecha_regreso"]
            .strftime(
                "%d/%m"
            )
            if pd.notna(
                row["fecha_regreso"]
            )
            else "Sin fecha"
        )

        detalle += f"""
        <div style='
            padding:10px 0;
            border-bottom:
            1px solid rgba(255,255,255,.04);
        '>

        <span style='color:#F9FAFB'>
        {icon}
        {row["nombre"].title()}
        </span>

        <span style='
            float:right;
            color:#9CA3AF;
        '>

        {row["tipo"]}

        ·

        {regreso}

        </span>

        </div>
        """

    for jugador in riesgo:

        detalle += f"""
        <div style='
            padding:10px 0;

            color:#FBBF24;

            border-bottom:
            1px solid rgba(255,255,255,.04);
        '>

        ⚠
        {jugador}

        · riesgo suspensión

        </div>
        """

    if detalle == "":

        detalle = """
        <div style='
        color:#22C55E;
        padding:10px 0;
        '>

        ✓ Plantel completo

        </div>
        """

    st.markdown(
        f"""
        <div style="

            background:#111827;

            border-radius:14px;

            padding:22px;

            border:1px solid rgba(255,255,255,.04);

            box-shadow:
            0 10px 28px rgba(0,0,0,.28);

        ">

        {detalle}

        </div>
        """,
        unsafe_allow_html=True
    )


divider()
# ==========================
# 6) ÚLTIMO PARTIDO
# ==========================

section("Último partido analizado")


if df.empty:

    st.markdown(
        insight(
            "Las estadísticas aparecerán luego del primer partido cargado.",
            "neutral"
        ),
        unsafe_allow_html=True
    )

else:

    ultima_fecha = (
        df["fecha"]
        .max()
    )

    df_ultimo = df[
        df["fecha"]
        ==
        ultima_fecha
    ]

    rival_row = jugados[
        jugados["fecha"]
        ==
        ultima_fecha
    ]

    rival = (
        rival_row["rival"]
        .values[0]
        if len(rival_row)
        else f"Fecha {ultima_fecha}"
    )

    pases = len(
        df_ultimo[
            df_ultimo["Event"]
            ==
            "pase"
        ]
    )

    perdidas = len(
        df_ultimo[
            df_ultimo["Event"]
            ==
            "perdida"
        ]
    )

    recuperaciones = len(
        df_ultimo[
            df_ultimo["Event"]
            ==
            "recuperacion"
        ]
    )

    jugadores = (
        df_ultimo["Player"]
        .nunique()
    )

    ratio = (
        round(
            pases
            /
            perdidas,
            1
        )
        if perdidas > 0
        else "—"
    )

    st.markdown(
        f"""
        <div style="
            color:#9CA3AF;

            margin-bottom:18px;

            font-size:.9rem;
        ">

        Rival analizado:

        <span style="
        color:#F9FAFB;
        font-weight:700">

        {rival}

        </span>

        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            card(
                "Circulación",
                pases,
                "acciones de pase"
            ),
            unsafe_allow_html=True
        )

    with c2:

        nivel = (
            "alta"
            if ratio != "—"
            and ratio >= 5
            else "media"
        )

        st.markdown(
            card(
                "Cuidado balón",
                ratio,
                nivel
            ),
            unsafe_allow_html=True
        )

    with c3:

        st.markdown(
            card(
                "Recuperaciones",
                recuperaciones,
                "fase defensiva"
            ),
            unsafe_allow_html=True
        )

    with c4:

        st.markdown(
            card(
                "Participación",
                jugadores,
                "jugadores activos"
            ),
            unsafe_allow_html=True
        )

    st.markdown(
        "<div style='height:22px'></div>",
        unsafe_allow_html=True
    )


    # ──────────────────────
    # INFLUENCIA EN EL JUEGO
    # ──────────────────────

    section(
        "Influencia en el juego"
    )

    top = (
        df_ultimo
        .groupby("Player")
        ["Event"]
        .count()
        .sort_values(
            ascending=False
        )
        .head(5)
    )

    contenido = ""

    maximo = top.max()

    for jugador, valor in top.items():

        ancho = int(
            valor
            /
            maximo
            *
            100
        )

        contenido += f"""

        <div style='
            margin-bottom:14px;
        '>

            <div style='
                display:flex;

                justify-content:
                space-between;

                margin-bottom:6px;
            '>

                <span style='
                color:#F9FAFB;
                font-weight:600'>
                {jugador}
                </span>

                <span style='
                color:#9CA3AF'>
                {valor}
                </span>

            </div>

            <div style='
                background:#1F2937;

                height:6px;

                border-radius:99px;
            '>

                <div style='
                    width:{ancho}%;

                    background:#E23E3E;

                    height:100%;

                    border-radius:99px;
                '>
                </div>

            </div>

        </div>
        """

    st.markdown(
        f"""
        <div style="
            background:#111827;

            border-radius:14px;

            padding:20px;

            border:1px solid rgba(255,255,255,.04);

            box-shadow:
            0 10px 28px rgba(0,0,0,.28);

        ">

        {contenido}

        </div>
        """,
        unsafe_allow_html=True
    )


divider()
# ==========================
# 7) CONCLUSIONES
# ==========================

section(
    "Conclusiones del análisis"
)


if df.empty:

    st.markdown(
        insight(
            "Todavía no hay eventos suficientes para generar observaciones.",
            "neutral"
        ),
        unsafe_allow_html=True
    )

else:

    conclusiones = []


    # ─────────────────────
    # CUIDADO DE BALÓN
    # ─────────────────────

    if ratio != "—":

        if ratio >= 5:

            conclusiones.append(
                (
                    "good",
                    "Buena relación pase / pérdida. El equipo sostuvo circulación con baja pérdida relativa."
                )
            )

        elif ratio >= 3:

            conclusiones.append(
                (
                    "warn",
                    "Relación pase / pérdida intermedia. Hubo secuencias de posesión pero con interrupciones."
                )
            )

        else:

            conclusiones.append(
                (
                    "bad",
                    "Relación pase / pérdida baja. El volumen de pérdidas condicionó continuidad."
                )
            )


    # ─────────────────────
    # RECUPERACIONES
    # ─────────────────────

    if recuperaciones > 25:

        conclusiones.append(
            (
                "good",
                f"{recuperaciones} recuperaciones registradas. Alta frecuencia de recuperación."
            )
        )

    elif recuperaciones < 10:

        conclusiones.append(
            (
                "warn",
                f"{recuperaciones} recuperaciones registradas. Revisar contexto del partido."
            )
        )


    # ─────────────────────
    # DESPEJES
    # ─────────────────────

    despejes = len(
        df_ultimo[
            df_ultimo["Event"]
            ==
            "despeje"
        ]
    )

    if despejes >= 15:

        conclusiones.append(
            (
                "warn",
                f"{despejes} despejes detectados. El partido presentó tramos de presión defensiva."
            )
        )


    # ─────────────────────
    # DISCIPLINA
    # ─────────────────────

    faltas = len(
        df_ultimo[
            df_ultimo["Event"]
            ==
            "falta cometida"
        ]
    )

    if faltas >= 8:

        conclusiones.append(
            (
                "warn",
                f"{faltas} faltas cometidas. Incremento del riesgo disciplinario."
            )
        )


    # ─────────────────────
    # JUGADOR REFERENCIA
    # ─────────────────────

    if recuperaciones > 0:

        top_rec = (
            df_ultimo[
                df_ultimo["Event"]
                ==
                "recuperacion"
            ]
            .groupby(
                "Player"
            )
            .size()
        )

        if not top_rec.empty:

            jugador = (
                top_rec
                .idxmax()
            )

            cantidad = (
                int(
                    top_rec.max()
                )
            )

            conclusiones.append(
                (
                    "neutral",
                    f"{jugador} lideró recuperaciones ({cantidad})."
                )
            )


    if len(
        conclusiones
    ) == 0:

        conclusiones.append(
            (
                "neutral",
                "No se detectaron observaciones relevantes para este partido."
            )
        )


    izquierda, derecha = st.columns(
        [1.5, 1]
    )


    with izquierda:

        html = ""

        for nivel, texto in conclusiones:

            html += insight(
                texto,
                nivel
            )

        st.markdown(
            html,
            unsafe_allow_html=True
        )


    with derecha:

        resumen = f"""

        <div style="

            background:#111827;

            border-radius:14px;

            padding:22px;

            border:1px solid rgba(255,255,255,.04);

            box-shadow:
            0 10px 28px rgba(0,0,0,.28);

        ">

            <div style="
                color:#6B7280;

                text-transform:uppercase;

                letter-spacing:2px;

                font-size:.72rem;

                margin-bottom:18px;
            ">

            Resumen

            </div>

            <div style="
                color:#F9FAFB;

                font-size:1.1rem;

                line-height:1.9;
            ">

            Pases:
            <b>{pases}</b>

            <br>

            Pérdidas:
            <b>{perdidas}</b>

            <br>

            Recuperaciones:
            <b>{recuperaciones}</b>

            <br>

            Participación:
            <b>{jugadores}</b>

            </div>

        </div>

        """

        st.markdown(
            resumen,
            unsafe_allow_html=True
        )


divider()
