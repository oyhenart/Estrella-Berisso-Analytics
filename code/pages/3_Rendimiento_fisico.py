"""
3_Rendimiento_fisico.py — Estrella FC · Rendimiento Físico (GPS + Salto)
==========================================================================
DISTANCIA (GPS)
Carga manual: el CT pasa por mensaje el Top 3 de distancia recorrida
por partido (dato de un software de GPS externo, sin integración
directa con esta app). Se carga a mano en data/distancia_fisica.csv
con columnas: fecha, jugador, distancia_km

El software del CT reporta un margen de error de ±0.3 a 1 km.

SALTO (CMJ)
Test de salto contramovimiento, evaluado a todo el plantel en distintas
fechas de la temporada. Se carga a mano en data/saltos_fisico.csv
con columnas: fecha, jugador, altura_cm, potencia_w, potencia_relativa,
peso_kg, evaluacion
"""

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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
    "Rendimiento físico · GPS y Salto"
)

DIST_PATH    = os.path.join(BASE, "data", "distancia_fisica.csv")
SALTO_PATH   = os.path.join(BASE, "data", "saltos_fisico.csv")
FIXTURE_PATH = os.path.join(BASE, "data", "fixture.csv")

MARGEN_MIN = 0.3
MARGEN_MAX = 1.0

EVAL_COLORS = {
    "NIVEL ÉLITE": "#A78BFA",
    "MUY BUENO":   "#34D399",
    "BUENO":       "#60A5FA",
    "ACEPTABLE":   "#FBBF24",
    "BAJO":        "#F87171",
}
EVAL_ORDER = ["NIVEL ÉLITE", "MUY BUENO", "BUENO", "ACEPTABLE", "BAJO"]


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
def cargar_saltos():
    cols = ["fecha", "jugador", "altura_cm", "potencia_w",
            "potencia_relativa", "peso_kg", "evaluacion"]
    if not os.path.exists(SALTO_PATH):
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(SALTO_PATH)
    df.columns = [c.strip().lower() for c in df.columns]
    df["jugador"] = df["jugador"].astype(str).str.strip().str.title()
    # A diferencia de "fecha" en distancia_fisica.csv (número de fixture),
    # acá "fecha" es la fecha calendario del entrenamiento (ej. 2026-07-02).
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce", dayfirst=True)
    for c in ["altura_cm", "potencia_w", "potencia_relativa", "peso_kg"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "evaluacion" in df.columns:
        df["evaluacion"] = df["evaluacion"].astype(str).str.strip().str.upper()
    return df


def nombre_fecha_salto(fecha):
    """Formatea la fecha calendario del entrenamiento, ej. 'Jue 02/07/2026'."""
    if pd.isna(fecha):
        return "Fecha desconocida"
    dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    return f"{dias[fecha.weekday()]} {fecha.strftime('%d/%m/%Y')}"


@st.cache_data(ttl=0)
def cargar_fixture():
    if not os.path.exists(FIXTURE_PATH):
        return pd.DataFrame()
    return pd.read_csv(FIXTURE_PATH)


dist = cargar_distancia()
saltos = cargar_saltos()
fixture = cargar_fixture()


def nombre_rival(num_fecha):
    """Devuelve 'Fecha N · vs Rival' si existe en el fixture, sino solo 'Fecha N'."""
    if fixture.empty:
        return f"Fecha {num_fecha}"
    fila = fixture[fixture["fecha"] == num_fecha]
    if fila.empty:
        return f"Fecha {num_fecha}"
    rival = fila["rival"].values[0]
    return f"Fecha {num_fecha} · vs {rival}"


# ==========================================================================
# SECCIÓN 1 · DISTANCIA (GPS)
# ==========================================================================
st.info(
    f"📡 Datos de distancia provistos por el software de GPS del CT. "
    f"Margen de error declarado: ±{MARGEN_MIN}–{MARGEN_MAX} km por jugador."
)

st.subheader("🥇 Top 3 · Distancia recorrida")

if dist.empty:
    st.warning(
        "Todavía no hay datos de distancia cargados. "
        "Agregá filas en `data/distancia_fisica.csv` con columnas: "
        "`fecha, jugador, distancia_km`."
    )
else:
    fechas_disponibles = sorted(dist["fecha"].unique().tolist(), reverse=True)
    fecha_sel = st.selectbox(
        "Seleccioná el partido",
        fechas_disponibles,
        format_func=nombre_rival,
        key="dist_fecha",
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

st.divider()

# ==========================================================================
# SECCIÓN 2 · TEST DE SALTO (CMJ)
# ==========================================================================
st.subheader("🦘 Test de Salto (CMJ)")

if saltos.empty:
    st.warning(
        "Todavía no hay datos de salto cargados. "
        "Agregá filas en `data/saltos_fisico.csv` con columnas: "
        "`fecha, jugador, altura_cm, potencia_w, potencia_relativa, peso_kg, evaluacion`."
    )
else:
    fechas_salto = sorted(saltos["fecha"].dropna().unique().tolist(), reverse=True)
    fecha_salto_sel = st.selectbox(
        "Seleccioná el test",
        fechas_salto,
        format_func=lambda f: nombre_fecha_salto(pd.Timestamp(f)),
        key="salto_fecha",
    )

    df_s = (
        saltos[saltos["fecha"] == fecha_salto_sel]
        .sort_values("potencia_relativa", ascending=False)
        .reset_index(drop=True)
    )

    if df_s.empty:
        st.info("Sin datos cargados para este test.")
    else:
        # Gráfico de barras · Potencia relativa por jugador, coloreado por evaluación
        fig = go.Figure()
        for ev in EVAL_ORDER:
            sub = df_s[df_s["evaluacion"] == ev]
            if sub.empty:
                continue
            fig.add_trace(go.Bar(
                x=sub["jugador"],
                y=sub["potencia_relativa"],
                name=ev,
                marker_color=EVAL_COLORS.get(ev, "#6B7280"),
                text=sub["potencia_relativa"].round(1),
                textposition="outside",
            ))

        fig.update_layout(
            barmode="stack",
            plot_bgcolor="#111827",
            paper_bgcolor="#111827",
            font=dict(color="#F9FAFB"),
            legend=dict(title="Evaluación", orientation="h", y=-0.25),
            yaxis_title="Potencia relativa (W/kg)",
            xaxis_title="",
            margin=dict(t=10, b=10, l=10, r=10),
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### Detalle del test")
        tabla_s = df_s[[
            "jugador", "altura_cm", "potencia_w",
            "potencia_relativa", "peso_kg", "evaluacion"
        ]].rename(columns={
            "jugador": "Jugador",
            "altura_cm": "Altura (cm)",
            "potencia_w": "Potencia (W)",
            "potencia_relativa": "Pot. Relativa (W/kg)",
            "peso_kg": "Peso (kg)",
            "evaluacion": "Evaluación",
        })
        st.dataframe(
            tabla_s,
            hide_index=True,
            use_container_width=True,
        )

    st.divider()

    # ── Evolución individual ─────────────────────────────────────────────
    st.markdown("##### 📈 Evolución individual")

    jugadores_salto = sorted(saltos["jugador"].unique().tolist())
    jugador_sel = st.selectbox("Seleccioná jugador", jugadores_salto, key="salto_jugador")

    df_j = saltos[saltos["jugador"] == jugador_sel].sort_values("fecha")

    if len(df_j) < 2:
        st.info(f"Todavía hay un solo test cargado para {jugador_sel}. "
                f"La evolución se mostrará cuando haya más de una fecha.")
    else:
        df_j = df_j.copy()
        df_j["Entrenamiento"] = df_j["fecha"].apply(nombre_fecha_salto)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df_j["Entrenamiento"], y=df_j["altura_cm"],
            name="Altura (cm)", mode="lines+markers",
            line=dict(color="#E23E3E", width=3),
        ))
        fig2.add_trace(go.Scatter(
            x=df_j["Entrenamiento"], y=df_j["potencia_relativa"],
            name="Pot. Relativa (W/kg)", mode="lines+markers",
            line=dict(color="#60A5FA", width=3), yaxis="y2",
        ))
        fig2.update_layout(
            plot_bgcolor="#111827",
            paper_bgcolor="#111827",
            font=dict(color="#F9FAFB"),
            yaxis=dict(title="Altura (cm)"),
            yaxis2=dict(title="Pot. Relativa (W/kg)", overlaying="y", side="right"),
            legend=dict(orientation="h", y=-0.25),
            margin=dict(t=10, b=10, l=10, r=10),
            height=380,
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.caption(
        "El test de salto (CMJ) se aplica a todo el plantel disponible en cada "
        "fecha evaluada — a diferencia de la distancia GPS, no está limitado a un Top 3."
    )
