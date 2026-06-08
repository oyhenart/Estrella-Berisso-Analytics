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
    
    # Estandarización preventiva de columnas clave para evitar rupturas de código
    if "Resultado" not in df.columns:
        df["Resultado"] = 1 # Si no tenés la columna, por defecto asume completado
    if "Receptor" not in df.columns:
        df["Receptor"] = "Desconocido"
        
    # Armar dataframe específico de pases con coordenadas de destino
    pases = df[df["Event"] == "pase"].copy()
    pases = pases.rename(columns={
        "Player": "jugador_origen", "X": "x_origen", "Y": "y_origen",
        "X2": "x_destino", "Y2": "y_destino", "Mins": "mins", "Secs": "secs",
        "Receptor": "jugador_destino", "Resultado": "resultado"
    })
    df_pases = pases[["jugador_origen","jugador_destino","x_origen","y_origen","x_destino","y_destino","mins","secs","fecha","resultado"]].dropna(subset=["x_destino","y_destino"])
    return df, df_pases

# ── Encabezado Personalizado ───────────────────────────────────────────────────
st.markdown("""
<div style='margin-bottom:28px'>
    <p style='font-size:0.72em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:3px; margin:0 0 6px 0'>Análisis Táctico</p>
    <h1 style='font-size:2em; font-weight:800; margin:0; color:#EEEEEE; letter-spacing:-0.5px'>Mapa de eventos y dinámica de pases</h1>
</div>
""", unsafe_allow_html=True)

if not os.path.exists(DATA_PATH) or not os.path.exists(FIXTURE_PATH):
    st.info("⏳ El torneo aún no comenzó o faltan archivos de datos. El mapa estará disponible a partir del primer partido.")
    st.stop()

df, df_pases = cargar_datos()
fixture = pd.read_csv(FIXTURE_PATH)

# Dimensiones reglamentarias de referencia (StatsBomb / Porcentual)
W, H = 100, 100
AG_X = 12.7; AG_Y = 44.8
AC_X = 4.2;  AC_Y = 20.4
ARCO = 8.1;  CR   = 7.0

# Gama cromática para eventos generales y discriminación de pases
colores = {
    "pase_correcto":  "#22C55E", # Verde estallado
    "pase_incorrecto":"#EF4444", # Rojo alerta
    "recuperacion":   "#34D399",
    "perdida":        "#F87171",
    "conduccion":     "#A78BFA",
    "tiro libre":     "#FCD34D",
    "remate":         "#FB923C",
    "centro":         "#67E8F9",
    "gol":            "#E23E3E",
    "despeje":        "#9CA3AF",
    "corner":         "#F9A8D4",
    "falta recibida": "#6EE7B7",
    "falta cometida": "#FCA5A5",
}

# ── Filtros de la Aplicación ───────────────────────────────────────────────────
fechas_disponibles = sorted(df["fecha"].unique().tolist())
opciones_fecha     = ["Todos los partidos"] + [f"Fecha {f}" for f in fechas_disponibles]

col1, col2, col3 = st.columns(3)
with col1:
    fecha_sel = st.selectbox("Partido", opciones_fecha)
with col2:
    condicion_sel = st.selectbox("Condición", ["Local y Visitante", "Local", "Visitante"])
with col3:
    jugadores   = ["Todos"] + sorted(df["Player"].unique().tolist())
    jugador_sel = st.selectbox("Jugador", jugadores)

eventos_disponibles = sorted(df["Event"].unique().tolist())
default_eventos     = ["pase"] if "pase" in eventos_disponibles else eventos_disponibles[:1]
eventos_sel = st.multiselect("Tipo de evento a visualizar", eventos_disponibles, default=default_eventos)

st.divider()

# ── Lógica de Filtrado de Datos ────────────────────────────────────────────────
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

# El dataframe general se filtra por la selección múltiple de eventos
df_filtrado = df_filtrado[df_filtrado["Event"].isin(eventos_sel)]

if jugador_sel != "Todos":
    df_filtrado  = df_filtrado[df_filtrado["Player"] == jugador_sel]
    df_pases_f   = df_pases_f[df_pases_f["jugador_origen"] == jugador_sel]

# ── Funciones de Diseño de la Cancha ───────────────────────────────────────────
def shapes_cancha():
    s = []
    def rect(x0, y0, x1, y1, fill="#1B4332", lw=1.5):
        return dict(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                    fillcolor=fill, line=dict(color="white", width=lw), layer="below")
    def line(x0, y0, x1, y1, lw=1.5):
        return dict(type="line", x0=x0, y0=y0, x1=x1, y1=y1,
                    line=dict(color="white", width=lw), layer="below")
    def circle(x0, y0, x1, y1):
        return dict(type="circle", x0=x0, y0=y0, x1=x1, y1=y1,
                    line=dict(color="white", width=1.5), fillcolor="rgba(0,0,0,0)", layer="below")
    
    s.append(rect(0, 0, W, H, lw=2))
    s.append(line(W/2, 0, W/2, H))
    s.append(circle(W/2-CR, H/2-CR, W/2+CR, H/2+CR))
    s.append(rect(0, (H-AG_Y)/2, AG_X, (H+AG_Y)/2))
    s.append(rect(0, (H-AC_Y)/2, AC_X, (H+AC_Y)/2))
    s.append(line(0, (H-ARCO)/2, 0, (H+ARCO)/2, lw=4))
    s.append(rect(W-AG_X, (H-AG_Y)/2, W, (H+AG_Y)/2))
    s.append(rect(W-AC_X, (H-AC_Y)/2, W, (H+AC_Y)/2))
    s.append(line(W, (H-ARCO)/2, W, (H+ARCO)/2, lw=4))
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

# ── GRÁFICO 1: MAPA GENERAL DE EVENTOS (CON MULTISELECT REPARADO) ──────────────
st.subheader("Ubicación de eventos en campo de juego")

fig = go.Figure()

# 1. Si "pase" está seleccionado, vectorizamos las trayectorias dirigidas
if "pase" in eventos_sel and not df_pases_f.empty:
    correctos = df_pases_f[df_pases_f["resultado"] == 1]
    incorrectos = df_pases_f[df_pases_f["resultado"] == 0]
    
    def graficar_lineas_y_conos(df_sub, color, nombre):
        if df_sub.empty: return
        # Trazado de líneas limpias
        x_lines, y_lines = [], []
        for _, row in df_sub.iterrows():
            x_lines.extend([row["x_origen"], row["x_destino"], None])
            y_lines.extend([row["y_origen"], row["y_destino"], None])
            
        fig.add_trace(go.Scatter(
            x=x_lines, y=y_lines, mode="lines",
            line=dict(color=color, width=1.5), name=nombre, legendgroup=nombre
        ))
        
        # Puntas de flecha orientadas con go.Cone
        x_dest, y_dest = df_sub["x_destino"].tolist(), df_sub["y_destino"].tolist()
        u_dir = (df_sub["x_destino"] - df_sub["x_origen"]).tolist()
        v_dir = (df_sub["y_destino"] - df_sub["y_origen"]).tolist()
        
        # Normalización manual de vectores para evitar deformaciones ópticas
        for i in range(len(u_dir)):
            norm = np.sqrt(u_dir[i]**2 + v_dir[i]**2)
            if norm > 0:
                u_dir[i] /= norm
                v_dir[i] /= norm

        fig.add_trace(go.Cone(
            x=x_dest, y=y_dest, z=[0]*len(x_dest),
            u=u_dir, v=v_dir, w=[0]*len(x_dest),
            colorscale=[[0, color], [1, color]], showscale=False,
            sizemode="absolute", sizeref=2.5,
            legendgroup=nombre, showlegend=False,
            text=df_sub["jugador_origen"],
            hovertemplate="Pase de: %{text}<extra></extra>"
        ))

    graficar_lineas_y_conos(correctos, colores["pase_correcto"], "Pase Completado")
    graficar_lineas_y_conos(incorrectos, colores["pase_incorrecto"], "Pase Errado")

# 2. Representación de todos los demás eventos del multiselect como puntos claros
for evento in eventos_sel:
    if evento == "pase":
        continue # Nos saltamos el pase común porque ya lo vectorizamos arriba de forma avanzada
        
    subset = df_filtrado[df_filtrado["Event"] == evento]
    if subset.empty:
        continue
        
    fig.add_trace(go.Scatter(
        x=subset["X"], y=subset["Y"],
        mode="markers", name=evento,
        marker=dict(
            color=colores.get(evento, "#ffffff"),
            size=10, opacity=0.9,
            line=dict(color="white", width=1)
        ),
        customdata=subset[["Player", "Mins", "Secs"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Evento: " + evento + "<br>"
            "Tiempo: %{customdata[1]:.0f}:%{customdata[2]:.0f}<br><extra></extra>"
        ),
    ))

fig.update_layout(**layout_cancha(600))
st.plotly_chart(fig, use_container_width=True)


# ── GRÁFICO 2: RED DE PASES COLECTIVA (ESTRUCTURAL) ───────────────────────────
st.divider()
st.subheader("Estructura de la Red de Pases Colectiva")

if fecha_sel == "Todos los partidos":
    st.info("💡 Consejo táctico: Elegí una Fecha puntual en los filtros superiores para examinar la red de pases exacta de una alineación.")

df_red = df_pases_f[df_pases_f["resultado"] == 1].copy()

if len(df_red) > 5:
    pos_media = df_red.groupby("jugador_origen")[["x_origen", "y_origen"]].mean().reset_index()
    cant_pases = df_red.groupby("jugador_origen").size().reset_index(name="cantidad")
    pos_media = pos_media.merge(cant_pases, on="jugador_origen")
    
    conexiones = df_red.groupby(["jugador_origen", "jugador_destino"]).size().reset_index(name="frecuencia")
    conexiones = conexiones[conexiones["frecuencia"] >= 2] # Filtro de frecuencia para evitar contaminación visual

    fig_red = go.Figure()

    for _, fila in conexiones.iterrows():
        orig = pos_media[pos_media["jugador_origen"] == fila["jugador_origen"]]
        dest = pos_media[pos_media["jugador_origen"] == fila["jugador_destino"]]
        if not orig.empty and not dest.empty:
            fig_red.add_trace(go.Scatter(
                x=[orig["x_origen"].values[0], dest["x_origen"].values[0]],
                y=[orig["y_origen"].values[0], dest["y_origen"].values[0]],
                mode="lines",
                line=dict(color="rgba(252, 211, 77, 0.45)", width=fila["frecuencia"] * 1.3),
                hoverinfo="skip", showlegend=False
            ))

    fig_red.add_trace(go.Scatter(
        x=pos_media["x_origen"], y=pos_media["y_origen"],
        mode="markers+text",
        marker=dict(color="white", size=pos_media["cantidad"] * 0.5 + 12, line=dict(color="#1B4332", width=2)),
        text=pos_media["jugador_origen"], textposition="top center",
        textfont=dict(color="white", size=10, family="Arial Black"),
        name="Posición Media"
    ))
    fig_red.update_layout(**layout_cancha(600))
    st.plotly_chart(fig_red, use_container_width=True)
else:
    st.info("No hay suficiente volumen de pases completados con receptor identificado para trazar el mapa de red estructural.")


# ── GRÁFICO 3: HEATMAP DE ACTIVIDAD ───────────────────────────────────────────
st.divider()
st.subheader("Zonas de mayor densidad de acciones")

if not df_filtrado.empty:
    nx, ny = 13, 9
    grid = np.zeros((ny, nx))
    for _, row in df_filtrado.iterrows():
        xi = min(int(row["X"] / W * nx), nx - 1)
        yi = min(int(row["Y"] / H * ny), ny - 1)
        grid[yi, xi] += 1

    fig2 = go.Figure(data=go.Heatmap(
        z=grid, x=np.linspace(0, W, nx), y=np.linspace(0, H, ny),
        colorscale=[
            [0.00, "rgba(0,0,0,0)"],
            [0.01, "rgba(255,255,0,0.4)"],
            [0.50, "rgba(255,140,0,0.6)"],
            [1.00, "rgba(200,0,0,0.85)"],
        ],
        showscale=False, xgap=1, ygap=1,
        hovertemplate="Acciones en zona: %{z}<extra></extra>"
    ))
    layout2 = layout_cancha(500)
    layout2.pop("legend", None)
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Seleccioná al menos un tipo de evento en el filtro para generar el mapa de calor.")
