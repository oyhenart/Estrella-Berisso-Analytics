"""
8_Player_review.py  —  Estrella FC · Player Review
====================================================
Pantalla inicial: escudo centrado + dropdown de jugadores.
Una vez seleccionado un jugador:
  · Columna izquierda (30%): foto, ficha, métricas clave, radar plotly
  · Columna derecha  (70%): videos embebidos de ese jugador

CSV requerido: data/videos_jugadores.csv
  columnas: jugador, titulo, youtube_id, fecha, descripcion
"""

import os
import base64
import mimetypes

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Player Review · Estrella FC",
    page_icon="🎬",
    layout="wide",
)

from components.layout import inject_css, render_sidebar, render_mobile_nav
inject_css()
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
render_sidebar(BASE)
render_mobile_nav()

# ── Rutas ─────────────────────────────────────────────────────────────────────
FOTOS_DIR      = os.path.join(BASE, "static", "fotos")
DATA_PATH      = os.path.join(BASE, "data", "events_clean.csv")
JUG_PATH       = os.path.join(BASE, "data", "Jugadores.csv")
SANC_PATH      = os.path.join(BASE, "data", "sanciones_lesiones.csv")
VIDEOS_JUG_CSV = os.path.join(BASE, "data", "videos_jugadores.csv")
ESCUDO         = os.path.join(BASE, "static", "escudo.png")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.pr-label {
    font-size: .58em; color: #6B7280;
    text-transform: uppercase; letter-spacing: 3px;
}
.pr-valor {
    font-size: 1em; font-weight: 800; color: #F9FAFB;
}
.pr-section {
    font-size: .60em; font-weight: 700; color: #4B5563;
    text-transform: uppercase; letter-spacing: 3px;
    border-bottom: 1px solid #1F2937;
    padding-bottom: 5px; margin: 14px 0 10px 0;
}
.pr-stat-card {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 8px;
    padding: 10px 12px;
    text-align: center;
    margin-bottom: 6px;
}
.pr-stat-num   { font-size: 1.6em; font-weight: 800; color: #F9FAFB; }
.pr-stat-label { font-size: .58em; color: #6B7280; text-transform: uppercase; letter-spacing: 2px; }
.pr-video-title {
    font-size: .92em; font-weight: 700; color: #F9FAFB; margin-bottom: 2px;
}
.pr-video-desc  {
    font-size: .78em; color: #9CA3AF; margin-bottom: 10px;
}
.badge { display:inline-block; border-radius:4px; padding:2px 7px; font-size:.68em; font-weight:700; }
.badge-verde { background:#064e3b; color:#34D399; }
.badge-rojo  { background:#450a0a; color:#F87171; }
.badge-amari { background:#451a03; color:#FBBF24; }
</style>
""", unsafe_allow_html=True)

# ── Constantes ────────────────────────────────────────────────────────────────
COLOR_POS = {
    "Arquero":       "#60A5FA",
    "Defensor":      "#34D399",
    "Mediocampista": "#FBBF24",
    "Delantero":     "#F87171",
}

METRICAS_POS = {
    "Arquero":       ["despeje", "recuperacion", "pase"],
    "Defensor":      ["recuperacion", "despeje", "falta cometida"],
    "Mediocampista": ["pase", "recuperacion", "conduccion"],
    "Delantero":     ["remate", "gol", "centro", "conduccion"],
}

LABEL_METRICAS = {
    "pase": "Pases", "recuperacion": "Recuperac.", "despeje": "Despejes",
    "falta cometida": "Faltas", "conduccion": "Cond.", "remate": "Remates",
    "gol": "Goles", "centro": "Centros",
}

ESCALA_RADAR = {
    "pase": 136, "recuperacion": 63, "conduccion": 22,
    "despeje": 65, "falta cometida": 8, "remate": 8,
    "gol": 2, "centro": 21,
}

# ── Carga de datos ────────────────────────────────────────────────────────────
@st.cache_data(ttl=0)
def cargar_jugadores():
    df = pd.read_csv(JUG_PATH)
    df["nombre"]   = df["nombre"].str.strip().str.title()
    df["posicion"] = df["posicion"].str.strip().str.title()
    if "edad" not in df.columns:
        df["edad"] = "—"
    return df

@st.cache_data(ttl=0)
def cargar_eventos():
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame()
    df = pd.read_csv(DATA_PATH)
    df["Mins"] = pd.to_numeric(df["Mins"], errors="coerce")
    df["Secs"] = pd.to_numeric(df["Secs"], errors="coerce")
    return df

@st.cache_data(ttl=0)
def cargar_alertas():
    if not os.path.exists(SANC_PATH):
        return pd.DataFrame()
    df = pd.read_csv(SANC_PATH)
    if not df.empty and "fecha_regreso" in df.columns:
        df["fecha_regreso"] = pd.to_datetime(df["fecha_regreso"], dayfirst=True, errors="coerce")
    return df

@st.cache_data(ttl=0)
def cargar_videos_jugadores():
    if not os.path.exists(VIDEOS_JUG_CSV):
        return pd.DataFrame(columns=["jugador","titulo","youtube_id","fecha","descripcion"])
    df = pd.read_csv(VIDEOS_JUG_CSV)
    df["jugador"] = df["jugador"].str.strip().str.title()
    return df

# ── Helpers ───────────────────────────────────────────────────────────────────
def mins_reales_partido(ep: pd.DataFrame) -> pd.DataFrame:
    m1 = ep[ep["mitad"] == 1]
    m2 = ep[ep["mitad"] == 2]
    if m1.empty or m2.empty:
        ep = ep.copy(); ep["Mins_real"] = ep["Mins"]; return ep
    m1_max = m1["Mins"].max(); m2_min = m2["Mins"].min()
    resetea = m2_min < 10
    ep = ep.copy()
    if resetea:
        offset = m1_max if not pd.isna(m1_max) else 45
        ep["Mins_real"] = ep.apply(
            lambda r: r["Mins"] + offset if r["mitad"] == 2 else r["Mins"], axis=1)
    else:
        ep["Mins_real"] = ep["Mins"]
    return ep

def calcular_minutos(nombre: str, eventos: pd.DataFrame) -> int:
    if eventos.empty: return 0
    j = eventos[eventos["Player"].str.lower() == nombre.lower()]
    if j.empty: return 0
    total = 0
    for f in j["fecha"].unique():
        ep_fixed = mins_reales_partido(eventos[eventos["fecha"] == f])
        jp = ep_fixed[ep_fixed["Player"].str.lower() == nombre.lower()]
        primero = jp["Mins_real"].min(); ultimo = jp["Mins_real"].max()
        total += int(ultimo if primero <= 15 else max(1, ultimo - primero + 1))
    return total

def stats_jugador(nombre: str, eventos: pd.DataFrame) -> dict:
    base = {"partidos": 0, "minutos": 0, "pase": 0, "recuperacion": 0,
            "conduccion": 0, "despeje": 0, "falta cometida": 0,
            "remate": 0, "gol": 0, "centro": 0}
    if eventos.empty: return base
    j = eventos[eventos["Player"].str.lower() == nombre.lower()]
    if j.empty: return base
    base["partidos"] = int(j["fecha"].nunique())
    base["minutos"]  = calcular_minutos(nombre, eventos)
    for ev in base:
        if ev not in ("partidos", "minutos"):
            base[ev] = int(len(j[j["Event"] == ev]))
    return base

def estado_jugador(nombre: str, alertas: pd.DataFrame) -> tuple:
    from datetime import date
    hoy = pd.Timestamp(date.today())
    if alertas.empty: return "✅", "Disponible", "badge-verde"
    fila = alertas[alertas["nombre"].str.lower() == nombre.lower()]
    if fila.empty: return "✅", "Disponible", "badge-verde"
    for _, row in fila.iterrows():
        tipo    = str(row.get("tipo", "")).lower()
        regreso = row.get("fecha_regreso", None)
        activo  = pd.isna(regreso) or regreso >= hoy
        if not activo: continue
        if tipo in ["lesión", "lesion"]:   return "🤕", "Lesionado", "badge-rojo"
        if tipo in ["sanción", "sancion", "roja directa"]: return "🟥", "Sancionado", "badge-rojo"
    amarillas = fila[fila["tipo"].str.lower() == "amarilla"]
    if len(amarillas) >= 4: return "🟨", "En riesgo", "badge-amari"
    return "✅", "Disponible", "badge-verde"

@st.cache_data(show_spinner=False)
def foto_b64(foto_path: str) -> str:
    if os.path.exists(foto_path):
        mime, _ = mimetypes.guess_type(foto_path)
        mime = mime or "image/jpeg"
        with open(foto_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"data:{mime};base64,{b64}"
    return None

def radar_jugador(nombre, posicion, eventos, color) -> go.Figure:
    metricas  = METRICAS_POS.get(posicion, ["pase", "recuperacion", "remate"])
    s         = stats_jugador(nombre, eventos)
    cats      = [LABEL_METRICAS.get(m, m) for m in metricas]
    vals_real = [s.get(m, 0) for m in metricas]
    vals_norm = [
        min(round(vals_real[k] / ESCALA_RADAR.get(metricas[k], 1) * 100, 1), 100)
        for k in range(len(metricas))
    ]
    cats_c      = cats + [cats[0]]
    vals_norm_c = vals_norm + [vals_norm[0]]
    vals_real_c = vals_real + [vals_real[0]]
    r, g, b_   = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
    fig = go.Figure(go.Scatterpolar(
        r=vals_norm_c, theta=cats_c, fill="toself",
        fillcolor=f"rgba({r},{g},{b_},0.15)",
        line=dict(color=color, width=2.5),
        marker=dict(color=color, size=7),
        customdata=vals_real_c,
        hovertemplate="%{theta}: <b>%{customdata}</b><extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0,100], showticklabels=False,
                            gridcolor="#374151", color="#6B7280"),
            angularaxis=dict(gridcolor="#374151", color="#9CA3AF"),
            bgcolor="#111827",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF", size=11, family="Inter"),
        margin=dict(l=20, r=20, t=20, b=20),
        height=280,
        showlegend=False,
    )
    return fig

# ── Carga global ──────────────────────────────────────────────────────────────
jugadores    = cargar_jugadores()
eventos      = cargar_eventos()
alertas      = cargar_alertas()
videos_df    = cargar_videos_jugadores()

nombres_ordenados = sorted(jugadores["nombre"].tolist())

# ══════════════════════════════════════════════════════════════════════════════
# PANTALLA INICIAL: escudo centrado + selector
# ══════════════════════════════════════════════════════════════════════════════
_, col_logo, _ = st.columns([1, 1, 1])
with col_logo:
    if os.path.exists(ESCUDO):
        st.image(ESCUDO, width=120)
    st.markdown("""
    <div style='text-align:center;margin-top:8px;margin-bottom:24px'>
        <div style='font-size:.62em;color:#6B7280;text-transform:uppercase;letter-spacing:4px'>
            Cuerpo Técnico · Análisis
        </div>
        <div style='font-size:1.4em;font-weight:800;color:#F9FAFB;margin-top:2px'>
            Player Review
        </div>
    </div>
    """, unsafe_allow_html=True)

_, col_sel, _ = st.columns([1, 2, 1])
with col_sel:
    jugador_sel = st.selectbox(
        "Seleccioná un jugador",
        options=["— Elegí un jugador —"] + nombres_ordenados,
        label_visibility="collapsed",
    )

# Si no eligieron todavía, terminamos acá
if jugador_sel == "— Elegí un jugador —":
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# CONTENIDO DEL JUGADOR SELECCIONADO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.markdown("<div style='height:1px;background:#1F2937;margin-bottom:20px'></div>",
            unsafe_allow_html=True)

# Datos del jugador desde Jugadores.csv
row_jug = jugadores[jugadores["nombre"] == jugador_sel]
if row_jug.empty:
    st.error(f"No se encontró '{jugador_sel}' en el plantel.")
    st.stop()
row_jug = row_jug.iloc[0]

posicion  = str(row_jug.get("posicion", "—"))
camiseta  = row_jug.get("camiseta", "—")
edad      = row_jug.get("edad", "—")
color     = COLOR_POS.get(posicion, "#9CA3AF")

_stats                     = stats_jugador(jugador_sel, eventos)
icono, estado_txt, badge_c = estado_jugador(jugador_sel, alertas)
metricas_clave             = METRICAS_POS.get(posicion, ["pase", "recuperacion", "remate"])

# Videos del jugador
videos_jug = videos_df[videos_df["jugador"].str.lower() == jugador_sel.lower()]
if not videos_jug.empty:
    videos_jug = videos_jug.sort_values("fecha", ascending=False)

# ── Layout: 30% stats | 70% videos ──────────────────────────────────────────
col_stats, col_videos = st.columns([3, 7])

# ─────────────────────────────────────────────────────────────────────────────
# COLUMNA IZQUIERDA: Ficha del jugador
# ─────────────────────────────────────────────────────────────────────────────
with col_stats:

    # Foto
    foto_path = os.path.join(FOTOS_DIR, str(row_jug.get("fotos", "")))
    src = foto_b64(foto_path)
    if src:
        st.markdown(
            f"<img src='{src}' style='width:100%;border-radius:10px;"
            f"object-fit:cover;aspect-ratio:1/1;margin-bottom:12px'>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='width:100%;aspect-ratio:1/1;background:#1F2937;"
            "border-radius:10px;display:flex;align-items:center;"
            "justify-content:center;font-size:3rem;margin-bottom:12px'>👤</div>",
            unsafe_allow_html=True,
        )

    # Nombre + badge
    st.markdown(f"""
    <div style='border-left:4px solid {color};padding-left:10px;margin-bottom:14px'>
        <div style='font-size:1.25em;font-weight:800;color:#F9FAFB'>
            #{camiseta} {jugador_sel}
        </div>
        <div style='color:{color};font-size:.82em;font-weight:700;margin-top:2px'>
            {posicion}
        </div>
        <span class='badge {badge_c}' style='margin-top:6px;display:inline-block'>
            {icono} {estado_txt}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Info básica
    st.markdown("<div class='pr-section'>Ficha</div>", unsafe_allow_html=True)
    info_cols = st.columns(2)
    for col_i, (lbl, val) in zip(
        [info_cols[0], info_cols[1], info_cols[0], info_cols[1]],
        [("Edad", edad), ("Posición", posicion),
         ("Partidos", _stats["partidos"]), ("Minutos", f"{_stats['minutos']}'")]
    ):
        col_i.markdown(f"""
        <div class='pr-stat-card'>
            <div class='pr-stat-num'>{val}</div>
            <div class='pr-stat-label'>{lbl}</div>
        </div>
        """, unsafe_allow_html=True)

    # Métricas clave
    st.markdown("<div class='pr-section'>Métricas clave</div>", unsafe_allow_html=True)
    for m in metricas_clave:
        val_m = _stats.get(m, 0)
        max_m = ESCALA_RADAR.get(m, 1)
        pct   = min(int(val_m / max_m * 100), 100)
        fill  = "#8A2525" if m in ("falta cometida",) else color
        st.markdown(f"""
        <div style='margin-bottom:10px'>
            <div style='display:flex;justify-content:space-between;
                        font-size:.75em;color:#9CA3AF;margin-bottom:3px'>
                <span>{LABEL_METRICAS.get(m, m)}</span>
                <span style='color:#F9FAFB;font-weight:700'>{val_m}</span>
            </div>
            <div style='background:#1F2937;border-radius:99px;height:5px'>
                <div style='width:{pct}%;background:{fill};
                            height:100%;border-radius:99px'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Radar
    if not eventos.empty:
        st.markdown("<div class='pr-section'>Perfil de rendimiento</div>",
                    unsafe_allow_html=True)
        fig_r = radar_jugador(jugador_sel, posicion, eventos, color)
        st.plotly_chart(fig_r, use_container_width=True, key=f"radar_{jugador_sel}")

    # Detalle por partido
    if not eventos.empty:
        j_ev = eventos[eventos["Player"].str.lower() == jugador_sel.lower()]
        if not j_ev.empty:
            st.markdown("<div class='pr-section'>Por partido</div>",
                        unsafe_allow_html=True)
            rows_t = []
            for fecha in sorted(j_ev["fecha"].unique()):
                jf = j_ev[j_ev["fecha"] == fecha]
                fila = {"F": int(fecha)}
                for m in metricas_clave:
                    fila[LABEL_METRICAS.get(m, m)] = int(len(jf[jf["Event"] == m]))
                rows_t.append(fila)
            st.dataframe(pd.DataFrame(rows_t), hide_index=True, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# COLUMNA DERECHA: Videos
# ─────────────────────────────────────────────────────────────────────────────
with col_videos:

    st.markdown(f"""
    <div style='margin-bottom:18px'>
        <div style='font-size:.62em;color:#6B7280;text-transform:uppercase;
                    letter-spacing:4px;margin-bottom:4px'>Biblioteca de clips</div>
        <div style='font-size:1.3em;font-weight:800;color:#F9FAFB'>
            {jugador_sel}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if videos_jug.empty:
        st.markdown(f"""
        <div style='background:#111827;border:1px dashed #374151;border-radius:12px;
                    padding:48px 32px;text-align:center;margin-top:20px'>
            <div style='font-size:2.5rem;margin-bottom:12px'>🎬</div>
            <div style='color:#F9FAFB;font-size:1em;font-weight:700;margin-bottom:6px'>
                Sin videos cargados aún
            </div>
            <div style='color:#6B7280;font-size:.82em;max-width:320px;margin:0 auto'>
                Agregá clips de <b style='color:{color}'>{jugador_sel}</b> en
                <code>data/videos_jugadores.csv</code> con las columnas:<br>
                <span style='color:#9CA3AF'>jugador · titulo · youtube_id · fecha · descripcion</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Filtro rápido por fecha si hay más de 1 fecha disponible
        fechas_disp = sorted(videos_jug["fecha"].unique().tolist(), reverse=True)
        if len(fechas_disp) > 1:
            fecha_fil = st.selectbox(
                "Filtrar por fecha",
                options=["Todas"] + [str(int(f)) for f in fechas_disp],
                key="filtro_fecha_video",
            )
            if fecha_fil != "Todas":
                videos_jug = videos_jug[videos_jug["fecha"] == int(fecha_fil)]

        for _, vrow in videos_jug.iterrows():
            with st.container(border=True):
                st.markdown(f"""
                <div style='margin-bottom:6px'>
                    <div class='pr-video-title'>
                        📹 {vrow['titulo']}
                        <span style='color:#6B7280;font-size:.8em;
                                     font-weight:400;margin-left:8px'>
                            · Fecha {int(vrow['fecha'])}
                        </span>
                    </div>
                    <div class='pr-video-desc'>{vrow['descripcion']}</div>
                </div>
                """, unsafe_allow_html=True)
                st.components.v1.iframe(
                    f"https://www.youtube.com/embed/{vrow['youtube_id']}",
                    height=420,
                )
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
