"""
plantel_ficha.py  —  Estrella FC · Ficha Dinámica por Jugador
=============================================================
Página unificada que combina:
  • Vista de Plantel  → grilla de cromos
  • Ficha Individual  → se despliega debajo al cliquear un jugador
  • Vista Colectiva   → estadísticas macro del equipo (via escudo)

Requisitos de archivos:
  data/Jugadores.csv          → nombre, posicion, camiseta, fotos, edad (opcional)
  data/events_clean.csv       → Player, Event, Mins, Secs, fecha
  data/fixture.csv            → fecha, condicion (Local/Visitante), goles_favor, goles_contra
  data/sanciones_lesiones.csv → nombre, tipo, fecha_regreso
  static/fotos/<archivo>      → imágenes de jugadores
  static/escudo.png           → escudo del club
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

from components.layout import inject_css, render_sidebar
inject_css()
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
render_sidebar(BASE)

# ── Rutas base ────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOTOS_DIR  = os.path.join(BASE, "static", "fotos")
DATA_PATH  = os.path.join(BASE, "data", "events_clean.csv")
FIXT_PATH  = os.path.join(BASE, "data", "fixture.csv")
JUG_PATH   = os.path.join(BASE, "data", "Jugadores.csv")
SANC_PATH  = os.path.join(BASE, "data", "sanciones_lesiones.csv")
ESCUDO     = os.path.join(BASE, "static", "escudo.png")

# ══════════════════════════════════════════════════════════════════════════════
# CSS — estilo oscuro con identidad de cancha
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Fuente ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Cromo de jugador ── */
.cromo {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 10px;
    padding: 10px 8px 14px 8px;
    text-align: center;
    cursor: pointer;
    transition: border-color .15s, transform .15s;
    min-height: 220px;
}
.cromo:hover { border-color: #3B82F6; transform: translateY(-2px); }
.cromo.selected { border-color: #E23E3E; border-width: 2px; }

.cromo-numero { font-size: .72em; color: #6B7280; font-weight: 700; letter-spacing: 2px; }
.cromo-nombre { font-size: .88em; font-weight: 800; color: #F9FAFB; margin: 4px 0 2px 0; line-height: 1.2; }
.cromo-pos    { font-size: .7em; color: #9CA3AF; margin-bottom: 4px; }
.cromo-estado { font-size: .75em; }

/* ── Ficha individual ── */
.ficha-header {
    background: linear-gradient(135deg, #0F172A 60%, #1E293B 100%);
    border: 1px solid #1F2937;
    border-left: 4px solid var(--accent);
    border-radius: 8px;
    padding: 20px 28px;
    margin-bottom: 20px;
}
.ficha-label  { font-size: .58em; color: #6B7280; text-transform: uppercase; letter-spacing: 3px; }
.ficha-valor  { font-size: 1.05em; font-weight: 800; color: #F9FAFB; }
.ficha-pos    { font-size: .9em; font-weight: 700; }

/* ── Badges ── */
.badge {
    display: inline-block; border-radius: 4px;
    padding: 2px 8px; font-size: .7em; font-weight: 700;
}
.badge-verde  { background: #064e3b; color: #34D399; }
.badge-rojo   { background: #450a0a; color: #F87171; }
.badge-amari  { background: #451a03; color: #FBBF24; }
.badge-azul   { background: #0c2461; color: #60A5FA; }

/* ── Sección titulo ── */
.seccion-titulo {
    font-size: .62em; font-weight: 700; color: #4B5563;
    text-transform: uppercase; letter-spacing: 3px;
    border-bottom: 1px solid #1F2937; padding-bottom: 6px; margin-bottom: 12px;
}

/* ── Botón escudo ── */
.escudo-btn button {
    background: #0F172A !important;
    border: 2px solid #1F2937 !important;
    border-radius: 50% !important;
    padding: 6px !important;
    transition: border-color .2s !important;
}
.escudo-btn button:hover { border-color: #E23E3E !important; }

/* ── Stats macro ── */
.macro-card {
    background: #111827; border: 1px solid #1F2937;
    border-radius: 8px; padding: 16px 20px; text-align: center;
}
.macro-num  { font-size: 2em; font-weight: 800; color: #F9FAFB; }
.macro-label{ font-size: .62em; color: #6B7280; text-transform: uppercase; letter-spacing: 2px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Carga de datos
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
# Helpers de estado y métricas
# ══════════════════════════════════════════════════════════════════════════════

# Colores y métricas por posición
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


def estado_jugador(nombre: str, alertas: pd.DataFrame) -> tuple[str, str, str]:
    """Devuelve (icono, texto, clase_css)."""
    hoy = pd.Timestamp(date.today())
    if alertas.empty:
        return "✅", "Disponible", "badge-verde"
    fila = alertas[alertas["nombre"].str.lower() == nombre.lower()]
    if fila.empty:
        return "✅", "Disponible", "badge-verde"
    for _, row in fila.iterrows():
        tipo    = str(row.get("tipo", "")).lower()
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
    """Estima minutos jugados según primer/último evento por partido."""
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
    """Devuelve diccionario de métricas del jugador."""
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
    for ev in ["pase","recuperacion","conduccion","despeje","falta cometida","remate","gol","centro"]:
        base[ev] = int(len(j[j["Event"] == ev]))
    return base


def radar_jugador(nombre: str, posicion: str, eventos: pd.DataFrame, color: str) -> go.Figure:
    """Genera figura Plotly del radar de rendimiento."""
    metricas = METRICAS_POS.get(posicion, ["pase", "recuperacion", "remate"])
    s        = stats_jugador(nombre, eventos)
    cats  = [LABEL_METRICAS.get(m, m) for m in metricas]
    vals  = [s.get(m, 0) for m in metricas]
    # Cerrar el polígono
    cats_c = cats + [cats[0]]
    vals_c = vals + [vals[0]]
    fig = go.Figure(go.Scatterpolar(
        r=vals_c, theta=cats_c,
        fill="toself",
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.15)",
        line=dict(color=color, width=2.5),
        marker=dict(color=color, size=7),
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, showticklabels=True,
                gridcolor="#374151", color="#6B7280", tickfont=dict(size=9),
            ),
            angularaxis=dict(gridcolor="#374151", color="#9CA3AF"),
            bgcolor="#111827",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF", size=12, family="Inter"),
        margin=dict(l=30, r=30, t=30, b=30),
        height=320,
        showlegend=False,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# Session State — jugador seleccionado y vista activa
# ══════════════════════════════════════════════════════════════════════════════
if "jugador_sel" not in st.session_state:
    st.session_state.jugador_sel = None   # None = nadie / "colectivo" = vista macro

if "obs_cache" not in st.session_state:
    st.session_state.obs_cache = {}       # {nombre: texto_observaciones}


def seleccionar(nombre: str):
    """Callback: alterna la selección del jugador."""
    if st.session_state.jugador_sel == nombre:
        st.session_state.jugador_sel = None
    else:
        st.session_state.jugador_sel = nombre


def ver_colectivo():
    """Callback: cambia a vista de estadísticas macro."""
    st.session_state.jugador_sel = "colectivo"


# ══════════════════════════════════════════════════════════════════════════════
# Carga
# ══════════════════════════════════════════════════════════════════════════════
jugadores = cargar_jugadores()
alertas   = cargar_alertas()
eventos   = cargar_eventos()
fixture   = cargar_fixture()


# ══════════════════════════════════════════════════════════════════════════════
# HEADER — Escudo + Título + Botón colectivo
# ══════════════════════════════════════════════════════════════════════════════
h_col1, h_col2, h_col3 = st.columns([0.08, 0.80, 0.12])

with h_col1:
    if os.path.exists(ESCUDO):
        st.image(ESCUDO, width=64)

with h_col2:
    st.markdown("""
    <div style='padding: 8px 0'>
        <div style='font-size:.62em;color:#6B7280;text-transform:uppercase;letter-spacing:4px'>
            Cuerpo Técnico · Análisis
        </div>
        <div style='font-size:1.6em;font-weight:800;color:#F9FAFB;margin-top:2px'>
            Plantel — Estrella FC
        </div>
    </div>
    """, unsafe_allow_html=True)

with h_col3:
    st.markdown("<div style='padding-top:12px'>", unsafe_allow_html=True)
    if st.button("📊 Stats Colectivas", key="btn_colectivo", use_container_width=True):
        ver_colectivo()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:1px;background:#1F2937;margin:4px 0 20px 0'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILTRO POR POSICIÓN
# ══════════════════════════════════════════════════════════════════════════════
posiciones = ["Todas"] + sorted(jugadores["posicion"].dropna().unique().tolist())
f_col1, f_col2, f_col3 = st.columns([2, 6, 2])
with f_col1:
    pos_sel = st.selectbox("Filtrar posición", posiciones, label_visibility="collapsed")

df_filtrado = jugadores if pos_sel == "Todas" else jugadores[jugadores["posicion"] == pos_sel]
df_filtrado = df_filtrado.reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRILLA DE CROMOS
# ══════════════════════════════════════════════════════════════════════════════
COLS = 5
sel  = st.session_state.jugador_sel

# Métricas rápidas del header
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total", len(jugadores))
m2.metric("Arqueros",   len(jugadores[jugadores["posicion"].str.lower() == "arquero"]))
m3.metric("Defensores", len(jugadores[jugadores["posicion"].str.lower() == "defensor"]))
m4.metric("Med. + Del.",
    len(jugadores[jugadores["posicion"].str.lower().isin(["mediocampista","delantero"])]))

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

for i in range(0, len(df_filtrado), COLS):
    row_cols = st.columns(COLS)
    for j, col in enumerate(row_cols):
        idx = i + j
        if idx >= len(df_filtrado):
            break
        row      = df_filtrado.iloc[idx]
        nombre   = row["nombre"]
        posicion = row["posicion"]
        color    = COLOR_POS.get(posicion, "#9CA3AF")
        icono, estado_txt, badge_cls = estado_jugador(nombre, alertas)
        foto_path = os.path.join(FOTOS_DIR, str(row.get("fotos", "")))
        es_sel    = (sel == nombre)

        with col:
            # Imagen
            if os.path.exists(foto_path):
                st.image(foto_path, use_container_width=True)
            else:
                fallback = os.path.join(FOTOS_DIR, "sin_perfil.jpg")
                if os.path.exists(fallback):
                    st.image(fallback, use_container_width=True)
                else:
                    # Placeholder SVG si no hay imagen
                    st.markdown(f"""
                    <div style='background:#1F2937;border-radius:6px;height:110px;
                                display:flex;align-items:center;justify-content:center;
                                font-size:2.5em'>👤</div>
                    """, unsafe_allow_html=True)

            # Datos del cromo
            borde = f"border: 2px solid {color};" if es_sel else "border: 1px solid #1F2937;"
            st.markdown(f"""
            <div style='background:#111827;{borde}border-radius:0 0 8px 8px;
                        padding:8px 6px 10px 6px;text-align:center;margin-top:-4px'>
                <div style='font-size:.65em;color:#6B7280;font-weight:700;letter-spacing:2px'>
                    #{int(row["camiseta"])}
                </div>
                <div style='font-size:.82em;font-weight:800;color:#F9FAFB;
                            line-height:1.2;margin:2px 0'>
                    {nombre}
                </div>
                <div style='font-size:.68em;color:{color};font-weight:600;margin-bottom:4px'>
                    {posicion}
                </div>
                <span class='badge {badge_cls}'>{icono} {estado_txt}</span>
            </div>
            """, unsafe_allow_html=True)

            # Botón de selección
            label = "▼ Ver ficha" if not es_sel else "▲ Cerrar"
            if st.button(label, key=f"btn_{nombre}_{idx}", use_container_width=True):
                seleccionar(nombre)

        # Registrar posición de fila para saber dónde expandir la ficha
        # La ficha se despliega al terminar cada fila de COLS jugadores
    # ── Ficha desplegable al final de cada fila ────────────────────────────
    jugadores_en_fila = [df_filtrado.iloc[i + k]["nombre"]
                          for k in range(COLS) if (i + k) < len(df_filtrado)]
    if sel in jugadores_en_fila and sel not in (None, "colectivo"):
        _render_ficha = True
    else:
        _render_ficha = False

    if _render_ficha:
        _nombre   = sel
        _row      = jugadores[jugadores["nombre"] == _nombre].iloc[0]
        _posicion = _row["posicion"]
        _color    = COLOR_POS.get(_posicion, "#9CA3AF")
        _stats    = stats_jugador(_nombre, eventos)
        _icono, _estado_txt, _badge = estado_jugador(_nombre, alertas)

        with st.container():
            st.markdown(f"""
            <div style='--accent:{_color}' class='ficha-header'>
                <div style='display:flex;gap:32px;flex-wrap:wrap;align-items:center'>
                    <div>
                        <div class='ficha-label'>Jugador</div>
                        <div style='font-size:1.4em;font-weight:800;color:#F9FAFB'>
                            #{int(_row["camiseta"])} {_nombre}
                        </div>
                    </div>
                    <div>
                        <div class='ficha-label'>Posición</div>
                        <div class='ficha-pos' style='color:{_color}'>{_posicion}</div>
                    </div>
                    <div>
                        <div class='ficha-label'>Edad</div>
                        <div class='ficha-valor'>{_row.get("edad","—")}</div>
                    </div>
                    <div>
                        <div class='ficha-label'>Partidos</div>
                        <div class='ficha-valor'>{_stats["partidos"]}</div>
                    </div>
                    <div>
                        <div class='ficha-label'>Minutos</div>
                        <div class='ficha-valor'>{_stats["minutos"]}'</div>
                    </div>
                    <div>
                        <div class='ficha-label'>Estado</div>
                        <span class='badge {_badge}'>{_icono} {_estado_txt}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            fc1, fc2 = st.columns([1, 1])

            # ── Radar ────────────────────────────────────────────────────
            with fc1:
                st.markdown("<div class='seccion-titulo'>Perfil de rendimiento</div>",
                            unsafe_allow_html=True)
                if eventos.empty:
                    st.info("Sin datos de eventos aún.")
                else:
                    fig_radar = radar_jugador(_nombre, _posicion, eventos, _color)
                    st.plotly_chart(fig_radar, use_container_width=True, key=f"radar_{_nombre}")

                # Métricas numéricas rápidas debajo del radar
                _metricas = METRICAS_POS.get(_posicion, ["pase","recuperacion","remate"])
                mc = st.columns(len(_metricas))
                for k, m in enumerate(_metricas):
                    mc[k].metric(LABEL_METRICAS.get(m, m), _stats.get(m, 0))

            # ── Observaciones Cualitativas ────────────────────────────────
            with fc2:
                st.markdown("<div class='seccion-titulo'>Observaciones del analista</div>",
                            unsafe_allow_html=True)

                # Recuperar texto guardado en cache
                obs_actual = st.session_state.obs_cache.get(_nombre, "")
                nueva_obs  = st.text_area(
                    label="Notas tácticas / comportamientos",
                    value=obs_actual,
                    height=140,
                    placeholder=(
                        "Ej: Sufre a la espalda en transición.\n"
                        "Buen pie derecho, débil en duelos aéreos.\n"
                        "En ABP defiende zona 4."
                    ),
                    key=f"obs_{_nombre}",
                    label_visibility="collapsed",
                )

                if st.button("💾 Guardar observación", key=f"save_{_nombre}"):
                    st.session_state.obs_cache[_nombre] = nueva_obs
                    st.success("Observación guardada en sesión.")

                # Tabla de métricas por partido
                if not eventos.empty:
                    st.markdown("<div class='seccion-titulo' style='margin-top:18px'>Detalle por partido</div>",
                                unsafe_allow_html=True)
                    j_ev = eventos[eventos["Player"].str.lower() == _nombre.lower()]
                    if not j_ev.empty:
                        rows_tabla = []
                        for fecha in sorted(j_ev["fecha"].unique()):
                            jf = j_ev[j_ev["fecha"] == fecha]
                            fila = {"Fecha": int(fecha)}
                            for m in _metricas:
                                fila[LABEL_METRICAS.get(m, m)] = int(len(jf[jf["Event"] == m]))
                            rows_tabla.append(fila)
                        st.dataframe(pd.DataFrame(rows_tabla),
                                     hide_index=True, use_container_width=True)
                    else:
                        st.caption("Sin acciones registradas.")

            st.markdown("<div style='height:1px;background:#1F2937;margin:20px 0'></div>",
                        unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# VISTA COLECTIVA — Stats macro del equipo
# ══════════════════════════════════════════════════════════════════════════════
if sel == "colectivo":
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='seccion-titulo' style='font-size:.75em;margin-bottom:20px'>
        📊 Estadísticas Colectivas — Temporada
    </div>
    """, unsafe_allow_html=True)

    if fixture.empty or eventos.empty:
        st.info("Datos de fixture o eventos aún no disponibles.")
    else:
        # ── KPIs globales ──────────────────────────────────────────────────
        gf = fixture["goles_favor"].sum()   if "goles_favor"  in fixture.columns else "—"
        gc = fixture["goles_contra"].sum()  if "goles_contra" in fixture.columns else "—"
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
            [pj,  wins,        draws,      loses,      gf,         gc],
        ):
            col_m.markdown(f"""
            <div class='macro-card'>
                <div class='macro-num'>{val}</div>
                <div class='macro-label'>{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        # ── Goles por tramos de 15 min ─────────────────────────────────────
        if "Event" in eventos.columns:
            goles_ev = eventos[eventos["Event"].isin(["gol", "gol_contra"])]
            tramos   = [0, 15, 30, 45, 60, 75, 90, 120]
            labels_t = ["1-15", "16-30", "31-45", "46-60", "61-75", "76-90", "90+"]

            def goles_tramos(df_g, etiqueta_evento):
                conteo = []
                evs = df_g[df_g["Event"] == etiqueta_evento]
                for i in range(len(tramos) - 1):
                    n = len(evs[(evs["Mins"] > tramos[i]) & (evs["Mins"] <= tramos[i+1])])
                    conteo.append(n)
                return conteo

            g_col1, g_col2 = st.columns(2)

            with g_col1:
                st.markdown("<div class='seccion-titulo'>Goles a favor por tramo (15')</div>",
                            unsafe_allow_html=True)
                vals_gf = goles_tramos(goles_ev, "gol")
                fig_gf  = go.Figure(go.Bar(
                    x=labels_t, y=vals_gf,
                    marker_color="#34D399", opacity=0.85,
                    text=vals_gf, textposition="outside",
                ))
                fig_gf.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#9CA3AF", size=11, family="Inter"),
                    margin=dict(l=0, r=0, t=10, b=0), height=220,
                    xaxis=dict(gridcolor="#1F2937"), yaxis=dict(gridcolor="#1F2937"),
                )
                st.plotly_chart(fig_gf, use_container_width=True, key="chart_gf")

            with g_col2:
                st.markdown("<div class='seccion-titulo'>Goles en contra por tramo (15')</div>",
                            unsafe_allow_html=True)
                vals_gc = goles_tramos(goles_ev, "gol_contra")
                fig_gc  = go.Figure(go.Bar(
                    x=labels_t, y=vals_gc,
                    marker_color="#F87171", opacity=0.85,
                    text=vals_gc, textposition="outside",
                ))
                fig_gc.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#9CA3AF", size=11, family="Inter"),
                    margin=dict(l=0, r=0, t=10, b=0), height=220,
                    xaxis=dict(gridcolor="#1F2937"), yaxis=dict(gridcolor="#1F2937"),
                )
                st.plotly_chart(fig_gc, use_container_width=True, key="chart_gc")

        # ── Efectividad Local vs Visitante ─────────────────────────────────
        if "condicion" in fixture.columns and "goles_favor" in fixture.columns:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown("<div class='seccion-titulo'>Efectividad Local vs Visitante</div>",
                        unsafe_allow_html=True)

            ev_col = st.columns(2)
            for col_ef, cond in zip(ev_col, ["Local", "Visitante"]):
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
                    labels=["Victorias","Empates","Derrotas"],
                    values=[w_c, d_c, l_c],
                    marker_colors=["#34D399","#FBBF24","#F87171"],
                    hole=0.55,
                    textinfo="label+percent",
                    textfont=dict(size=11, family="Inter"),
                ))
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#9CA3AF", family="Inter"),
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=200,
                    showlegend=False,
                    annotations=[dict(
                        text=f"<b>{efec}%</b>",
                        x=0.5, y=0.5, font_size=18, showarrow=False,
                        font_color="#F9FAFB",
                    )],
                )
                with col_ef:
                    st.markdown(f"<div style='text-align:center;font-size:.72em;"
                                f"color:#9CA3AF;margin-bottom:4px'>{cond} · {pj_c} PJ</div>",
                                unsafe_allow_html=True)
                    st.plotly_chart(fig_pie, use_container_width=True, key=f"pie_{cond}")

    if st.button("← Volver al plantel", key="btn_volver"):
        st.session_state.jugador_sel = None
        st.rerun()
