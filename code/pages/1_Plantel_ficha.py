"""
plantel_ficha.py  —  Estrella FC · Ficha Dinámica por Jugador
=============================================================
CAMBIOS MOBILE v2:
  • Grilla adaptativa: 2 cols en mobile, 4 en desktop (CSS media query)
  • Ficha usa st.expander → abre inline, sin rerun ni scroll perdido
  • Radar desactivado en mobile → reemplazado por métricas simples (mucho más rápido)
  • Imágenes: tamaño fijo pequeño, sin use_container_width en grilla
  • render_mobile_nav() agregado para consistencia con resto de la app

CAMBIOS RADAR v3:
  • Escala fija por métrica (ESCALA_RADAR) → todos los radares son comparables
  • range=[0, 100] fijo en eje radial → nunca se auto-ajusta
  • Tooltip muestra valor real, no el normalizado
"""

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Plantel · Estrella FC",
    page_icon="👥",
    layout="wide",
)

from components.layout import inject_css, render_sidebar, render_mobile_nav
inject_css()
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
render_sidebar(BASE)
render_mobile_nav()

# ── Rutas base ────────────────────────────────────────────────────────────────
FOTOS_DIR = os.path.join(BASE, "static", "fotos")
DATA_PATH = os.path.join(BASE, "data", "events_clean.csv")
FIXT_PATH = os.path.join(BASE, "data", "fixture.csv")
JUG_PATH  = os.path.join(BASE, "data", "Jugadores.csv")
SANC_PATH = os.path.join(BASE, "data", "sanciones_lesiones.csv")
ESCUDO    = os.path.join(BASE, "static", "escudo.png")

# ══════════════════════════════════════════════════════════════════════════════
# CSS — mobile first
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Grilla responsive ──
   En desktop mostramos 4-5 columnas normalmente via st.columns.
   En mobile Streamlit apila todo en 1 col, así que usamos nuestra propia grilla CSS */
.plantel-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 20px;
}
@media (min-width: 640px)  { .plantel-grid { grid-template-columns: repeat(3, 1fr); } }
@media (min-width: 900px)  { .plantel-grid { grid-template-columns: repeat(4, 1fr); } }
@media (min-width: 1200px) { .plantel-grid { grid-template-columns: repeat(5, 1fr); } }

/* ── Cromo ── */
.cromo {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 10px;
    padding: 10px 8px 12px 8px;
    text-align: center;
    cursor: pointer;
    transition: border-color .15s;
}
.cromo img {
    width: 100%;
    aspect-ratio: 1/1;
    object-fit: cover;
    border-radius: 6px;
    margin-bottom: 8px;
}
.cromo-placeholder {
    width: 100%;
    aspect-ratio: 1/1;
    background: #1F2937;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    margin-bottom: 8px;
}
.cromo-numero { font-size: .65em; color: #6B7280; font-weight: 700; letter-spacing: 2px; }
.cromo-nombre { font-size: .82em; font-weight: 800; color: #F9FAFB; line-height: 1.2; margin: 2px 0; }
.cromo-pos    { font-size: .68em; font-weight: 600; margin-bottom: 4px; }

/* ── Badges ── */
.badge {
    display: inline-block; border-radius: 4px;
    padding: 2px 7px; font-size: .68em; font-weight: 700;
}
.badge-verde  { background: #064e3b; color: #34D399; }
.badge-rojo   { background: #450a0a; color: #F87171; }
.badge-amari  { background: #451a03; color: #FBBF24; }

/* ── Ficha expandida ── */
.ficha-header {
    background: #0F172A;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 16px;
    border-left: 4px solid var(--accent, #E23E3E);
}
.ficha-label { font-size: .58em; color: #6B7280; text-transform: uppercase; letter-spacing: 3px; }
.ficha-valor { font-size: 1em; font-weight: 800; color: #F9FAFB; }

/* ── Sección titulo ── */
.seccion-titulo {
    font-size: .62em; font-weight: 700; color: #4B5563;
    text-transform: uppercase; letter-spacing: 3px;
    border-bottom: 1px solid #1F2937;
    padding-bottom: 6px; margin-bottom: 12px;
}

/* ── Stats macro ── */
.macro-card {
    background: #111827; border: 1px solid #1F2937;
    border-radius: 8px; padding: 14px 16px; text-align: center;
}
.macro-num   { font-size: 1.8em; font-weight: 800; color: #F9FAFB; }
.macro-label { font-size: .60em; color: #6B7280; text-transform: uppercase; letter-spacing: 2px; }

/* ── Ocultar radar en mobile ── */
.radar-desktop { display: block; }
@media (max-width: 768px) {
    .radar-desktop { display: none; }
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Configuración de posiciones
# ══════════════════════════════════════════════════════════════════════════════
COLOR_POS = {
    "Arquero":       "#60A5FA",
    "Defensor":      "#34D399",
    "Mediocampista": "#FBBF24",
    "Delantero":     "#F87171",
}

METRICAS_POS = {
    "Arquero":        ["despeje", "recuperacion", "pase"],
    "Defensor":       ["recuperacion", "despeje", "falta cometida"],
    "Mediocampista":  ["pase", "recuperacion", "conduccion"],
    "Delantero":      ["remate", "gol", "centro", "conduccion"],
}

LABEL_METRICAS = {
    "pase": "Pases", "recuperacion": "Recuperac.", "despeje": "Despejes",
    "falta cometida": "Faltas", "conduccion": "Cond.", "remate": "Remates",
    "gol": "Goles", "centro": "Centros",
}

# ── Escala fija por métrica (valor = 100% del radar) ─────────────────────────
# Ajustá estos valores según la realidad de tu plantel.
# Si un jugador supera el máximo, topa en el borde (100%) sin romper el gráfico.
ESCALA_RADAR = {
    "pase":            136,   # max real del plantel = 113  (Romo)
    "recuperacion":     63,   # max real = 52  (Romo)
    "conduccion":       22,   # max real = 18  (Villoldo)
    "despeje":          65,   # max real = 54  (Sanjiau)
    "falta cometida":    8,   # max real = 6   (Dedomingo)
    "remate":            8,   # max real = 6   (Retamozo)
    "gol":               2,   # max real = 1   (Marinucci)
    "centro":           21,   # max real = 17  (Barneix)
}


# ══════════════════════════════════════════════════════════════════════════════
# Carga de datos — todo con ttl=0 para evitar datos obsoletos
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=0)
def cargar_jugadores() -> pd.DataFrame:
    df = pd.read_csv(JUG_PATH)
    df["nombre"]   = df["nombre"].str.strip().str.title()
    df["posicion"] = df["posicion"].str.strip().str.title()
    if "edad" not in df.columns:
        df["edad"] = "—"
    return df


@st.cache_data(ttl=0)
def cargar_alertas() -> pd.DataFrame:
    if not os.path.exists(SANC_PATH):
        return pd.DataFrame()
    df = pd.read_csv(SANC_PATH)
    if not df.empty and "fecha_regreso" in df.columns:
        df["fecha_regreso"] = pd.to_datetime(
            df["fecha_regreso"], dayfirst=True, errors="coerce"
        )
    return df


@st.cache_data(ttl=0)
def cargar_eventos() -> pd.DataFrame:
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame()
    df = pd.read_csv(DATA_PATH)
    df["Mins"] = pd.to_numeric(df["Mins"], errors="coerce")
    df["Secs"] = pd.to_numeric(df["Secs"], errors="coerce")
    return df


@st.cache_data(ttl=0)
def cargar_fixture() -> pd.DataFrame:
    if not os.path.exists(FIXT_PATH):
        return pd.DataFrame()
    return pd.read_csv(FIXT_PATH)


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════
def estado_jugador(nombre: str, alertas: pd.DataFrame) -> tuple:
    hoy = pd.Timestamp(date.today())
    if alertas.empty:
        return "✅", "Disponible", "badge-verde"
    fila = alertas[alertas["nombre"].str.lower() == nombre.lower()]
    if fila.empty:
        return "✅", "Disponible", "badge-verde"
    for _, row in fila.iterrows():
        tipo   = str(row.get("tipo", "")).lower()
        regreso = row.get("fecha_regreso", None)
        activo  = pd.isna(regreso) or regreso >= hoy
        if not activo:
            continue
        if tipo in ["lesión", "lesion"]:
            return "🤕", "Lesionado", "badge-rojo"
        if tipo in ["sanción", "sancion", "roja directa"]:
            return "🟥", "Sancionado", "badge-rojo"
    amarillas = fila[fila["tipo"].str.lower() == "amarilla"]
    if len(amarillas) >= 4:
        return "🟨", "En riesgo", "badge-amari"
    return "✅", "Disponible", "badge-verde"


def calcular_minutos(nombre: str, eventos: pd.DataFrame) -> int:
    if eventos.empty:
        return 0
    j = eventos[eventos["Player"].str.lower() == nombre.lower()]
    if j.empty:
        return 0
    total = 0
    for f in j["fecha"].unique():
        ep = eventos[eventos["fecha"] == f]
        jp = j[j["fecha"] == f]
        final   = int(ep["Mins"].max())
        primero = int(jp["Mins"].min())
        mins = final if primero <= 15 else max(1, final - primero + 1)
        total += mins
    return total


def stats_jugador(nombre: str, eventos: pd.DataFrame) -> dict:
    base = {
        "partidos": 0, "minutos": 0,
        "pase": 0, "recuperacion": 0, "conduccion": 0,
        "despeje": 0, "falta cometida": 0, "remate": 0,
        "gol": 0, "centro": 0,
    }
    if eventos.empty:
        return base
    j = eventos[eventos["Player"].str.lower() == nombre.lower()]
    if j.empty:
        return base
    base["partidos"] = int(j["fecha"].nunique())
    base["minutos"]  = calcular_minutos(nombre, eventos)
    for ev in ["pase", "recuperacion", "conduccion", "despeje",
               "falta cometida", "remate", "gol", "centro"]:
        base[ev] = int(len(j[j["Event"] == ev]))
    return base


def radar_jugador(nombre: str, posicion: str, eventos: pd.DataFrame, color: str) -> go.Figure:
    metricas  = METRICAS_POS.get(posicion, ["pase", "recuperacion", "remate"])
    s         = stats_jugador(nombre, eventos)

    cats      = [LABEL_METRICAS.get(m, m) for m in metricas]
    vals_real = [s.get(m, 0) for m in metricas]

    # Normalizar contra escala fija → 0 a 100
    # Si el jugador supera el techo definido, topa en 100 sin romper el gráfico
    vals_norm = [
        min(round(vals_real[k] / ESCALA_RADAR.get(metricas[k], 1) * 100, 1), 100)
        for k in range(len(metricas))
    ]

    # Cerrar el polígono repitiendo el primer punto
    cats_c      = cats + [cats[0]]
    vals_norm_c = vals_norm + [vals_norm[0]]
    vals_real_c = vals_real + [vals_real[0]]

    fig = go.Figure(go.Scatterpolar(
        r=vals_norm_c,
        theta=cats_c,
        fill="toself",
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.15)",
        line=dict(color=color, width=2.5),
        marker=dict(color=color, size=7),
        # El tooltip muestra el valor real, no el normalizado
        customdata=vals_real_c,
        hovertemplate="%{theta}: <b>%{customdata}</b><extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],         # ← escala fija, nunca se auto-ajusta
                showticklabels=False,   # los números internos son % relativos, mejor ocultarlos
                gridcolor="#374151",
                color="#6B7280",
            ),
            angularaxis=dict(gridcolor="#374151", color="#9CA3AF"),
            bgcolor="#111827",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF", size=12, family="Inter"),
        margin=dict(l=30, r=30, t=30, b=30),
        height=300,
        showlegend=False,
    )
    return fig


@st.cache_data(show_spinner=False)
def foto_html(foto_path: str) -> str:
    """Devuelve HTML de imagen en base64 o placeholder. Base64 funciona en cualquier entorno."""
    import base64, mimetypes
    if os.path.exists(foto_path):
        mime, _ = mimetypes.guess_type(foto_path)
        mime = mime or "image/jpeg"
        with open(foto_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return (f"<img src='data:{mime};base64,{b64}' "
                f"style='width:100%;aspect-ratio:1/1;object-fit:cover;"
                f"border-radius:6px;margin-bottom:8px'>")
    return "<div class='cromo-placeholder'>👤</div>"


# ══════════════════════════════════════════════════════════════════════════════
# Carga global
# ══════════════════════════════════════════════════════════════════════════════
jugadores = cargar_jugadores()
alertas   = cargar_alertas()
eventos   = cargar_eventos()
fixture   = cargar_fixture()

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
h1, h2, h3 = st.columns([0.08, 0.80, 0.12])
with h1:
    if os.path.exists(ESCUDO):
        st.image(ESCUDO, width=56)
with h2:
    st.markdown("""
    <div style='padding:6px 0'>
        <div style='font-size:.62em;color:#6B7280;text-transform:uppercase;letter-spacing:4px'>
            Cuerpo Técnico · Análisis
        </div>
        <div style='font-size:1.5em;font-weight:800;color:#F9FAFB;margin-top:2px'>
            Plantel — Estrella FC
        </div>
    </div>
    """, unsafe_allow_html=True)
with h3:
    st.markdown("<div style='padding-top:10px'>", unsafe_allow_html=True)
    ver_col = st.button("📊 Stats", key="btn_col", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:1px;background:#1F2937;margin:4px 0 16px 0'></div>",
            unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FILTRO
# ══════════════════════════════════════════════════════════════════════════════
posiciones   = ["Todas"] + sorted(jugadores["posicion"].dropna().unique().tolist())
f1, _, f3    = st.columns([2, 5, 3])
with f1:
    pos_sel = st.selectbox("Posición", posiciones, label_visibility="collapsed")

df_filtrado = (jugadores if pos_sel == "Todas"
               else jugadores[jugadores["posicion"] == pos_sel]).reset_index(drop=True)

# ══════════════════════════════════════════════════════════════════════════════
# KPIs rápidos
# ══════════════════════════════════════════════════════════════════════════════
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total", len(jugadores))
m2.metric("Arqueros",    len(jugadores[jugadores["posicion"].str.lower() == "arquero"]))
m3.metric("Defensores",  len(jugadores[jugadores["posicion"].str.lower() == "defensor"]))
m4.metric("Med. + Del.", len(jugadores[jugadores["posicion"].str.lower().isin(
    ["mediocampista", "delantero"])]))

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# GRILLA DE CROMOS — renderizada en HTML puro para evitar rerun por imagen
# La interacción (abrir ficha) se maneja con st.expander debajo de cada cromo
# ══════════════════════════════════════════════════════════════════════════════
COLS_DESKTOP = 4   # cuántas columnas usa st.columns en desktop

ORDEN_POSICIONES = ["Arquero", "Defensor", "Mediocampista", "Delantero"]

# Agrupar jugadores filtrados por posición, respetando el orden táctico.
# Las posiciones que no estén en ORDEN_POSICIONES (por si hay un valor raro
# en el CSV) se agregan al final, en orden alfabético, para no perder jugadores.
posiciones_presentes = df_filtrado["posicion"].dropna().unique().tolist()
posiciones_extra = sorted(p for p in posiciones_presentes if p not in ORDEN_POSICIONES)
orden_final = [p for p in ORDEN_POSICIONES if p in posiciones_presentes] + posiciones_extra

for pos_grupo in orden_final:
    grupo_df = df_filtrado[df_filtrado["posicion"] == pos_grupo].reset_index(drop=True)
    if grupo_df.empty:
        continue

    color_grupo = COLOR_POS.get(pos_grupo, "#9CA3AF")
    st.markdown(f"""
    <div class='seccion-titulo' style='margin-top:18px;color:{color_grupo}'>
        {pos_grupo} <span style='color:#4B5563'>({len(grupo_df)})</span>
    </div>
    """, unsafe_allow_html=True)

    for i in range(0, len(grupo_df), COLS_DESKTOP):
        bloque = grupo_df.iloc[i : i + COLS_DESKTOP]
        cols   = st.columns(COLS_DESKTOP)

        for j, (_, row) in enumerate(bloque.iterrows()):
            nombre   = row["nombre"]
            posicion = row["posicion"]
            color    = COLOR_POS.get(posicion, "#9CA3AF")
            icono, estado_txt, badge_cls = estado_jugador(nombre, alertas)
            foto_path = os.path.join(FOTOS_DIR, str(row.get("fotos", "")))

            with cols[j]:
                # ── Cromo en HTML (sin st.image para no relentizar) ──
                img_html = foto_html(foto_path)
                st.markdown(f"""
                <div class='cromo'>
                    {img_html}
                    <div class='cromo-numero'>#{int(row['camiseta'])}</div>
                    <div class='cromo-nombre'>{nombre}</div>
                    <div class='cromo-pos' style='color:{color}'>{posicion}</div>
                    <span class='badge {badge_cls}'>{icono} {estado_txt}</span>
                </div>
                """, unsafe_allow_html=True)

                # ── Ficha expandible inline (no hace rerun de toda la página) ──
                with st.expander("Ver ficha", expanded=False):
                    _stats  = stats_jugador(nombre, eventos)
                    _metr   = METRICAS_POS.get(posicion, ["pase", "recuperacion", "remate"])

                    # Cabecera de ficha
                    st.markdown(f"""
                    <div style='--accent:{color}' class='ficha-header'>
                        <div style='font-size:1.1em;font-weight:800;color:#F9FAFB;margin-bottom:10px'>
                            #{int(row['camiseta'])} {nombre}
                        </div>
                        <div style='display:flex;gap:20px;flex-wrap:wrap'>
                            <div><div class='ficha-label'>Posición</div>
                                 <div class='ficha-valor' style='color:{color}'>{posicion}</div></div>
                            <div><div class='ficha-label'>Edad</div>
                                 <div class='ficha-valor'>{row.get("edad","—")}</div></div>
                            <div><div class='ficha-label'>Partidos</div>
                                 <div class='ficha-valor'>{_stats["partidos"]}</div></div>
                            <div><div class='ficha-label'>Minutos</div>
                                 <div class='ficha-valor'>{_stats["minutos"]}'</div></div>
                            <div><div class='ficha-label'>Estado</div>
                                 <span class='badge {badge_cls}'>{icono} {estado_txt}</span></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Métricas clave (siempre visibles, incluso en mobile)
                    st.markdown("<div class='seccion-titulo'>Métricas clave</div>",
                                unsafe_allow_html=True)
                    mc = st.columns(len(_metr))
                    for k, m in enumerate(_metr):
                        mc[k].metric(LABEL_METRICAS.get(m, m), _stats.get(m, 0))

                    # Radar solo en desktop (oculto via CSS en mobile)
                    if not eventos.empty:
                        st.markdown("<div class='radar-desktop'>", unsafe_allow_html=True)
                        st.markdown("<div class='seccion-titulo'>Perfil de rendimiento</div>",
                                    unsafe_allow_html=True)
                        fig_r = radar_jugador(nombre, posicion, eventos, color)
                        st.plotly_chart(fig_r, use_container_width=True,
                                        key=f"radar_{nombre}_{pos_grupo}_{i}_{j}")
                        st.markdown("</div>", unsafe_allow_html=True)

                    # Observaciones
                    st.markdown("<div class='seccion-titulo' style='margin-top:14px'>Observaciones</div>",
                                unsafe_allow_html=True)
                    if "obs_cache" not in st.session_state:
                        st.session_state.obs_cache = {}
                    obs_val = st.session_state.obs_cache.get(nombre, "")
                    nueva   = st.text_area(
                        "Notas",
                        value=obs_val,
                        height=110,
                        placeholder="Notas tácticas, comportamientos...",
                        key=f"obs_{nombre}_{pos_grupo}_{i}_{j}",
                        label_visibility="collapsed",
                    )
                    if st.button("💾 Guardar", key=f"save_{nombre}_{pos_grupo}_{i}_{j}"):
                        st.session_state.obs_cache[nombre] = nueva
                        st.success("Guardado.")

                    # Detalle por partido
                    if not eventos.empty:
                        j_ev = eventos[eventos["Player"].str.lower() == nombre.lower()]
                        if not j_ev.empty:
                            st.markdown(
                                "<div class='seccion-titulo' style='margin-top:14px'>Detalle por partido</div>",
                                unsafe_allow_html=True)
                            rows_t = []
                            for fecha in sorted(j_ev["fecha"].unique()):
                                jf   = j_ev[j_ev["fecha"] == fecha]
                                fila = {"Fecha": int(fecha)}
                                for m in _metr:
                                    fila[LABEL_METRICAS.get(m, m)] = int(len(jf[jf["Event"] == m]))
                                rows_t.append(fila)
                            st.dataframe(pd.DataFrame(rows_t),
                                         hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# VISTA COLECTIVA
# ══════════════════════════════════════════════════════════════════════════════
if ver_col:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='seccion-titulo' style='font-size:.75em;margin-bottom:16px'>
        📊 Estadísticas Colectivas — Temporada
    </div>
    """, unsafe_allow_html=True)

    if fixture.empty or eventos.empty:
        st.info("Datos de fixture o eventos aún no disponibles.")
    else:
        gf = fixture["goles_favor"].sum()  if "goles_favor"  in fixture.columns else "—"
        gc = fixture["goles_contra"].sum() if "goles_contra" in fixture.columns else "—"
        pj = len(fixture)
        wins  = len(fixture[fixture["goles_favor"] > fixture["goles_contra"]]) \
                if "goles_favor" in fixture.columns else 0
        draws = len(fixture[fixture["goles_favor"] == fixture["goles_contra"]]) \
                if "goles_favor" in fixture.columns else 0
        loses = pj - wins - draws

        k1, k2, k3, k4, k5, k6 = st.columns(6)
        for col_m, lbl, val in zip(
            [k1, k2, k3, k4, k5, k6],
            ["PJ", "Victorias", "Empates", "Derrotas", "Goles F.", "Goles C."],
            [pj,  wins, draws, loses, gf, gc],
        ):
            col_m.markdown(f"""
            <div class='macro-card'>
                <div class='macro-num'>{val}</div>
                <div class='macro-label'>{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        if "Event" in eventos.columns:
            goles_ev = eventos[eventos["Event"].isin(["gol", "gol_contra"])]
            tramos   = [0, 15, 30, 45, 60, 75, 90, 120]
            labels_t = ["1-15", "16-30", "31-45", "46-60", "61-75", "76-90", "90+"]

            def goles_tramos(df_g, ev):
                return [len(df_g[(df_g["Event"] == ev) &
                                 (df_g["Mins"] > tramos[i]) &
                                 (df_g["Mins"] <= tramos[i+1])])
                        for i in range(len(tramos) - 1)]

            g1, g2 = st.columns(2)
            for col_g, ev_name, color_b, titulo in [
                (g1, "gol",        "#34D399", "Goles a favor por tramo (15')"),
                (g2, "gol_contra", "#F87171", "Goles en contra por tramo (15')"),
            ]:
                with col_g:
                    st.markdown(f"<div class='seccion-titulo'>{titulo}</div>",
                                unsafe_allow_html=True)
                    vals_g = goles_tramos(goles_ev, ev_name)
                    fig_g  = go.Figure(go.Bar(
                        x=labels_t, y=vals_g,
                        marker_color=color_b, opacity=0.85,
                        text=vals_g, textposition="outside",
                    ))
                    fig_g.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#9CA3AF", size=11, family="Inter"),
                        margin=dict(l=0, r=0, t=10, b=0), height=200,
                        xaxis=dict(gridcolor="#1F2937"),
                        yaxis=dict(gridcolor="#1F2937"),
                    )
                    st.plotly_chart(fig_g, use_container_width=True, key=f"bar_{ev_name}")

        if "condicion" in fixture.columns and "goles_favor" in fixture.columns:
            st.markdown("<div class='seccion-titulo' style='margin-top:8px'>Efectividad Local vs Visitante</div>",
                        unsafe_allow_html=True)
            ev_col_cols = st.columns(2)
            for col_ef, cond in zip(ev_col_cols, ["Local", "Visitante"]):
                sub = fixture[fixture["condicion"] == cond]
                if sub.empty:
                    col_ef.caption(f"Sin partidos de {cond}.")
                    continue
                pj_c = len(sub)
                w_c  = len(sub[sub["goles_favor"] > sub["goles_contra"]])
                d_c  = len(sub[sub["goles_favor"] == sub["goles_contra"]])
                l_c  = pj_c - w_c - d_c
                efec = round(w_c / pj_c * 100) if pj_c > 0 else 0
                fig_pie = go.Figure(go.Pie(
                    labels=["Victorias", "Empates", "Derrotas"],
                    values=[w_c, d_c, l_c],
                    marker_colors=["#34D399", "#FBBF24", "#F87171"],
                    hole=0.55,
                    textinfo="label+percent",
                    textfont=dict(size=11, family="Inter"),
                ))
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#9CA3AF", family="Inter"),
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=200, showlegend=False,
                    annotations=[dict(text=f"<b>{efec}%</b>",
                                      x=0.5, y=0.5, font_size=16,
                                      showarrow=False, font_color="#F9FAFB")],
                )
                with col_ef:
                    st.markdown(f"<div style='text-align:center;font-size:.72em;"
                                f"color:#9CA3AF;margin-bottom:4px'>{cond} · {pj_c} PJ</div>",
                                unsafe_allow_html=True)
                    st.plotly_chart(fig_pie, use_container_width=True, key=f"pie_{cond}")
