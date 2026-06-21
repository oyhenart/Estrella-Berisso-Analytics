"""
3_Rendimiento_fisico.py — Estrella FC · Rendimiento Físico (GPS)
==================================================================
Carga manual: el CT pasa por mensaje el Top 3 de distancia recorrida
por partido (dato de un software de GPS externo, sin integración
directa con esta app). Se carga a mano en data/distancia_fisica.csv
con columnas: fecha, jugador, distancia_km

El software del CT reporta un margen de error de ±0.3 a 1 km.
"""

import os
import streamlit as st
import pandas as pd

from components.layout import inject_css, render_sidebar, render_header

st.set_page_config(
    page_title="Rendimiento Físico",
    page_icon="🏃",
    layout="wide"
)

inject_css()

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
render_sidebar(BASE)

render_header(
    "Torneo Promocional Amateur 2026",
    "Rendimiento físico · GPS"
)

DIST_PATH    = os.path.join(BASE, "data", "distancia_fisica.csv")
FIXTURE_PATH = os.path.join(BASE, "data", "fixture.csv")

MARGEN_MIN = 0.3
MARGEN_MAX = 1.0

# ── Aviso de margen de error (siempre visible, es info del propio dato) ──────
st.info(
    f"📡 Datos provistos por el software de GPS del CT. "
    f"Margen de error declarado: ±{MARGEN_MIN}–{MARGEN_MAX} km por jugador."
)


# ==========================
# CARGA DE DATOS
# ==========================
@st.cache_data(ttl=0)
def cargar_distancia():
    if not os.path.exists(DIST_PATH):
        return pd.DataFrame(columns=["fecha", "jugador", "distancia_km"])
    df = pd.read_csv(DIST_PATH)
    df["jugador"] = df["jugador"].astype(str).str.strip().str.title()
    df["distancia_km"] = pd.to_numeric(df["distancia_km"], errors="coerce")
    return df


@st.cache_data(ttl=0)
def cargar_fixture():
    if not os.path.exists(FIXTURE_PATH):
        return pd.DataFrame()
    return pd.read_csv(FIXTURE_PATH)


dist = cargar_distancia()
fixture = cargar_fixture()

if dist.empty:
    st.warning(
        "Todavía no hay datos de distancia cargados. "
        "Agregá filas en `data/distancia_fisica.csv` con columnas: "
        "`fecha, jugador, distancia_km`."
    )
    st.stop()


def nombre_rival(num_fecha):
    """Devuelve 'Fecha N · vs Rival' si existe en el fixture, sino solo 'Fecha N'."""
    if fixture.empty:
        return f"Fecha {num_fecha}"
    fila = fixture[fixture["fecha"] == num_fecha]
    if fila.empty:
        return f"Fecha {num_fecha}"
    rival = fila["rival"].values[0]
    return f"Fecha {num_fecha} · vs {rival}"


# ==========================
# PODIO POR FECHA
# ==========================
st.subheader("🥇 Top 3 · Distancia recorrida")

fechas_disponibles = sorted(dist["fecha"].unique().tolist(), reverse=True)
fecha_sel = st.selectbox(
    "Seleccioná el partido",
    fechas_disponibles,
    format_func=nombre_rival,
)

df_fecha = (
    dist[dist["fecha"] == fecha_sel]
    .sort_values("distancia_km", ascending=False)
    .reset_index(drop=True)
)

if df_fecha.empty:
    st.info("Sin datos cargados para esta fecha.")
else:
    medallas = ["🥇", "🥈", "🥉"]
    cols = st.columns(len(df_fecha))

    for i, (_, row) in enumerate(df_fecha.iterrows()):
        medalla = medallas[i] if i < len(medallas) else "•"
        with cols[i]:
            st.markdown(f"""
            <div style='background:#111827; border:1px solid rgba(255,255,255,.04);
                        border-radius:14px; padding:22px; text-align:center;
                        box-shadow: 0 10px 28px rgba(0,0,0,.28);'>
                <div style='font-size:2rem;'>{medalla}</div>
                <div style='margin-top:8px; font-size:1.05rem; font-weight:800; color:#F9FAFB;'>
                    {row['jugador']}
                </div>
                <div style='margin-top:6px; font-size:1.9rem; font-weight:800; color:#E23E3E;'>
                    {row['distancia_km']:.1f} km
                </div>
                <div style='margin-top:6px; color:#6B7280; font-size:.72rem;'>
                    ±{MARGEN_MIN}–{MARGEN_MAX} km
                </div>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# ==========================
# HISTORIAL COMPLETO
# ==========================
st.subheader("📜 Historial completo")

historial = dist.sort_values(["fecha", "distancia_km"], ascending=[False, False]).copy()
historial["Partido"] = historial["fecha"].apply(nombre_rival)
historial_view = historial[["Partido", "jugador", "distancia_km"]].rename(
    columns={"jugador": "Jugador", "distancia_km": "Distancia (km)"}
)

st.dataframe(
    historial_view,
    hide_index=True,
    use_container_width=True,
)

st.divider()

# ==========================
# ACUMULADO POR JUGADOR (TEMPORADA)
# ==========================
st.subheader("📈 Acumulado por jugador en la temporada")

acumulado = (
    dist.groupby("jugador")["distancia_km"]
    .agg(partidos="count", total_km="sum", promedio_km="mean")
    .sort_values("total_km", ascending=False)
    .reset_index()
    .rename(columns={
        "jugador": "Jugador",
        "partidos": "Partidos en Top 3",
        "total_km": "Total (km)",
        "promedio_km": "Promedio (km)",
    })
)
acumulado["Total (km)"] = acumulado["Total (km)"].round(1)
acumulado["Promedio (km)"] = acumulado["Promedio (km)"].round(1)

st.dataframe(
    acumulado,
    hide_index=True,
    use_container_width=True,
)

st.caption(
    "Este acumulado solo contempla partidos en los que el jugador apareció "
    "en el Top 3 de distancia recorrida — no es la distancia total real de "
    "la temporada, ya que el CT solo reporta los 3 primeros por fecha."
)