import streamlit as st
import pandas as pd
import numpy as np
import os

from mplsoccer import Pitch
import matplotlib.pyplot as plt

from components.layout import (
    inject_css,
    render_sidebar
)

# ── Configuración de Página ─────────────────────────────────────────
st.set_page_config(
    page_title="Mapa de cancha",
    page_icon="🗺️",
    layout="wide"
)

inject_css()

BASE = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

render_sidebar(BASE)

# ── Rutas de Archivos ──────────────────────────────────────────────
DATA_PATH = os.path.join(BASE, "data", "events_clean.csv")
FIXTURE_PATH = os.path.join(BASE, "data", "fixture.csv")

# ── Carga de Datos ────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    df = pd.read_csv(DATA_PATH)
    
    df["Mins"] = pd.to_numeric(df["Mins"], errors="coerce").fillna(0)
    df["Secs"] = pd.to_numeric(df["Secs"], errors="coerce").fillna(0)
    df["tiempo_total"] = df["Mins"] * 60 + df["Secs"]

    for col in ["X", "Y", "X2", "Y2"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    return df

# ── Validar Existencia de Archivos ─────────────────────────────────
if not os.path.exists(DATA_PATH):
    st.info("No se encontró events_clean.csv")
    st.stop()

if not os.path.exists(FIXTURE_PATH):
    st.info("No se encontró fixture.csv")
    st.stop()

df_original = cargar_datos()
fixture = pd.read_csv(FIXTURE_PATH)

# ── Clasificación Automática de Pases ─────────────────────────────
def clasificar_pases(df):
    df = df.copy()
    df["pase_ok"] = False

    s_continuidad = {
        "pase", "centro", "conduccion", "corner", 
        "remate", "tiro libre", "falta recibida"
    }
    s_corte = {"perdida", "despeje", "recuperacion"}
    tolerancia = 8

    # Usamos un rango basado en la posición física (indexación limpia)
    for i in range(len(df)):
        fila = df.iloc[i]

        if str(fila["Event"]).lower() != "pase":
            continue

        if pd.isna(fila["X2"]) or pd.isna(fila["Y2"]):
            continue

        destino_x = fila["X2"]
        destino_y = fila["Y2"]
        limite = min(i + 5, len(df))

        for j in range(i + 1, limite):
            siguiente = df.iloc[j]

            if pd.isna(siguiente["X"]) or pd.isna(siguiente["Y"]):
                continue

            distancia = np.sqrt(
                (destino_x - siguiente["X"])**2 +
                (destino_y - siguiente["Y"])**2
            )

            if distancia > tolerancia:
                continue

            _sig = str(siguiente["Event"]).lower()

            if evento_sig in eventos_continuidad:
                df.iat[i, df.columns.get_loc("pase_ok")] = True
                break

            if evento_sig in eventos_corte:
                break
                
    return df

# ── Encabezado ────────────────────────────────────────────────────
st.markdown(
    """
    <div style='margin-bottom:28px'>
        <p style='font-size:0.72em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:3px; margin:0 0 6px 0'>
            Análisis Táctico
        </p>
        <h1 style='font-size:2em; font-weight:800; margin:0; color:#EEEEEE; letter-spacing:-0.5px'>
            Mapa de eventos y dinámica de pases
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ── Filtros en UI ─────────────────────────────────────────────────
fechas_disponibles = sorted(df_original["fecha"].unique().tolist())
opciones_fecha = ["Todos los partidos"] + [f"Fecha {f}" for f in fechas_disponibles]

col1, col2, col3 = st.columns(3)

with col1:
    fecha_sel = st.selectbox("Partido", opciones_fecha)

with col2:
    condicion_sel = st.selectbox("Condición", ["Local y Visitante", "Local", "Visitante"])

with col3:
    jugador_sel = st.selectbox(
        "Jugador", 
        ["Todos"] + sorted(df_original["Player"].dropna().unique().tolist())
    )

eventos_disponibles = sorted(df_original["Event"].dropna().unique().tolist())
default_eventos = ["pase"] if "pase" in eventos_disponibles else eventos_disponibles[:1]
eventos_sel = st.multiselect("Eventos", eventos_disponibles, default=default_eventos)

st.divider()

# ── Segmentación Base (Por Fecha / Condición) ──────────────────────
if fecha_sel != "Todos los partidos":
    num_fecha = int(fecha_sel.replace("Fecha ", ""))
    df_base = df_original[df_original["fecha"] == num_fecha].copy()
else:
    df_base = df_original.copy()

if condicion_sel != "Local y Visitante" and fecha_sel == "Todos los partidos":
    fechas_cond = fixture[fixture["condicion"] == condicion_sel]["fecha"].tolist()
    df_base = df_base[df_base["fecha"].isin(fechas_cond)]

# Clasificamos pases sobre la base cronológica antes de romper el df con filtros específicos
df_base = clasificar_pases(df_base)

# ── Filtros Específicos para Mapas Visuales ────────────────────────
df_filtrado = df_base[df_base["Event"].isin(eventos_sel)].copy()

if jugador_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Player"] == jugador_sel]

# ── Configuración de Cancha ───────────────────────────────────────
def crear_cancha():
    pitch = Pitch(
        pitch_type="opta",
        pitch_color="#1B4332",
        line_color="white",
        linewidth=2,
        line_zorder=10,
        corner_arcs=True
    )
    fig, ax = pitch.draw(figsize=(12, 8))
    fig.set_facecolor("#1B4332")
    return pitch, fig, ax

# =============================================================================
# MAPA DE EVENTOS
# =============================================================================
st.subheader("📍 Ubicación de eventos")

if not df_filtrado.empty:
    pitch, fig, ax = crear_cancha()
    
    colores_eventos = {
        "recuperacion": "#34D399", "perdida": "#F87171",
        "conduccion": "#A78BFA", "tiro libre": "#FCD34D",
        "remate": "#FB923C", "despeje": "#9CA3AF",
        "corner": "#F9A8D4", "falta recibida": "#6EE7B7",
        "falta cometida": "#FCA5A5"
    }

    eventos_presentes = df_filtrado["Event"].dropna().unique()

    for evento in eventos_presentes:
        subset = df_filtrado[df_filtrado["Event"] == evento]
        if subset.empty:
            continue

        if evento.lower() == "pase":
            subset_flechas = subset[subset["X2"].notna() & subset["Y2"].notna()].copy()

            # Agrupar por zona de origen y destino (bins de 10x10 sobre cancha 100x100)
            subset_flechas["X_bin"]  = (subset_flechas["X"]  // 10 * 10 + 5).astype(int)
            subset_flechas["Y_bin"]  = (subset_flechas["Y"]  // 10 * 10 + 5).astype(int)
            subset_flechas["X2_bin"] = (subset_flechas["X2"] // 10 * 10 + 5).astype(int)
            subset_flechas["Y2_bin"] = (subset_flechas["Y2"] // 10 * 10 + 5).astype(int)

            # Agrupar pases exitosos
            pases_ok  = subset_flechas[subset_flechas["pase_ok"]]
            pases_bad = subset_flechas[~subset_flechas["pase_ok"]]

            if not pases_ok.empty:
                agrupado_ok = (
                    pases_ok
                    .groupby(["X_bin", "Y_bin", "X2_bin", "Y2_bin"])
                    .size()
                    .reset_index(name="cantidad")
                )
                max_cant = agrupado_ok["cantidad"].max()
                for _, fila in agrupado_ok.iterrows():
                    grosor = 1 + (fila["cantidad"] / max_cant) * 6
                    alpha  = 0.4 + (fila["cantidad"] / max_cant) * 0.5
                    pitch.arrows(
                        fila["X_bin"], fila["Y_bin"],
                        fila["X2_bin"], fila["Y2_bin"],
                        ax=ax, color="#22C55E",
                        width=grosor, alpha=alpha
                )

            if not pases_bad.empty:
                agrupado_bad = (
                    pases_bad
                    .groupby(["X_bin", "Y_bin", "X2_bin", "Y2_bin"])
                    .size()
                    .reset_index(name="cantidad")
            )
            max_cant = agrupado_bad["cantidad"].max()
            for _, fila in agrupado_bad.iterrows():
                grosor = 1 + (fila["cantidad"] / max_cant) * 6
                alpha  = 0.4 + (fila["cantidad"] / max_cant) * 0.5
                pitch.arrows(
                    fila["X_bin"], fila["Y_bin"],
                    fila["X2_bin"], fila["Y2_bin"],
                    ax=ax, color="#EF4444",
                    width=grosor, alpha=alpha
                )
            continue

        if evento.lower() == "centro":
            subset_flechas = subset[subset["X2"].notna() & subset["Y2"].notna()]
            pitch.arrows(subset_flechas["X"], subset_flechas["Y"], subset_flechas["X2"], subset_flechas["Y2"],
                         ax=ax, color="#67E8F9", width=2, alpha=0.9)
            continue

        pitch.scatter(subset["X"], subset["Y"], ax=ax, s=80,
                      color=colores_eventos.get(evento.lower(), "#FFFFFF"),
                      edgecolors="white", linewidth=0.8, alpha=0.9, label=evento)

    ax.legend(loc="upper left", fontsize=8, facecolor="#1B4332", edgecolor="white", labelcolor="white")
    st.pyplot(fig, use_container_width=True)
else:
    st.info("No hay eventos para mostrar.")

# =============================================================================
# MAPA DE CALOR
# =============================================================================
st.divider()
if jugador_sel != "Todos":
    st.subheader(f"🔥 Mapa de calor - {jugador_sel}")
else:
    st.subheader("🔥 Mapa de calor del equipo")

if not df_filtrado.empty:
    pitch, fig, ax = crear_cancha()
    bin_stat = pitch.bin_statistic(df_filtrado["X"], df_filtrado["Y"], statistic="count", bins=(8, 6))
    pitch.heatmap(bin_stat, ax=ax, cmap="Reds", alpha=0.55, zorder=1)
    pitch.draw(ax=ax)
    st.pyplot(fig, use_container_width=True)
else:
    st.info("No hay eventos para generar el mapa de calor.")

# =============================================================================
# RED DE PASES (Lógica Optimizada)
# =============================================================================
def detectar_conexiones_optimizada(df_partido):
    conexiones = []
    # Buscamos de forma posicional indexando sobre las filas reales secuenciales
    df_partido = df_partido.reset_index(drop=True)
    
    pases_idx = df_partido[(df_partido["Event"] == "pase") & (df_partido["pase_ok"] == True)].index

    for idx in pases_idx:
        fila = df_partido.iloc[idx]
        jugador_origen = fila["Player"]
        destino_x = fila["X2"]
        destino_y = fila["Y2"]

        limite = min(idx + 5, len(df_partido))
        siguientes = df_partido.iloc[idx + 1 : limite]

        mejor_jugador = None
        mejor_dist = 999

        for _, sig in siguientes.iterrows():
            if pd.isna(sig["X"]) or pd.isna(sig["Y"]):
                continue

            distancia = np.sqrt((destino_x - sig["X"])**2 + (destino_y - sig["Y"])**2)

            if distancia < mejor_dist:
                mejor_dist = distancia
                mejor_jugador = sig["Player"]

        if mejor_jugador is not None and mejor_jugador != jugador_origen:
            conexiones.append((jugador_origen, mejor_jugador))

    return pd.DataFrame(conexiones, columns=["origen", "destino"])

st.divider()
st.subheader("🕸️ Red de pases")

def obtener_eventos_antes_del_primer_cambio(df_partido):
    # Ordenar cronológicamente de forma estricta
    df_partido = df_partido.sort_values(by=["mitad", "Mins", "Secs"]).reset_index(drop=True)
    
    jugadores_unicos = []
    indice_cambio = len(df_partido)
    
    for idx, fila in df_partido.iterrows():
        jugador = fila["Player"]
        if pd.isna(jugador):
            continue
        
        if jugador not in jugadores_unicos:
            if len(jugadores_unicos) == 11:
                # El jugador número 12 es el que entra (primer cambio)
                indice_cambio = idx
                break
            jugadores_unicos.append(jugador)
            
    df_recortado = df_partido.iloc[:indice_cambio].copy()
    
    info_cambio = None
    if indice_cambio < len(df_partido):
        fila_cambio = df_partido.iloc[indice_cambio]
        info_cambio = {
            "jugador_entra": fila_cambio["Player"],
            "minuto": int(fila_cambio["Mins"]),
            "segundo": int(fila_cambio["Secs"]),
            "mitad": int(fila_cambio["mitad"])
        }
        
    return df_recortado, jugadores_unicos, info_cambio

if not df_base.empty:
    # Si se seleccionó un partido específico, mostramos solo los titulares hasta el primer cambio
    if fecha_sel != "Todos los partidos":
        df_red, titulares, info_cambio = obtener_eventos_antes_del_primer_cambio(df_base)
        if info_cambio:
            st.info(f"💡 Red de pases calculada con los **11 titulares** hasta el primer cambio (Entra **{info_cambio['jugador_entra']}** al min {info_cambio['minuto']}:{info_cambio['segundo']} - Mitad {info_cambio['mitad']}).")
        else:
            st.info("💡 Red de pases calculada con los **11 titulares** (no se registraron cambios).")
    else:
        df_red = df_base.copy()
        st.warning("⚠️ Al mostrar 'Todos los partidos', la red de pases incluye a todos los jugadores que participaron en el conjunto de partidos.")

    conexiones = detectar_conexiones_optimizada(df_red)

    if conexiones.empty:
        st.info("No se detectaron conexiones de pase.")
    else:
        pitch, fig, ax = crear_cancha()

        # Posición promedio basada estrictamente en los pases hechos para mayor precisión táctica
        pases_validos = df_red[df_red["Event"] == "pase"]
        posiciones = pases_validos.groupby("Player").agg({"X": "mean", "Y": "mean"}).reset_index()

        conexiones_count = conexiones.groupby(["origen", "destino"]).size().reset_index(name="cantidad")

        # Dibujar líneas
        for _, fila in conexiones_count.iterrows():
            origen, destino, cantidad = fila["origen"], fila["destino"], fila["cantidad"]

            pos_origen = posiciones[posiciones["Player"] == origen]
            pos_destino = posiciones[posiciones["Player"] == destino]

            if pos_origen.empty or pos_destino.empty:
                continue

            x1, y1 = pos_origen["X"].iloc[0], pos_origen["Y"].iloc[0]
            x2, y2 = pos_destino["X"].iloc[0], pos_destino["Y"].iloc[0]

            pitch.lines(x1, y1, x2, y2, ax=ax, lw=max(1, cantidad * 1.5), color="#4ADE80", alpha=0.75, zorder=2)

        # Dibujar nodos
        pitch.scatter(posiciones["X"], posiciones["Y"], ax=ax, s=600, color="#2563EB", edgecolors="white", linewidth=2, zorder=3)

        # Etiquetas de texto
        for _, fila in posiciones.iterrows():
            ax.text(fila["X"], fila["Y"], fila["Player"], color="white", fontsize=8,
                    ha="center", va="center", weight="bold", zorder=4)

        st.pyplot(fig, use_container_width=True)
else:
    st.info("No hay datos suficientes para estructurar la red de pases.")
