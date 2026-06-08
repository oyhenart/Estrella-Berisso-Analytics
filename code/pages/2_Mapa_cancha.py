import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

from components.layout import (
    inject_css,
    render_sidebar
)

# ── Configuración de Página ───────────────────────────────────────────────────
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

# ── Rutas de Archivos ──────────────────────────────────────────────────────────
DATA_PATH = os.path.join(BASE, "data", "events_clean.csv")
FIXTURE_PATH = os.path.join(BASE, "data", "fixture.csv")

# ── Carga de Datos con Caché ───────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    df = pd.read_csv(DATA_PATH)
    df["tiempo_total"] = df["Mins"] * 60 + df["Secs"]
    
    # Nota: Se asume la columna 'Resultado' (1: completado, 0: incompleto)
    # Si no existe en tu csv, creamos una por defecto para que no rompa
    if "Resultado" not in df.columns:
        df["Resultado"] = 1 
    if "Receptor" not in df.columns:
        df["Receptor"] = "Desconocido"

    pases = df[df["Event"] == "pase"].copy()
    pases = pases.rename(columns={
        "Player": "jugador_origen", "X": "x_origen", "Y": "y_origen",
        "X2": "x_destino", "Y2": "y_destino", "Mins": "mins", "Secs": "secs",
        "Receptor": "jugador_destino", "Resultado": "resultado"
    })
    df_pases = pases[["jugador_origen","jugador_destino","x_origen","y_origen","x_destino","y_destino","mins","secs","fecha","resultado"]].dropna(subset=["x_destino","y_destino"])
    return df, df_pases

# ── Encabezado ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style='margin-bottom:28px'>
    <p style='font-size:0.72em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:3px; margin:0 0 6px 0'>Análisis Avanzado</p>
    <h1 style='font-size:2em; font-weight:800; margin:0; color:#EEEEEE; letter-spacing:-0.5px'>Estructura de Pases y Eventos</h1>
</div>
""", unsafe_allow_html=True)

if not os.path.exists(DATA_PATH) or not os.path.exists(FIXTURE_PATH):
    st.info("⏳ Archivos de datos no encontrados.")
    st.stop()

df, df_pases = cargar_datos()
fixture = pd.read_csv(FIXTURE_PATH)

W, H = 100, 100
AG_X = 12.7; AG_Y = 44.8
AC_X = 4.2;  AC_Y = 20.4
ARCO = 8.1;  CR   = 7.0

colores = {
    "pase_correcto":  "#22C55E", # Verde
    "pase_incorrecto":"#EF4444", # Rojo
    "recuperacion":   "#34D399",
    "perdida":        "#F87171",
    "conduccion":     "#A78BFA",
    "remate":         "#FB923C",
    "despeje":        "#9CA3AF",
}

# ── Filtros ───────────────────────────────────────────────────────────────────
fechas_disponibles = sorted(df["fecha"].unique().tolist())
opciones_fecha     = ["Todos los partidos"] + [f"Fecha {f}" for f in fechas_disponibles]

col1, col2, col3 = st.columns(3)
with col1:
    fecha_sel = st.selectbox("Partido / Fecha", opciones_fecha)
with col2:
    condicion_sel = st.selectbox("Condición", ["Local y Visitante", "Local", "Visitante"])
with col3:
    jugadores   = ["Todos"] + sorted(df["Player"].unique().tolist())
    jugador_sel = st.selectbox("Jugador Específico", jugadores)

# ── Lógica de Filtrado Base ───────────────────────────────────────────────────
if fecha_sel != "Todos los partidos":
    num_fecha   = int(fecha_sel.replace("Fecha ", ""))
    df_filtrado = df[df["fecha"] == num_fecha]
    df_pases_f  = df_pases[df_pases["fecha"] == num_fecha]
else:
    num_fecha   = None
    df_filtrado = df.copy()
    df_pases_f  = df_pases.copy()

if condicion_sel != "Local y Visitante" and num_fecha is None:
    fechas_cond = fixture[fixture["condicion"] == condicion_sel]["fecha"].tolist()
    df_filtrado = df_filtrado[df_filtrado["fecha"].isin(fechas_cond)]
    df_pases_f  = df_pases_f[df_pases_f["fecha"].isin(fechas_cond)]

# ── Dimensiones de Cancha Layout Plotly ────────────────────────────────────────
def shapes_cancha():
    s = []
    def rect(x0, y0, x1, y1, fill="#1B4332", lw=1.5): # Un verde un poco más oscuro para contrastar flechas
        return dict(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                    fillcolor=fill, line=dict(color="rgba(255,255,255,0.6)", width=lw), layer="below")
    def line(x0, y0, x1, y1, lw=1.5):
        return dict(type="line", x0=x0, y0=y0, x1=x1, y1=y1,
                    line=dict(color="rgba(255,255,255,0.6)", width=lw), layer="below")
    def circle(x0, y0, x1, y1):
        return dict(type="circle", x0=x0, y0=y0, x1=x1, y1=y1,
                    line=dict(color="rgba(255,255,255,0.6)", width=1.5), fillcolor="rgba(0,0,0,0)", layer="below")
    
    s.append(rect(0, 0, W, H, lw=2))
    s.append(line(W/2, 0, W/2, H))
    s.append(circle(W/2-CR, H/2-CR, W/2+CR, H/2+CR))
    s.append(rect(0, (H-AG_Y)/2, AG_X, (H+AG_Y)/2))
    s.append(rect(0, (H-AC_Y)/2, AC_X, (H+AC_Y)/2))
    s.append(rect(W-AG_X, (H-AG_Y)/2, W, (H+AG_Y)/2))
    s.append(rect(W-AC_X, (H-AC_Y)/2, W, (H+AC_Y)/2))
    return s

def layout_cancha(height=600):
    return dict(
        height=height, margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#1B4332",
        xaxis=dict(range=[-2, W+2], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[H+2, -2], showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=0.69),
        shapes=shapes_cancha(),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color="white")),
    )

# ── VISTA 1: RED DE PASES COLECTIVA (Imagen image_89900a.png) ─────────────────
st.subheader("Red de Pases Colectiva")
st.caption("Muestra la posición media de los jugadores y la frecuencia de pases entre ellos (mínimo 2 pases).")

if fecha_sel == "Todos los partidos":
    st.warning("⚠️ Para una Red de Pases precisa, se recomienda filtrar por una 'Fecha' específica para no mezclar alineaciones.")

# Filtrar solo pases correctos para la red estructural de juego
df_red = df_pases_f[df_pases_f["resultado"] == 1].copy()

if len(df_red) > 5:
    # 1. Calcular posición promedio (puntos de origen)
    pos_media = df_red.groupby("jugador_origen")[["x_origen", "y_origen"]].mean().reset_index()
    # 2. Calcular volumen de pases individuales por jugador (Tamaño del nodo)
    cant_pases = df_red.groupby("jugador_origen").size().reset_index(name="cantidad")
    pos_media = pos_media.merge(cant_pases, on="jugador_origen")
    
    # 3. Calcular conexiones entre parejas de jugadores
    conexiones = df_red.groupby(["jugador_origen", "jugador_destino"]).size().reset_index(name="frecuencia")
    conexiones = conexiones[conexiones["frecuencia"] >= 2] # Umbral mínimo para limpiar ruido táctico

    fig_red = go.Figure()

    # Dibujar líneas de conexión
    for _, fila in conexiones.iterrows():
        orig = pos_media[pos_media["jugador_origen"] == fila["jugador_origen"]]
        dest = pos_media[pos_media["jugador_origen"] == fila["jugador_destino"]]
        
        if not orig.empty and not dest.empty:
            x0, y0 = orig["x_origen"].values[0], orig["y_origen"].values[0]
            x1, y1 = dest["x_origen"].values[0], dest["y_origen"].values[0]
            
            fig_red.add_trace(go.Scatter(
                x=[x0, x1], y=[y0, y1],
                mode="lines",
                line=dict(color="rgba(24CD, 211, 77, 0.5)", width=fila["frecuencia"] * 1.2), # Grosor según volumen
                hoverinfo="skip", showlegend=False
            ))

    # Dibujar los Nodos (Jugadores)
    fig_red.add_trace(go.Scatter(
        x=pos_media["x_origen"], y=pos_media["y_origen"],
        mode="markers+text",
        marker=dict(color="white", size=pos_media["cantidad"] * 0.6 + 12, line=dict(color="#1B4332", width=2)),
        text=pos_media["jugador_origen"],
        textposition="top center",
        textfont=dict(color="white", size=11, family="Arial Black"),
        hovertemplate="<b>%{text}</b><br>Pases dados: %{marker.size}<extra></extra>",
        name="Jugadores"
    ))

    fig_red.update_layout(**layout_cancha(650))
    st.plotly_chart(fig_red, use_container_width=True)
else:
    st.info("Faltan datos de pases e identificación de receptores en este set para armar la red estructural.")


# ── VISTA 2: MAPA DE DIRECCIÓN Y EFECTIVIDAD (Imagen image_899005.jpg) ─────────
st.divider()
st.subheader("Dirección y Efectividad de Pases")

# Filtrado por jugador si se requiere
if jugador_sel != "Todos":
    df_pases_mapa = df_pases_f[df_pases_f["jugador_origen"] == jugador_sel]
else:
    df_pases_mapa = df_pases_f.copy()

fig_mapa = go.Figure()

# Separar pases correctos e incorrectos
correctos = df_pases_mapa[df_pases_mapa["resultado"] == 1]
incorrectos = df_pases_mapa[df_pases_mapa["resultado"] == 0]

# Función auxiliar para graficar vectores con flechas simuladas en Plotly
def agregar_vectores_pases(fig, df_pms, color, nombre, visible):
    if df_pms.empty: return
    
    # Líneas de trayecto
    x_lines, y_lines = [], []
    for _, row in df_pms.iterrows():
        x_lines.extend([row["x_origen"], row["x_destino"], None])
        y_lines.extend([row["y_origen"], row["y_destino"], None])
        
    fig.add_trace(go.Scatter(
        x=x_lines, y=y_lines, mode="lines",
        line=dict(color=color, width=2), name=nombre,
        legendgroup=nombre
    ))
    
    # Puntos de destino (actúan como la punta del pase)
    fig.add_trace(go.Scatter(
        x=df_pms["x_destino"], y=df_pms["y_destino"], mode="markers",
        marker=dict(color=color, size=6, symbol="triangle-up" if color=="#22C55E" else "x"),
        showlegend=False, legendgroup=nombre,
        text=df_pms["jugador_origen"],
        hovertemplate="Pase de: %{text}<extra></extra>"
    ))

agregar_vectores_pases(fig_mapa, correctos, colores["pase_correcto"], "Pases Completos (Verde)", True)
agregar_vectores_pases(fig_mapa, incorrectos, colores["pase_incorrecto"], "Pases Incompletos (Rojo)", True)

fig_mapa.update_layout(**layout_cancha(600))
st.plotly_chart(fig_mapa, use_container_width=True)


# ── VISTA 3: MAPA DE CALOR TRADICIONAL ─────────────────────────────────────────
st.divider()
# ... (Se conserva intacto tu código del mapa de calor inferior)
st.subheader("Zonas de mayor actividad general")
eventos_totales = df_filtrado[df_filtrado["Event"].isin(st.multiselect("Filtrar Heatmap por evento", df["Event"].unique().tolist(), default=["pase"]))]
if not eventos_totales.empty:
    nx, ny = 13, 9
    grid = np.zeros((ny, nx))
    for _, row in eventos_totales.iterrows():
        xi = min(int(row["X"] / W * nx), nx - 1)
        yi = min(int(row["Y"] / H * ny), ny - 1)
        grid[yi, xi] += 1
    fig2 = go.Figure(data=go.Heatmap(
        z=grid, x=np.linspace(0, W, nx), y=np.linspace(0, H, ny),
        colorscale=[[0, "rgba(0,0,0,0)"], [0.1, "rgba(255,255,0,0.4)"], [1, "rgba(200,0,0,0.8)"]],
        showscale=False, xgap=1, ygap=1
    ))
    fig2.update_layout(**layout_cancha(500))
    st.plotly_chart(fig2, use_container_width=True)
