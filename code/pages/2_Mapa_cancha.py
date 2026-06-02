import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Mapa de cancha", page_icon="🗺️", layout="wide")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE, "data", "events_clean.csv")

@st.cache_data
def cargar_datos():
    df = pd.read_csv(DATA_PATH)
    df["tiempo_total"] = df["Mins"] * 60 + df["Secs"]
    # Armar df_pases desde X2/Y2 del nuevo formato
    pases = df[df["Event"] == "pase"].copy()
    pases = pases.rename(columns={
        "Player": "jugador_origen", "X": "x_origen", "Y": "y_origen",
        "X2": "x_destino", "Y2": "y_destino", "Mins": "mins", "Secs": "secs"
    })
    df_pases = pases[["jugador_origen","x_origen","y_origen","x_destino","y_destino","mins","secs"]].dropna(subset=["x_destino","y_destino"])
    return df, df_pases

st.title("🗺️ Mapa de eventos en cancha")

if not os.path.exists(DATA_PATH):
    st.info("⏳ El torneo aún no comenzó. El mapa estará disponible a partir del primer partido.")
    st.stop()

df, df_pases = cargar_datos()

W, H = 100, 100
AG_X = 12.7; AG_Y = 44.8
AC_X = 4.2;  AC_Y = 20.4
ARCO = 8.1;  CR   = 7.0

# Colores en minúsculas
colores = {
    "pase": "#3498db", "recuperacion": "#2ecc71", "perdida": "#e74c3c",
    "conduccion": "#9b59b6", "tiro libre": "#f1c40f",
    "remate": "#e74c3c", "centro": "#1abc9c", "gol": "#ff0000",
    "despeje": "#95a5a6", "corner": "#e67e22",
    "falta recibida": "#00bcd4", "falta cometida": "#ff5722",
}

col1, col2 = st.columns(2)
with col1:
    jugadores = ["Todos"] + sorted(df["Player"].unique().tolist())
    jugador_sel = st.selectbox("Jugador", jugadores)
with col2:
    eventos_disponibles = sorted(df["Event"].unique().tolist())
    eventos_sel = st.multiselect("Tipo de evento", eventos_disponibles, default=eventos_disponibles)

st.divider()

df_filtrado = df[df["Event"].isin(eventos_sel)]
if jugador_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Player"] == jugador_sel]
    df_pases_f = df_pases[df_pases["jugador_origen"] == jugador_sel]
else:
    df_pases_f = df_pases

def shapes_cancha():
    s = []
    def rect(x0, y0, x1, y1, fill="#4a7c3f", lw=1.5):
        return dict(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                    fillcolor=fill, line=dict(color="white", width=lw), layer="below")
    def line(x0, y0, x1, y1, lw=1.5):
        return dict(type="line", x0=x0, y0=y0, x1=x1, y1=y1,
                    line=dict(color="white", width=lw), layer="below")
    def circle(x0, y0, x1, y1):
        return dict(type="circle", x0=x0, y0=y0, x1=x1, y1=y1,
                    line=dict(color="white", width=1.5), fillcolor="rgba(0,0,0,0)", layer="below")
    s.append(rect(0, 0, W, H, fill="#4a7c3f", lw=2))
    s.append(line(W/2, 0, W/2, H))
    s.append(circle(W/2-CR, H/2-CR, W/2+CR, H/2+CR))
    s.append(rect(0, (H-AG_Y)/2, AG_X, (H+AG_Y)/2))
    s.append(rect(0, (H-AC_Y)/2, AC_X, (H+AC_Y)/2))
    s.append(line(0, (H-ARCO)/2, 0, (H+ARCO)/2, lw=5))
    s.append(rect(W-AG_X, (H-AG_Y)/2, W, (H+AG_Y)/2))
    s.append(rect(W-AC_X, (H-AC_Y)/2, W, (H+AC_Y)/2))
    s.append(line(W, (H-ARCO)/2, W, (H+ARCO)/2, lw=5))
    return s

def layout_cancha(height=600):
    return dict(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#4a7c3f",
        xaxis=dict(range=[-2, W+2], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[H+2, -2], showgrid=False, zeroline=False, showticklabels=False,
                   scaleanchor="x", scaleratio=0.69),
        shapes=shapes_cancha(),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(color="white"), bgcolor="rgba(0,0,0,0.4)"),
    )

# --- Figura principal ---
fig = go.Figure()

# Líneas de pase con X2/Y2
if "pase" in eventos_sel and not df_pases_f.empty:
    for _, row in df_pases_f.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["x_origen"], row["x_destino"]],
            y=[row["y_origen"], row["y_destino"]],
            mode="lines",
            line=dict(color="rgba(255,255,255,0.4)", width=1.5),
            showlegend=False, hoverinfo="skip",
        ))

for evento in eventos_sel:
    subset = df_filtrado[df_filtrado["Event"] == evento]
    if subset.empty:
        continue
    fig.add_trace(go.Scatter(
        x=subset["X"], y=subset["Y"],
        mode="markers", name=evento,
        marker=dict(color=colores.get(evento, "#ffffff"), size=9, opacity=0.9,
                    line=dict(color="white", width=0.8)),
        customdata=subset[["Player", "Mins", "Secs"]].values,
        hovertemplate="<b>%{customdata[0]}</b><br>Evento: " + evento +
                      "<br>Tiempo: %{customdata[1]:.0f}:%{customdata[2]:.0f}<br>" +
                      "X: %{x:.0f} | Y: %{y:.0f}<extra></extra>",
    ))

fig.update_layout(**layout_cancha(600))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Heatmap ---
st.subheader("Zonas de mayor actividad")

nx, ny = 13, 9
xs = np.linspace(0, W, nx + 1)
ys = np.linspace(0, H, ny + 1)

grid = np.zeros((ny, nx))
for _, row in df_filtrado.iterrows():
    xi = min(int(row["X"] / W * nx), nx - 1)
    yi = min(int(row["Y"] / H * ny), ny - 1)
    grid[yi, xi] += 1

x_centers = [(xs[i] + xs[i+1]) / 2 for i in range(nx)]
y_centers = [(ys[i] + ys[i+1]) / 2 for i in range(ny)]

fig2 = go.Figure()
fig2.add_trace(go.Heatmap(
    z=grid, x=x_centers, y=y_centers,
    colorscale=[[0.0, "rgba(0,0,0,0)"], [0.01, "rgba(255,255,0,0.5)"],
                [0.5, "rgba(255,140,0,0.75)"], [1.0, "rgba(200,0,0,0.85)"]],
    showscale=False, hovertemplate="Eventos: %{z}<extra></extra>",
    zmin=0, xgap=1, ygap=1,
))
layout2 = layout_cancha(500)
layout2.pop("legend", None)
fig2.update_layout(**layout2)
st.plotly_chart(fig2, use_container_width=True)