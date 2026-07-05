"""
1_Plantel_ficha.py — Estrella FC · Ficha de jugador consolidada
==================================================================
Antes: grid de cromos con fotos de todo el plantel + expander por jugador.
Ahora: selector único de jugador (más liviano, no carga fotos de todos)
que al elegir despliega TODA la info junta, sin expanders anidados:

  · Ficha básica (foto, posición, edad, estado, partidos, minutos)
  · Métricas clave + radar de rendimiento      (eventos: events_clean.csv)
  · Alertas (amarillas, sanciones, lesiones)    (data/sanciones_lesiones.csv)
  · Rendimiento físico (últimos tests)          (data/distancia_fisica.csv,
                                                  data/saltos_fisico.csv,
                                                  data/velocidad_fisica.csv)
  · Mapa de cancha (calor + pases)              (events_clean.csv, mplsoccer)
  · Videos del jugador                          (data/videos_jugadores.csv)
  · Observaciones + detalle por partido

La "Vista colectiva" (stats de equipo) se mantiene igual que antes,
activable con el botón "📊 Stats" — no depende del selector de jugador.

NOTA: cada página del proyecto mantiene sus propias funciones de carga
(no hay un módulo de datos compartido), así que varias funciones de acá
son copias deliberadas de 3_Rendimiento_fisico.py, 5_Alertas.py,
8_Player_review.py y 2_Mapa_cancha.py, adaptadas a una sola ficha.
"""

import os
import base64
import mimetypes
from datetime import date

import numpy as np
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from mplsoccer import Pitch
import matplotlib.pyplot as plt

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
FOTOS_DIR      = os.path.join(BASE, "static", "fotos")
DATA_PATH      = os.path.join(BASE, "data", "events_clean.csv")
FIXT_PATH      = os.path.join(BASE, "data", "fixture.csv")
JUG_PATH       = os.path.join(BASE, "data", "Jugadores.csv")
SANC_PATH      = os.path.join(BASE, "data", "sanciones_lesiones.csv")
ESCUDO         = os.path.join(BASE, "static", "escudo.png")

DIST_PATH      = os.path.join(BASE, "data", "distancia_fisica.csv")
SALTO_PATH     = os.path.join(BASE, "data", "saltos_fisico.csv")
VELOC_PATH     = os.path.join(BASE, "data", "velocidad_fisica.csv")
VIDEOS_JUG_CSV = os.path.join(BASE, "data", "videos_jugadores.csv")

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.badge {
    display: inline-block; border-radius: 4px;
    padding: 2px 7px; font-size: .68em; font-weight: 700;
}
.badge-verde  { background: #064e3b; color: #34D399; }
.badge-rojo   { background: #450a0a; color: #F87171; }
.badge-amari  { background: #451a03; color: #FBBF24; }

.ficha-header {
    background: #0F172A;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 16px;
    border-left: 4px solid var(--accent, #E23E3E);
}
.ficha-label { font-size: .58em; color: #6B7280; text-transform: uppercase; letter-spacing: 3px; }
.ficha-valor { font-size: 1em; font-weight: 800; color: #F9FAFB; }

.seccion-titulo {
    font-size: .62em; font-weight: 700; color: #4B5563;
    text-transform: uppercase; letter-spacing: 3px;
    border-bottom: 1px solid #1F2937;
    padding-bottom: 6px; margin: 22px 0 12px 0;
}

.macro-card {
    background: #111827; border: 1px solid #1F2937;
    border-radius: 8px; padding: 14px 16px; text-align: center;
}
.macro-num   { font-size: 1.8em; font-weight: 800; color: #F9FAFB; }
.macro-label { font-size: .60em; color: #6B7280; text-transform: uppercase; letter-spacing: 2px; }

.mini-card {
    background: #111827; border: 1px solid #1F2937;
    border-radius: 8px; padding: 12px 14px;
}
.mini-titulo { font-size: .62em; color: #6B7280; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 6px; }
.mini-valor  { font-size: 1.3em; font-weight: 800; color: #F9FAFB; }
.mini-sub    { font-size: .72em; color: #6B7280; margin-top: 2px; }
.mini-delta-up   { color: #F87171; font-weight: 700; }
.mini-delta-down { color: #34D399; font-weight: 700; }

.video-title { font-size: .92em; font-weight: 700; color: #F9FAFB; margin-bottom: 2px; }
.video-desc  { font-size: .78em; color: #9CA3AF; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Constantes de posición / radar
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

ESCALA_RADAR = {
    "pase":            136,
    "recuperacion":     63,
    "conduccion":       22,
    "despeje":          65,
    "falta cometida":    8,
    "remate":            8,
    "gol":               2,
    "centro":           21,
}

EVAL_COLORS = {
    "NIVEL ÉLITE": "#A78BFA", "MUY BUENO": "#34D399", "BUENO": "#60A5FA",
    "ACEPTABLE": "#FBBF24", "BAJO": "#F87171",
}
EVAL_COLORS_VELOC = {
    "ÉLITE": "#A78BFA", "MUY BUENO": "#34D399", "BUENO": "#60A5FA",
    "REGULAR": "#FBBF24", "MARGEN DE MEJORA": "#F87171",
}


# ══════════════════════════════════════════════════════════════════════════════
# Carga de datos
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=0)
def cargar_jugadores() -> pd.DataFrame:
    df = pd.read_csv(JUG_PATH)
    df["nombre"] = df["nombre"].str.strip().str.title()
    df["posicion"] = df["posicion"].str.strip().str.title()

    if "fecha_nacimiento" in df.columns:
        df["fecha_nacimiento"] = pd.to_datetime(
            df["fecha_nacimiento"], format="%d-%m-%Y", errors="coerce"
        )
        hoy = pd.Timestamp.today()
        df["edad"] = (
            hoy.year - df["fecha_nacimiento"].dt.year
            - ((hoy.month < df["fecha_nacimiento"].dt.month)
               | ((hoy.month == df["fecha_nacimiento"].dt.month)
                  & (hoy.day < df["fecha_nacimiento"].dt.day)))
        )
        df["edad"] = df["edad"].astype("Int64")
    else:
        df["edad"] = "—"
    return df


@st.cache_data(ttl=0)
def cargar_alertas() -> pd.DataFrame:
    if not os.path.exists(SANC_PATH):
        return pd.DataFrame()
    df = pd.read_csv(SANC_PATH)
    if not df.empty and "fecha_regreso" in df.columns:
        df["fecha_regreso"] = pd.to_datetime(df["fecha_regreso"], dayfirst=True, errors="coerce")
    return df


@st.cache_data(ttl=0)
def cargar_eventos() -> pd.DataFrame:
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame()
    df = pd.read_csv(DATA_PATH)
    df["Mins"] = pd.to_numeric(df["Mins"], errors="coerce")
    df["Secs"] = pd.to_numeric(df["Secs"], errors="coerce")
    for col in ["X", "Y", "X2", "Y2"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(ttl=0)
def cargar_fixture() -> pd.DataFrame:
    if not os.path.exists(FIXT_PATH):
        return pd.DataFrame()
    return pd.read_csv(FIXT_PATH)


def parse_fecha_flexible(serie):
    """Copiado de 3_Rendimiento_fisico.py: evita que dayfirst=True rompa fechas ISO."""
    s = serie.astype(str).str.strip()
    resultado = pd.Series(pd.NaT, index=s.index)
    iso_mask = s.str.match(r"^\d{4}-\d{2}-\d{2}$")
    if iso_mask.any():
        resultado.loc[iso_mask] = pd.to_datetime(s[iso_mask], format="%Y-%m-%d", errors="coerce")
    resto_mask = ~iso_mask
    if resto_mask.any():
        resultado.loc[resto_mask] = pd.to_datetime(s[resto_mask], dayfirst=True, errors="coerce")
    return resultado


def nombre_fecha_test(fecha):
    if pd.isna(fecha):
        return "Fecha desconocida"
    dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    return f"{dias[fecha.weekday()]} {fecha.strftime('%d/%m/%Y')}"


@st.cache_data(ttl=0)
def cargar_distancia() -> pd.DataFrame:
    if not os.path.exists(DIST_PATH):
        return pd.DataFrame(columns=["fecha", "jugador", "distancia_km"])
    df = pd.read_csv(DIST_PATH)
    df["jugador"] = df["jugador"].astype(str).str.strip().str.title()
    df["distancia_km"] = pd.to_numeric(df["distancia_km"], errors="coerce")
    return df


@st.cache_data(ttl=0)
def cargar_saltos() -> pd.DataFrame:
    cols = ["fecha", "jugador", "altura_cm", "potencia_w",
            "potencia_relativa", "peso_kg", "evaluacion"]
    if not os.path.exists(SALTO_PATH):
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(SALTO_PATH)
    df.columns = [c.strip().lower() for c in df.columns]
    df["jugador"] = df["jugador"].astype(str).str.strip().str.title()
    df["fecha"] = parse_fecha_flexible(df["fecha"])
    for c in ["altura_cm", "potencia_w", "potencia_relativa", "peso_kg"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "evaluacion" in df.columns:
        df["evaluacion"] = df["evaluacion"].astype(str).str.strip().str.upper()
    return df


@st.cache_data(ttl=0)
def cargar_velocidad() -> pd.DataFrame:
    cols = ["fecha", "jugador", "tiempo_40m", "tiempo_10m", "tiempo_20m",
            "velocidad_pico", "puesto", "evaluacion"]
    if not os.path.exists(VELOC_PATH):
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(VELOC_PATH)
    df = df.rename(columns={
        "Nombre": "nombre_completo", "Fecha": "fecha", "40m": "tiempo_40m",
        "10m": "tiempo_10m", "20m": "tiempo_20m", "Pico": "velocidad_pico",
        "Observacion": "puesto", "Evaluacion_Nivel": "evaluacion",
    })
    df["jugador"] = (
        df["nombre_completo"].astype(str).str.split(",").str[0].str.strip().str.title()
    )
    df["fecha"] = parse_fecha_flexible(df["fecha"])
    for c in ["tiempo_40m", "tiempo_10m", "tiempo_20m", "velocidad_pico"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "puesto" in df.columns:
        df["puesto"] = df["puesto"].astype(str).str.strip().str.title()
    if "evaluacion" in df.columns:
        df["evaluacion"] = df["evaluacion"].astype(str).str.strip().str.upper()
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA
    return df[cols]


@st.cache_data(ttl=0)
def cargar_videos_jugadores() -> pd.DataFrame:
    cols = ["jugador", "titulo", "youtube_id", "fecha", "descripcion"]
    if not os.path.exists(VIDEOS_JUG_CSV):
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(VIDEOS_JUG_CSV)
    df["jugador"] = df["jugador"].str.strip().str.title()
    return df


def nombre_rival(num_fecha, fixture: pd.DataFrame):
    if fixture.empty:
        return f"Fecha {num_fecha}"
    fila = fixture[fixture["fecha"] == num_fecha]
    if fila.empty:
        return f"Fecha {num_fecha}"
    return f"Fecha {num_fecha} · vs {fila['rival'].values[0]}"


# ══════════════════════════════════════════════════════════════════════════════
# Helpers — plantel / eventos / alertas
# ══════════════════════════════════════════════════════════════════════════════
def estado_jugador(nombre: str, alertas: pd.DataFrame) -> tuple:
    hoy = pd.Timestamp(date.today())
    if alertas.empty:
        return "✅", "Disponible", "badge-verde"
    fila = alertas[alertas["nombre"].str.lower() == nombre.lower()]
    if fila.empty:
        return "✅", "Disponible", "badge-verde"
    for _, row in fila.iterrows():
        tipo = str(row.get("tipo", "")).lower()
        regreso = row.get("fecha_regreso", None)
        activo = pd.isna(regreso) or regreso >= hoy
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


def umbral_suspension(sanciones_cumplidas):
    """Copiado de 5_Alertas.py: cuántas amarillas se necesitan para la próxima suspensión."""
    return {0: 5, 1: 4, 2: 3}.get(sanciones_cumplidas, 2)


def resumen_alertas_jugador(nombre: str, alertas: pd.DataFrame) -> dict:
    """
    Versión "para un solo jugador" de la lógica de 5_Alertas.py: estado actual,
    amarillas en el ciclo vigente, cuántas faltan para la próxima suspensión,
    y motivo/fecha de regreso si está sancionado o lesionado.
    """
    icono, estado_txt, badge_cls = estado_jugador(nombre, alertas)
    resultado = {
        "icono": icono, "estado_txt": estado_txt, "badge_cls": badge_cls,
        "amarillas_total": 0, "amarillas_ciclo": 0, "faltan_suspension": None,
        "motivo": None, "fecha_regreso": None,
    }
    if alertas.empty:
        return resultado

    fila = alertas[alertas["nombre"].str.lower() == nombre.lower()]
    if fila.empty:
        return resultado

    hoy = pd.Timestamp(date.today())
    amarillas = fila[fila["tipo"].str.lower() == "amarilla"]
    sanciones = fila[fila["tipo"].str.lower().isin(["sanción", "sancion", "roja directa"])]
    lesiones = fila[fila["tipo"].str.lower().isin(["lesión", "lesion"])]

    resultado["amarillas_total"] = len(amarillas)
    sanciones_cumplidas = len(sanciones)
    umbral = umbral_suspension(sanciones_cumplidas)
    ciclo = len(amarillas) - sum([5, 4, 3, 2][:sanciones_cumplidas]) if sanciones_cumplidas > 0 else len(amarillas)
    resultado["amarillas_ciclo"] = max(ciclo, 0)
    resultado["faltan_suspension"] = max(umbral - resultado["amarillas_ciclo"], 0)

    activas_sancion = sanciones[sanciones["fecha_regreso"].isna() | (sanciones["fecha_regreso"] >= hoy)]
    activas_lesion = lesiones[lesiones["fecha_regreso"].isna() | (lesiones["fecha_regreso"] >= hoy)]
    activa = pd.concat([activas_sancion, activas_lesion])
    if not activa.empty:
        fila_activa = activa.iloc[0]
        resultado["motivo"] = fila_activa.get("motivo", "—")
        regreso = fila_activa.get("fecha_regreso", None)
        resultado["fecha_regreso"] = (
            regreso.strftime("%d/%m/%Y") if pd.notna(regreso) else "Sin fecha definida"
        )
    return resultado


def mins_reales_partido(ep: pd.DataFrame) -> pd.DataFrame:
    m1 = ep[ep["mitad"] == 1]
    m2 = ep[ep["mitad"] == 2]
    if m1.empty or m2.empty:
        ep = ep.copy()
        ep["Mins_real"] = ep["Mins"]
        return ep
    m1_max = m1["Mins"].max()
    m2_min = m2["Mins"].min()
    resetea = m2_min < 10
    ep = ep.copy()
    if resetea:
        offset = m1_max if not pd.isna(m1_max) else 45
        ep["Mins_real"] = ep.apply(
            lambda r: r["Mins"] + offset if r["mitad"] == 2 else r["Mins"], axis=1
        )
    else:
        ep["Mins_real"] = ep["Mins"]
    return ep


def calcular_minutos(nombre: str, eventos: pd.DataFrame) -> int:
    if eventos.empty:
        return 0
    j = eventos[eventos["Player"].str.lower() == nombre.lower()]
    if j.empty:
        return 0
    total = 0
    for f in j["fecha"].unique():
        ep_fixed = mins_reales_partido(eventos[eventos["fecha"] == f])
        jp = ep_fixed[ep_fixed["Player"].str.lower() == nombre.lower()]
        primero = jp["Mins_real"].min()
        ultimo = jp["Mins_real"].max()
        mins = ultimo if primero <= 15 else max(1, ultimo - primero + 1)
        total += mins
    return int(total)


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
    base["minutos"] = calcular_minutos(nombre, eventos)
    for ev in ["pase", "recuperacion", "conduccion", "despeje",
               "falta cometida", "remate", "gol", "centro"]:
        base[ev] = int(len(j[j["Event"] == ev]))
    return base


def radar_jugador(nombre: str, posicion: str, eventos: pd.DataFrame, color: str) -> go.Figure:
    metricas = METRICAS_POS.get(posicion, ["pase", "recuperacion", "remate"])
    s = stats_jugador(nombre, eventos)
    cats = [LABEL_METRICAS.get(m, m) for m in metricas]
    vals_real = [s.get(m, 0) for m in metricas]
    vals_norm = [
        min(round(vals_real[k] / ESCALA_RADAR.get(metricas[k], 1) * 100, 1), 100)
        for k in range(len(metricas))
    ]
    cats_c = cats + [cats[0]]
    vals_norm_c = vals_norm + [vals_norm[0]]
    vals_real_c = vals_real + [vals_real[0]]

    fig = go.Figure(go.Scatterpolar(
        r=vals_norm_c, theta=cats_c, fill="toself",
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.15)",
        line=dict(color=color, width=2.5),
        marker=dict(color=color, size=7),
        customdata=vals_real_c,
        hovertemplate="%{theta}: <b>%{customdata}</b><extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False,
                             gridcolor="#374151", color="#6B7280"),
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
def foto_b64(foto_path: str):
    if os.path.exists(foto_path):
        mime, _ = mimetypes.guess_type(foto_path)
        mime = mime or "image/jpeg"
        with open(foto_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"data:{mime};base64,{b64}"
    return None


# ══════════════════════════════════════════════════════════════════════════════
# Helpers — mapa de cancha (adaptado de 2_Mapa_cancha.py, filtrado a un jugador)
# ══════════════════════════════════════════════════════════════════════════════
def clasificar_pases(df: pd.DataFrame) -> pd.DataFrame:
    """Copiado de 2_Mapa_cancha.py: marca cada pase como exitoso o no según
    si el próximo evento cercano (misma zona, hasta 5 eventos después) continúa
    la jugada o la corta."""
    df = df.copy()
    df["pase_ok"] = False
    eventos_continuidad = {"pase", "centro", "conduccion", "corner",
                            "remate", "tiro libre", "falta recibida"}
    eventos_corte = {"perdida", "despeje", "recuperacion"}
    tolerancia = 8
    df = df.reset_index(drop=True)

    for i in range(len(df)):
        fila = df.iloc[i]
        if str(fila["Event"]).lower() != "pase":
            continue
        if pd.isna(fila["X2"]) or pd.isna(fila["Y2"]):
            continue
        destino_x, destino_y = fila["X2"], fila["Y2"]
        limite = min(i + 5, len(df))
        for j in range(i + 1, limite):
            siguiente = df.iloc[j]
            if pd.isna(siguiente["X"]) or pd.isna(siguiente["Y"]):
                continue
            distancia = np.sqrt((destino_x - siguiente["X"]) ** 2 + (destino_y - siguiente["Y"]) ** 2)
            if distancia > tolerancia:
                continue
            evento_sig = str(siguiente["Event"]).lower()
            if evento_sig in eventos_continuidad:
                df.at[i, "pase_ok"] = True
                break
            if evento_sig in eventos_corte:
                break
    return df


def crear_cancha():
    pitch = Pitch(pitch_type="opta", pitch_color="#111827", line_color="#374151",
                  linewidth=1.5, line_zorder=10, corner_arcs=True)
    fig, ax = pitch.draw(figsize=(6, 4))
    fig.set_facecolor("#111827")
    return pitch, fig, ax


def mapa_calor_jugador(nombre: str, eventos: pd.DataFrame):
    j = eventos[eventos["Player"].str.lower() == nombre.lower()]
    j = j[j["X"].notna() & j["Y"].notna()]
    if j.empty:
        return None
    pitch, fig, ax = crear_cancha()
    bin_stat = pitch.bin_statistic(j["X"], j["Y"], statistic="count", bins=(8, 6))
    pitch.heatmap(bin_stat, ax=ax, cmap="Reds", alpha=0.6, zorder=1)
    pitch.draw(ax=ax)
    return fig


def mapa_pases_jugador(nombre: str, eventos: pd.DataFrame):
    """Flechas de pases del jugador (promediadas por zona), verde = exitoso,
    rojo = no continuó la jugada — mismo criterio que 2_Mapa_cancha.py."""
    eventos_clasificados = clasificar_pases(eventos)
    j = eventos_clasificados[
        (eventos_clasificados["Player"].str.lower() == nombre.lower())
        & (eventos_clasificados["Event"] == "pase")
        & eventos_clasificados["X2"].notna()
        & eventos_clasificados["Y2"].notna()
    ].copy()
    if j.empty:
        return None

    j["X_bin"] = (j["X"] // 20 * 20 + 10).astype(int)
    j["Y_bin"] = (j["Y"] // 20 * 20 + 10).astype(int)
    j["X2_bin"] = (j["X2"] // 20 * 20 + 10).astype(int)
    j["Y2_bin"] = (j["Y2"] // 20 * 20 + 10).astype(int)
    j = j[(j["X_bin"] != j["X2_bin"]) | (j["Y_bin"] != j["Y2_bin"])]

    pitch, fig, ax = crear_cancha()
    for sub, color in [(j[j["pase_ok"]], "#22C55E"), (j[~j["pase_ok"]], "#EF4444")]:
        if sub.empty:
            continue
        agrupado = (
            sub.groupby(["X_bin", "Y_bin", "X2_bin", "Y2_bin"])
            .agg(cantidad=("X", "count"), x_o=("X", "mean"), y_o=("Y", "mean"),
                 x_d=("X2", "mean"), y_d=("Y2", "mean"))
            .reset_index()
        )
        if agrupado.empty:
            continue
        max_cant = agrupado["cantidad"].max()
        for _, fila in agrupado.iterrows():
            grosor = 1 + (fila["cantidad"] / max_cant) * 6
            alpha = 0.45 + (fila["cantidad"] / max_cant) * 0.5
            pitch.arrows(fila["x_o"], fila["y_o"], fila["x_d"], fila["y_d"],
                         ax=ax, color=color, width=grosor, alpha=alpha)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# Helpers — resumen de físico (última fila por dataset)
# ══════════════════════════════════════════════════════════════════════════════
def ultimo_y_delta(df_jugador: pd.DataFrame, col: str):
    """Devuelve (último valor, fecha, delta vs el registro anterior o None)."""
    if df_jugador.empty:
        return None, None, None
    df_ord = df_jugador.sort_values("fecha")
    ultimo = df_ord.iloc[-1]
    delta = None
    if len(df_ord) >= 2:
        anterior = df_ord.iloc[-2]
        if pd.notna(ultimo[col]) and pd.notna(anterior[col]):
            delta = round(ultimo[col] - anterior[col], 2)
    return ultimo, ultimo["fecha"], delta


# ══════════════════════════════════════════════════════════════════════════════
# Carga global
# ══════════════════════════════════════════════════════════════════════════════
jugadores = cargar_jugadores()
alertas   = cargar_alertas()
eventos   = cargar_eventos()
fixture   = cargar_fixture()
dist      = cargar_distancia()
saltos    = cargar_saltos()
velocidad = cargar_velocidad()
videos_df = cargar_videos_jugadores()

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
    ver_col = st.button("📊 Stats", key="btn_col", width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:1px;background:#1F2937;margin:4px 0 16px 0'></div>",
            unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# KPIs rápidos del plantel (siempre visibles)
# ══════════════════════════════════════════════════════════════════════════════
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total", len(jugadores))
m2.metric("Arqueros", len(jugadores[jugadores["posicion"].str.lower() == "arquero"]))
m3.metric("Defensores", len(jugadores[jugadores["posicion"].str.lower() == "defensor"]))
m4.metric("Med. + Del.", len(jugadores[jugadores["posicion"].str.lower().isin(
    ["mediocampista", "delantero"])]))

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SELECTOR ÚNICO DE JUGADOR (reemplaza el grid de cromos)
# ══════════════════════════════════════════════════════════════════════════════
jugadores_ordenados = jugadores.sort_values("nombre")
opciones = ["— Elegí un jugador —"] + [
    f"{row['nombre']} · {row['posicion']}" for _, row in jugadores_ordenados.iterrows()
]
seleccion = st.selectbox("Buscar jugador", opciones, label_visibility="collapsed")

if seleccion == "— Elegí un jugador —":
    st.info("Elegí un jugador arriba para ver su ficha completa: rendimiento, físico, alertas, mapa de cancha y videos.")
else:
    nombre = seleccion.split(" · ")[0]
    row = jugadores[jugadores["nombre"] == nombre].iloc[0]
    posicion = row["posicion"]
    color = COLOR_POS.get(posicion, "#9CA3AF")

    _stats = stats_jugador(nombre, eventos)
    _alerta = resumen_alertas_jugador(nombre, alertas)
    _metr = METRICAS_POS.get(posicion, ["pase", "recuperacion", "remate"])
    foto_path = os.path.join(FOTOS_DIR, str(row.get("fotos", "")))
    src = foto_b64(foto_path)

    # ── Ficha básica: foto + datos principales ──────────────────────────────
    col_foto, col_ficha = st.columns([1, 4])
    with col_foto:
        if src:
            st.markdown(
                f"<img src='{src}' style='width:100%;border-radius:10px;"
                f"object-fit:cover;aspect-ratio:1/1'>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='width:100%;aspect-ratio:1/1;background:#1F2937;"
                "border-radius:10px;display:flex;align-items:center;"
                "justify-content:center;font-size:3rem'>👤</div>",
                unsafe_allow_html=True,
            )
    with col_ficha:
        camiseta = int(row["camiseta"]) if pd.notna(row.get("camiseta")) else "—"
        st.markdown(f"""
        <div style='--accent:{color}' class='ficha-header'>
            <div style='font-size:1.3em;font-weight:800;color:#F9FAFB;margin-bottom:10px'>
                #{camiseta} {nombre}
            </div>
            <div style='display:flex;gap:24px;flex-wrap:wrap'>
                <div><div class='ficha-label'>Posición</div>
                     <div class='ficha-valor' style='color:{color}'>{posicion}</div></div>
                <div><div class='ficha-label'>Edad</div>
                     <div class='ficha-valor'>{row.get("edad","—")}</div></div>
                <div><div class='ficha-label'>Partidos</div>
                     <div class='ficha-valor'>{_stats["partidos"]}</div></div>
                <div><div class='ficha-label'>Minutos</div>
                     <div class='ficha-valor'>{_stats["minutos"]}'</div></div>
                <div><div class='ficha-label'>Estado</div>
                     <span class='badge {_alerta["badge_cls"]}'>{_alerta["icono"]} {_alerta["estado_txt"]}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='seccion-titulo' style='margin-top:8px'>Métricas clave</div>",
                    unsafe_allow_html=True)
        mc = st.columns(len(_metr))
        for k, m in enumerate(_metr):
            mc[k].metric(LABEL_METRICAS.get(m, m), _stats.get(m, 0))

    # ── Radar de rendimiento ─────────────────────────────────────────────────
    if not eventos.empty:
        st.markdown("<div class='seccion-titulo'>📐 Perfil de rendimiento</div>",
                    unsafe_allow_html=True)
        fig_r = radar_jugador(nombre, posicion, eventos, color)
        st.plotly_chart(fig_r, width='stretch', key=f"radar_{nombre}")

    # ── Alertas ───────────────────────────────────────────────────────────────
    st.markdown("<div class='seccion-titulo'>🚨 Alertas</div>", unsafe_allow_html=True)
    ac1, ac2, ac3 = st.columns(3)
    ac1.markdown(f"""
    <div class='mini-card'><div class='mini-titulo'>Amarillas en ciclo</div>
        <div class='mini-valor'>{_alerta["amarillas_ciclo"]} / {_alerta["amarillas_total"]}</div>
        <div class='mini-sub'>Total temporada: {_alerta["amarillas_total"]}</div></div>
    """, unsafe_allow_html=True)
    ac2.markdown(f"""
    <div class='mini-card'><div class='mini-titulo'>Faltan para suspensión</div>
        <div class='mini-valor'>{_alerta["faltan_suspension"] if _alerta["faltan_suspension"] is not None else "—"}</div>
        <div class='mini-sub'>Amarillas</div></div>
    """, unsafe_allow_html=True)
    if _alerta["motivo"]:
        ac3.markdown(f"""
        <div class='mini-card'><div class='mini-titulo'>{_alerta["estado_txt"]}</div>
            <div class='mini-valor' style='font-size:.95em'>{_alerta["motivo"]}</div>
            <div class='mini-sub'>Regresa: {_alerta["fecha_regreso"]}</div></div>
        """, unsafe_allow_html=True)
    else:
        ac3.markdown(f"""
        <div class='mini-card'><div class='mini-titulo'>Estado actual</div>
            <span class='badge {_alerta["badge_cls"]}'>{_alerta["icono"]} {_alerta["estado_txt"]}</span></div>
        """, unsafe_allow_html=True)

    # ── Rendimiento físico ────────────────────────────────────────────────────
    st.markdown("<div class='seccion-titulo'>🏃 Rendimiento físico — últimos tests</div>",
                unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns(3)

    dist_j = dist[dist["jugador"] == nombre]
    with fc1:
        if dist_j.empty:
            st.markdown("<div class='mini-card'><div class='mini-titulo'>Distancia (GPS)</div>"
                        "<div class='mini-sub'>Sin apariciones en el Top 3</div></div>",
                        unsafe_allow_html=True)
        else:
            ultimo = dist_j.sort_values("fecha").iloc[-1]
            st.markdown(f"""
            <div class='mini-card'><div class='mini-titulo'>Distancia (GPS) · Top 3</div>
                <div class='mini-valor'>{ultimo["distancia_km"]:.1f} km</div>
                <div class='mini-sub'>{nombre_rival(ultimo["fecha"], fixture)}</div></div>
            """, unsafe_allow_html=True)

    saltos_j = saltos[saltos["jugador"] == nombre]
    with fc2:
        if saltos_j.empty:
            st.markdown("<div class='mini-card'><div class='mini-titulo'>Salto (CMJ)</div>"
                        "<div class='mini-sub'>Sin tests cargados</div></div>",
                        unsafe_allow_html=True)
        else:
            ultimo, fecha_u, delta = ultimo_y_delta(saltos_j, "potencia_relativa")
            ev = str(ultimo.get("evaluacion", "—"))
            color_ev = EVAL_COLORS.get(ev, "#9CA3AF")
            delta_html = ""
            if delta is not None:
                cls = "mini-delta-up" if delta > 0 else "mini-delta-down"
                signo = "▲" if delta > 0 else "▼"
                delta_html = f"<span class='{cls}'> {signo} {abs(delta):.1f}</span>"
            st.markdown(f"""
            <div class='mini-card'><div class='mini-titulo'>Salto (CMJ)</div>
                <div class='mini-valor'>{ultimo["potencia_relativa"]:.1f} W/kg{delta_html}</div>
                <div class='mini-sub' style='color:{color_ev}'>{ev} · {nombre_fecha_test(fecha_u)}</div></div>
            """, unsafe_allow_html=True)

    veloc_j = velocidad[velocidad["jugador"] == nombre]
    with fc3:
        if veloc_j.empty:
            st.markdown("<div class='mini-card'><div class='mini-titulo'>Velocidad (Sprint)</div>"
                        "<div class='mini-sub'>Sin tests cargados</div></div>",
                        unsafe_allow_html=True)
        else:
            ultimo, fecha_u, delta = ultimo_y_delta(veloc_j, "tiempo_40m")
            ev = str(ultimo.get("evaluacion", "—"))
            color_ev = EVAL_COLORS_VELOC.get(ev, "#9CA3AF")
            delta_html = ""
            if delta is not None:
                # Para tiempos, bajar es mejora → invertimos el color de la flecha
                cls = "mini-delta-down" if delta < 0 else "mini-delta-up"
                signo = "▼" if delta < 0 else "▲"
                delta_html = f"<span class='{cls}'> {signo} {abs(delta):.2f}s</span>"
            st.markdown(f"""
            <div class='mini-card'><div class='mini-titulo'>Velocidad · 40m</div>
                <div class='mini-valor'>{ultimo["tiempo_40m"]:.2f}s{delta_html}</div>
                <div class='mini-sub' style='color:{color_ev}'>{ev} · {nombre_fecha_test(fecha_u)}</div></div>
            """, unsafe_allow_html=True)

    # ── Mapa de cancha ────────────────────────────────────────────────────────
    if not eventos.empty:
        st.markdown("<div class='seccion-titulo'>🗺️ Mapa de cancha (temporada)</div>",
                    unsafe_allow_html=True)
        camp1, camp2 = st.columns(2)
        with camp1:
            st.caption("Mapa de calor")
            fig_calor = mapa_calor_jugador(nombre, eventos)
            if fig_calor is not None:
                st.pyplot(fig_calor, width='stretch')
                plt.close(fig_calor)
            else:
                st.info("Sin eventos con coordenadas para este jugador.")
        with camp2:
            st.caption("Pases — verde exitoso / rojo no continuó")
            fig_pases = mapa_pases_jugador(nombre, eventos)
            if fig_pases is not None:
                st.pyplot(fig_pases, width='stretch')
                plt.close(fig_pases)
            else:
                st.info("Sin pases con coordenadas para este jugador.")

    # ── Videos ────────────────────────────────────────────────────────────────
    st.markdown("<div class='seccion-titulo'>🎬 Videos</div>", unsafe_allow_html=True)
    videos_jug = videos_df[videos_df["jugador"].str.lower() == nombre.lower()]
    if videos_jug.empty:
        st.markdown(f"""
        <div style='background:#111827;border:1px dashed #374151;border-radius:12px;
                    padding:32px 24px;text-align:center'>
            <div style='font-size:2rem;margin-bottom:8px'>🎬</div>
            <div style='color:#9CA3AF;font-size:.85em'>
                Sin videos cargados para {nombre} en <code>data/videos_jugadores.csv</code>.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        videos_jug = videos_jug.sort_values("fecha", ascending=False)
        for _, vrow in videos_jug.iterrows():
            with st.container(border=True):
                st.markdown(f"""
                <div class='video-title'>📹 {vrow['titulo']}
                    <span style='color:#6B7280;font-size:.8em;font-weight:400;margin-left:8px'>
                        · Fecha {vrow['fecha']}
                    </span>
                </div>
                <div class='video-desc'>{vrow['descripcion']}</div>
                """, unsafe_allow_html=True)
                st.components.v1.iframe(
                    f"https://www.youtube.com/embed/{vrow['youtube_id']}", height=360,
                )

    # ── Observaciones ─────────────────────────────────────────────────────────
    st.markdown("<div class='seccion-titulo'>📝 Observaciones</div>", unsafe_allow_html=True)
    if "obs_cache" not in st.session_state:
        st.session_state.obs_cache = {}
    obs_val = st.session_state.obs_cache.get(nombre, "")
    nueva = st.text_area(
        "Notas", value=obs_val, height=110,
        placeholder="Notas tácticas, comportamientos...",
        key=f"obs_{nombre}", label_visibility="collapsed",
    )
    if st.button("💾 Guardar", key=f"save_{nombre}"):
        st.session_state.obs_cache[nombre] = nueva
        st.success("Guardado.")

    # ── Detalle por partido ────────────────────────────────────────────────────
    if not eventos.empty:
        j_ev = eventos[eventos["Player"].str.lower() == nombre.lower()]
        if not j_ev.empty:
            st.markdown("<div class='seccion-titulo'>📋 Detalle por partido</div>",
                        unsafe_allow_html=True)
            rows_t = []
            for fecha in sorted(j_ev["fecha"].unique()):
                jf = j_ev[j_ev["fecha"] == fecha]
                fila_t = {"Fecha": int(fecha)}
                for m in _metr:
                    fila_t[LABEL_METRICAS.get(m, m)] = int(len(jf[jf["Event"] == m]))
                rows_t.append(fila_t)
            st.dataframe(pd.DataFrame(rows_t), hide_index=True, width='stretch')

# ══════════════════════════════════════════════════════════════════════════════
# VISTA COLECTIVA (sin cambios respecto a la versión anterior)
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
        gf = fixture["goles_favor"].sum() if "goles_favor" in fixture.columns else "—"
        gc = fixture["goles_contra"].sum() if "goles_contra" in fixture.columns else "—"
        pj = len(fixture)
        wins = len(fixture[fixture["goles_favor"] > fixture["goles_contra"]]) \
            if "goles_favor" in fixture.columns else 0
        draws = len(fixture[fixture["goles_favor"] == fixture["goles_contra"]]) \
            if "goles_favor" in fixture.columns else 0
        loses = pj - wins - draws

        k1, k2, k3, k4, k5, k6 = st.columns(6)
        for col_m, lbl, val in zip(
            [k1, k2, k3, k4, k5, k6],
            ["PJ", "Victorias", "Empates", "Derrotas", "Goles F.", "Goles C."],
            [pj, wins, draws, loses, gf, gc],
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
            tramos = [0, 15, 30, 45, 60, 75, 90, 120]
            labels_t = ["1-15", "16-30", "31-45", "46-60", "61-75", "76-90", "90+"]

            def goles_tramos(df_g, ev):
                return [len(df_g[(df_g["Event"] == ev) &
                                 (df_g["Mins"] > tramos[i]) &
                                 (df_g["Mins"] <= tramos[i + 1])])
                        for i in range(len(tramos) - 1)]

            g1, g2 = st.columns(2)
            for col_g, ev_name, color_b, titulo in [
                (g1, "gol", "#34D399", "Goles a favor por tramo (15')"),
                (g2, "gol_contra", "#F87171", "Goles en contra por tramo (15')"),
            ]:
                with col_g:
                    st.markdown(f"<div class='seccion-titulo'>{titulo}</div>",
                                unsafe_allow_html=True)
                    vals_g = goles_tramos(goles_ev, ev_name)
                    fig_g = go.Figure(go.Bar(
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
                    st.plotly_chart(fig_g, width='stretch', key=f"bar_{ev_name}")

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
                w_c = len(sub[sub["goles_favor"] > sub["goles_contra"]])
                d_c = len(sub[sub["goles_favor"] == sub["goles_contra"]])
                l_c = pj_c - w_c - d_c
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
                    st.plotly_chart(fig_pie, width='stretch', key=f"pie_{cond}")
