import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import date

from components.layout import (
    inject_css,
    render_sidebar,
    render_header
)

inject_css()

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOTOS_DIR = os.path.join(BASE, "static", "fotos")
DATA_PATH = os.path.join(BASE, "data", "events_clean.csv")

render_sidebar(BASE)

render_header(
    "Plantel",
    "Plantilla"
)

@st.cache_data(ttl=0)
def cargar_jugadores():
    df = pd.read_csv(os.path.join(BASE, "data", "Jugadores.csv"))
    df["nombre"] = df["nombre"].str.strip().str.title()
    df["posicion"] = df["posicion"].str.strip().str.title()
    return df

@st.cache_data(ttl=0)
def cargar_alertas():
    df = pd.read_csv(os.path.join(BASE, "data", "sanciones_lesiones.csv"))
    if not df.empty:
        df["fecha_regreso"] = pd.to_datetime(df["fecha_regreso"], dayfirst=True, errors="coerce")
    return df

@st.cache_data
def cargar_eventos():
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame()
    return pd.read_csv(DATA_PATH)

def estado_jugador(nombre, alertas):
    hoy = pd.Timestamp(date.today())
    if alertas.empty:
        return "✅", "Disponible"
    fila = alertas[alertas["nombre"].str.lower() == nombre.lower()]
    if fila.empty:
        return "✅", "Disponible"
    for _, row in fila.iterrows():
        tipo = str(row["tipo"]).lower()
        regreso = row.get("fecha_regreso", None)
        activo = pd.isna(regreso) or regreso >= hoy
        if not activo:
            continue
        if tipo in ["lesión", "lesion"]:
            return "🤕", "Lesionado"
        if tipo in ["sanción", "sancion", "roja directa"]:
            return "🟥", "Sancionado"
    # Verificar riesgo por amarillas
    amarillas = fila[fila["tipo"].str.lower() == "amarilla"]
    if len(amarillas) >= 4:
        return "🟨", "En riesgo"
    return "✅", "Disponible"

def stats_jugador(nombre, eventos):
    if eventos.empty:
        return {"partidos": 0, "minutos": 0, "pases": 0, "recuperaciones": 0,
                "conducciones": 0, "despejes": 0, "faltas": 0, "remates": 0}
    j = eventos[eventos["Player"].str.lower() == nombre.lower()]
    if j.empty:
        return {"partidos": 0, "minutos": 0, "pases": 0, "recuperaciones": 0,
                "conducciones": 0, "despejes": 0, "faltas": 0, "remates": 0}
    partidos = j["fecha"].nunique()
    minutos = int(j.groupby("fecha")["Mins"].max().sum() - j.groupby("fecha")["Mins"].min().sum())
    return {
        "partidos": partidos,
        "minutos": minutos,
        "pases": len(j[j["Event"] == "pase"]),
        "recuperaciones": len(j[j["Event"] == "recuperacion"]),
        "conducciones": len(j[j["Event"] == "conduccion"]),
        "despejes": len(j[j["Event"] == "despeje"]),
        "faltas": len(j[j["Event"] == "falta cometida"]),
        "remates": len(j[j["Event"] == "remate"]),
    }

jugadores = cargar_jugadores()
alertas = cargar_alertas()
eventos = cargar_eventos()

# --- Tabs ---
tab1, tab2 = st.tabs(["📋 Plantel", "⚖️ Comparar jugadores"])

with tab1:
    posiciones = ["Todas"] + sorted(jugadores["posicion"].unique().tolist())
    pos_sel = st.selectbox("Filtrar por posición", posiciones)
    df_filtrado = jugadores if pos_sel == "Todas" else jugadores[jugadores["posicion"] == pos_sel]

    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total jugadores", len(jugadores))
    col2.metric("Arqueros", len(jugadores[jugadores["posicion"].str.lower() == "arquero"]))
    col3.metric("Defensores", len(jugadores[jugadores["posicion"].str.lower() == "defensor"]))
    col4.metric("Mediocampistas + Delanteros",
                len(jugadores[jugadores["posicion"].str.lower().isin(["mediocampista", "delantero"])]))

    st.divider()

    COLS = 4
    lista = df_filtrado.reset_index(drop=True)
    for i in range(0, len(lista), COLS):
        cols = st.columns(COLS)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(lista):
                break
            row = lista.iloc[idx]
            foto_path = os.path.join(FOTOS_DIR, str(row["fotos"]))
            icono, estado_txt = estado_jugador(row["nombre"], alertas)
            stats = stats_jugador(row["nombre"], eventos)

            with col:
                if os.path.exists(foto_path):
                    st.image(foto_path, use_container_width=True)
                else:
                    fallback = os.path.join(FOTOS_DIR, "sin_perfil.jpg")
                    if os.path.exists(fallback):
                        st.image(fallback, use_container_width=True)

                st.markdown(f"""
                <div style='text-align:center; padding: 4px 0'>
                    <span style='font-size:1.3em; font-weight:700'>#{int(row['camiseta'])} {row['nombre']}</span><br>
                    <span style='font-size:0.85em; color:#9CA3AF'>{row['posicion']}</span><br>
                    <span style='font-size:1em'>{icono} {estado_txt}</span><br>
                    <span style='font-size:0.8em; color:#D1D5DB'>
                        🎮 {stats['partidos']} partidos &nbsp;|&nbsp; ⏱️ {stats['minutos']} min<br>
                        ⚽ {stats['pases']} pases &nbsp;|&nbsp; 💪 {stats['recuperaciones']} recup.<br>
                        🎯 {stats['remates']} remates
                    </span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("---")

with tab2:
    st.subheader("⚖️ Comparador de jugadores")

    nombres = sorted(jugadores["nombre"].tolist())
    seleccionados = st.multiselect("Elegí los jugadores a comparar (mínimo 2)", nombres, max_selections=5)

    if len(seleccionados) < 2:
        st.info("Seleccioná al menos 2 jugadores para comparar.")
    else:
        METRICAS = ["pases", "recuperaciones", "conducciones", "despejes", "faltas", "remates"]
        LABELS   = ["Pases", "Recuperaciones", "Conducciones", "Despejes", "Faltas", "Remates"]

        # Tabla comparativa
        st.divider()
        filas = []
        stats_todos = {}
        for nombre in seleccionados:
            s = stats_jugador(nombre, eventos)
            stats_todos[nombre] = s
            filas.append({
                "Jugador": nombre,
                "Partidos": s["partidos"],
                "Minutos": s["minutos"],
                "Pases": s["pases"],
                "Recuperaciones": s["recuperaciones"],
                "Conducciones": s["conducciones"],
                "Despejes": s["despejes"],
                "Faltas": s["faltas"],
                "Remates": s["remates"],
            })

        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

        st.divider()

        # Radar chart
        st.subheader("Radar de rendimiento")
        fig = go.Figure()
        colores_radar = [
            "#E23E3E",
            "#60A5FA",
            "#34D399",
            "#FBBF24",
            "#A78BFA"
        ]

        for idx, nombre in enumerate(seleccionados):
            s = stats_todos[nombre]
            valores = [s[m] for m in METRICAS]
            valores += [valores[0]]  # cerrar el polígono
            fig.add_trace(go.Scatterpolar(
                r=valores,
                theta=LABELS + [LABELS[0]],
                fill="toself",
                name=nombre,
                line=dict(color=colores_radar[idx % len(colores_radar)]),
                opacity=0.6,
            ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, showticklabels=True)),
            showlegend=True,
            height=500,
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
