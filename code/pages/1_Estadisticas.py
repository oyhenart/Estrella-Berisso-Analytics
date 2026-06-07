import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Estadísticas · Estrella FC", page_icon="📊", layout="wide")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from components.layout import inject_css, render_sidebar, render_header
    inject_css()
    render_sidebar(BASE)
    render_header("Análisis", "Estadísticas por jugador")
except Exception:
    pass

DATA_PATH    = os.path.join(BASE, "data", "events_clean.csv")
FIXTURE_PATH = os.path.join(BASE, "data", "fixture.csv")
JUGADORES_PATH = os.path.join(BASE, "data", "Jugadores.csv")

@st.cache_data
def cargar_datos():
    df = pd.read_csv(DATA_PATH)
    df["tiempo_total"] = df["Mins"] * 60 + df["Secs"]
    return df

@st.cache_data(ttl=0)
def cargar_fixture():
    return pd.read_csv(FIXTURE_PATH)

@st.cache_data(ttl=0)
def cargar_jugadores():
    df = pd.read_csv(JUGADORES_PATH)
    df["nombre"] = df["nombre"].str.strip().str.title()
    df["posicion"] = df["posicion"].str.strip().str.title()
    return df

if not os.path.exists(DATA_PATH):
    st.info("⏳ El torneo aún no comenzó.")
    st.stop()

df       = cargar_datos()
fixture  = cargar_fixture()
jugadores_df = cargar_jugadores()

# Posición de cada jugador
pos_map = dict(zip(jugadores_df["nombre"], jugadores_df["posicion"]))

# ── Métricas por posición ─────────────────────────────────────────────────────
METRICAS_POS = {
    "Arquero":        ["despeje", "recuperacion", "pase"],
    "Defensor":       ["recuperacion", "despeje", "falta cometida"],
    "Mediocampista":  ["pase", "recuperacion", "conduccion"],
    "Delantero":      ["remate", "gol", "centro", "conduccion"],
}
COLOR_POS = {
    "Arquero":       "#60A5FA",
    "Defensor":      "#34D399",
    "Mediocampista": "#FCD34D",
    "Delantero":     "#F87171",
}
LABEL_METRICAS = {
    "pase": "Pases", "recuperacion": "Recup.", "despeje": "Despejes",
    "falta cometida": "Faltas", "conduccion": "Cond.", "remate": "Remates",
    "gol": "Goles", "centro": "Centros",
}

# ── Filtros ───────────────────────────────────────────────────────────────────
fechas_disponibles = sorted(df["fecha"].unique().tolist())
opciones_fecha = ["Todos los partidos"] + [f"Fecha {f}" for f in fechas_disponibles]

col1, col2, col3 = st.columns(3)
with col1:
    fecha_sel = st.selectbox("Partido", opciones_fecha)
with col2:
    condicion_sel = st.selectbox("Condición", ["Local y Visitante", "Local", "Visitante"])
with col3:
    jugadores_lista = ["Todos"] + sorted(df["Player"].unique().tolist())
    jugador_sel = st.selectbox("Jugador", jugadores_lista)

if fecha_sel != "Todos los partidos":
    num_fecha = int(fecha_sel.replace("Fecha ", ""))
    df_f = df[df["fecha"] == num_fecha]
else:
    num_fecha = None
    df_f = df.copy()

if condicion_sel != "Local y Visitante" and num_fecha is None:
    fechas_cond = fixture[fixture["condicion"] == condicion_sel]["fecha"].tolist()
    df_f = df_f[df_f["fecha"].isin(fechas_cond)]

st.markdown("<div style='margin:16px 0;height:1px;background:#1F2937'></div>", unsafe_allow_html=True)

# ── Vista: un jugador específico ──────────────────────────────────────────────
if jugador_sel != "Todos":
    df_j = df_f[df_f["Player"] == jugador_sel]
    posicion = pos_map.get(jugador_sel, "")
    metricas_clave = METRICAS_POS.get(posicion, ["pase", "recuperacion", "remate"])
    color = COLOR_POS.get(posicion, "#9CA3AF")

    # KPIs del jugador
    partidos = df_j["fecha"].nunique()
    minutos  = int(df_j.groupby("fecha")["Mins"].max().sum() - df_j.groupby("fecha")["Mins"].min().sum())
    eventos_totales = len(df_j)

    st.markdown(f"""
    <div style='background:#1F2937;border-left:3px solid {color};border-radius:4px;padding:14px 20px;margin-bottom:20px'>
        <div style='display:flex;gap:32px;align-items:center'>
            <div>
                <div style='font-size:0.62em;color:#6B7280;text-transform:uppercase;letter-spacing:2px'>Jugador</div>
                <div style='font-size:1.3em;font-weight:800;color:#F9FAFB'>{jugador_sel}</div>
            </div>
            <div>
                <div style='font-size:0.62em;color:#6B7280;text-transform:uppercase;letter-spacing:2px'>Posición</div>
                <div style='font-size:1em;font-weight:700;color:{color}'>{posicion or "—"}</div>
            </div>
            <div>
                <div style='font-size:0.62em;color:#6B7280;text-transform:uppercase;letter-spacing:2px'>Partidos</div>
                <div style='font-size:1em;font-weight:700;color:#F9FAFB'>{partidos}</div>
            </div>
            <div>
                <div style='font-size:0.62em;color:#6B7280;text-transform:uppercase;letter-spacing:2px'>Min. estimados</div>
                <div style='font-size:1em;font-weight:700;color:#F9FAFB'>{minutos}'</div>
            </div>
            <div>
                <div style='font-size:0.62em;color:#6B7280;text-transform:uppercase;letter-spacing:2px'>Eventos totales</div>
                <div style='font-size:1em;font-weight:700;color:#F9FAFB'>{eventos_totales}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_radar, col_detalle = st.columns([1, 1])

    with col_radar:
        st.markdown("<p style='font-size:0.65em;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:3px;margin-bottom:10px'>Perfil de rendimiento</p>", unsafe_allow_html=True)
        cats = [LABEL_METRICAS.get(m, m) for m in metricas_clave]
        vals = [len(df_j[df_j["Event"] == m]) for m in metricas_clave]
        cats_closed = cats + [cats[0]]
        vals_closed = vals + [vals[0]]
        fig = go.Figure(go.Scatterpolar(
            r=vals_closed, theta=cats_closed,
            fill="toself",
            fillcolor=color.replace(")", ",0.15)").replace("rgb", "rgba") if "rgb" in color else color + "26",
            line=dict(color=color, width=2),
            marker=dict(color=color, size=6),
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, showticklabels=True, gridcolor="#374151", color="#6B7280"),
                angularaxis=dict(gridcolor="#374151", color="#9CA3AF"),
                bgcolor="#1F2937",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF", size=12),
            margin=dict(l=20, r=20, t=20, b=20),
            height=300,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_detalle:
        st.markdown("<p style='font-size:0.65em;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:3px;margin-bottom:10px'>Métricas clave por partido</p>", unsafe_allow_html=True)

        rows = []
        for fecha in sorted(df_j["fecha"].unique()):
            df_fp = df_j[df_j["fecha"] == fecha]
            row = {"Fecha": int(fecha)}
            for m in metricas_clave:
                row[LABEL_METRICAS.get(m, m)] = len(df_fp[df_fp["Event"] == m])
            rows.append(row)

        if rows:
            tabla = pd.DataFrame(rows)
            st.dataframe(tabla, use_container_width=True, hide_index=True)

        # Actividad por minuto (compacta)
        st.markdown("<p style='font-size:0.65em;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:3px;margin:16px 0 8px 0'>Actividad por minuto</p>", unsafe_allow_html=True)
        act = df_j.groupby("Mins")["Event"].count().reset_index()
        fig2 = go.Figure(go.Bar(
            x=act["Mins"], y=act["Event"],
            marker_color=color, opacity=0.7,
            hovertemplate="Min %{x}: %{y}<extra></extra>",
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF", size=11),
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(gridcolor="#1F2937", title=""),
            yaxis=dict(gridcolor="#1F2937", title=""),
            height=180,
        )
        st.plotly_chart(fig2, use_container_width=True)

# ── Vista: todos los jugadores ────────────────────────────────────────────────
else:
    st.markdown("<p style='font-size:0.65em;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:3px;margin-bottom:12px'>Rendimiento por posición</p>", unsafe_allow_html=True)

    # Construir tabla con métricas relevantes por posición
    rows = []
    for jugador in sorted(df_f["Player"].unique()):
        df_j = df_f[df_f["Player"] == jugador]
        posicion = pos_map.get(jugador, "—")
        metricas = METRICAS_POS.get(posicion, ["pase", "recuperacion", "remate"])
        color = COLOR_POS.get(posicion, "#9CA3AF")
        partidos = df_j["fecha"].nunique()
        row = {
            "_color": color,
            "_posicion": posicion,
            "Jugador": jugador,
            "Pos.": posicion or "—",
            "PJ": partidos,
        }
        for m in ["pase","recuperacion","despeje","remate","gol","falta cometida","conduccion"]:
            row[LABEL_METRICAS.get(m, m)] = len(df_j[df_j["Event"] == m])
        rows.append(row)

    tabla_df = pd.DataFrame(rows).sort_values(["_posicion", "Jugador"])

    # Renderizar por grupo de posición
    for posicion in ["Arquero", "Defensor", "Mediocampista", "Delantero"]:
        grupo = tabla_df[tabla_df["_posicion"] == posicion]
        if grupo.empty:
            continue
        color = COLOR_POS.get(posicion, "#9CA3AF")
        metricas_pos = METRICAS_POS.get(posicion, [])
        cols_mostrar = ["Jugador", "Pos.", "PJ"] + [LABEL_METRICAS[m] for m in metricas_pos if m in LABEL_METRICAS]

        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:10px;margin:16px 0 8px 0'>
            <div style='width:3px;height:16px;background:{color};border-radius:2px'></div>
            <span style='font-size:0.72em;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:2px'>{posicion}s</span>
        </div>
        """, unsafe_allow_html=True)

        display = grupo[cols_mostrar].reset_index(drop=True)

        # Highlight de la columna más relevante para la posición
        col_highlight = LABEL_METRICAS.get(metricas_pos[0], "") if metricas_pos else ""

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                col_highlight: st.column_config.ProgressColumn(
                    col_highlight,
                    min_value=0,
                    max_value=int(display[col_highlight].max()) if col_highlight in display.columns and display[col_highlight].max() > 0 else 1,
                    format="%d",
                ) if col_highlight in display.columns else None,
            }
        )