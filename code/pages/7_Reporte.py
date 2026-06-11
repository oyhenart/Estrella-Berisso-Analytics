import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import os
from components.layout import inject_css, render_sidebar

st.set_page_config(page_title="Reporte Imagen", page_icon="🖼", layout="wide")
inject_css()

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
render_sidebar(BASE)

DATA_PATH      = os.path.join(BASE, "data", "events_clean.csv")
FIXTURE_PATH   = os.path.join(BASE, "data", "fixture.csv")
JUGADORES_PATH = os.path.join(BASE, "data", "Jugadores.csv")
ESCUDO_PATH    = os.path.join(BASE, "static", "escudo.png")

st.markdown("""
<div style='margin-bottom:24px'>
    <p style='font-size:0.68em;font-weight:600;color:#E23E3E;text-transform:uppercase;letter-spacing:3px;margin:0 0 4px 0'>Documentos</p>
    <h1 style='font-size:1.9em;font-weight:800;margin:0;color:#F9FAFB;letter-spacing:-0.5px'>Reporte post-partido</h1>
</div>
""", unsafe_allow_html=True)

if not os.path.exists(DATA_PATH):
    st.info("⏳ No hay datos disponibles aún.")
    st.stop()

@st.cache_data
def cargar_datos():
    return pd.read_csv(DATA_PATH)

@st.cache_data(ttl=0)
def cargar_fixture():
    return pd.read_csv(FIXTURE_PATH)

@st.cache_data(ttl=0)
def cargar_jugadores():
    df = pd.read_csv(JUGADORES_PATH)
    df["nombre"]   = df["nombre"].str.strip().str.title()
    df["posicion"] = df["posicion"].str.strip().str.title()
    return df

df         = cargar_datos()
fixture    = cargar_fixture()
jugadores_df = cargar_jugadores()
pos_map    = dict(zip(jugadores_df["nombre"], jugadores_df["posicion"]))

# ── Selector de partido ───────────────────────────────────────────────────────
fechas    = sorted(df["fecha"].unique().tolist())
fecha_sel = st.selectbox("Seleccioná el partido", [f"Fecha {f}" for f in fechas])
num_fecha = int(fecha_sel.replace("Fecha ", ""))

df_p        = df[df["fecha"] == num_fecha].copy().reset_index(drop=True)
fixture_row = fixture[fixture["fecha"] == num_fecha]
rival       = fixture_row["rival"].values[0]       if not fixture_row.empty else "Rival"
condicion   = fixture_row["condicion"].values[0]   if not fixture_row.empty else ""
resultado   = ""
if not fixture_row.empty and str(fixture_row["estado"].values[0]) == "Jugado":
    gf = int(fixture_row["goles_favor"].values[0])
    gc = int(fixture_row["goles_contra"].values[0])
    resultado = f"{gf} - {gc}"

st.markdown(f"""
<div style='background:#1F2937;border-left:3px solid #E23E3E;border-radius:4px;padding:14px 20px;margin-bottom:20px'>
    <span style='color:#9CA3AF;font-size:0.72em;text-transform:uppercase;letter-spacing:2px'>Partido seleccionado</span><br>
    <span style='color:#F9FAFB;font-size:1.2em;font-weight:700'>Estrella de Berisso vs {rival}</span>
    <span style='color:#6B7280;font-size:0.9em;margin-left:12px'>{condicion}</span>
    {'<span style="color:#E23E3E;font-size:1.1em;font-weight:700;margin-left:12px">' + resultado + '</span>' if resultado else ''}
</div>
""", unsafe_allow_html=True)

# ── Constantes de cancha ──────────────────────────────────────────────────────
W, H = 100, 100
AG_X=12.7; AG_Y=44.8; AC_X=4.2; AC_Y=20.4; ARCO=8.1; CR=7.0
PITCH_BG = "#F2EEE7"

METRICAS_POS = {
    "Arquero":       ["despeje","recuperacion","pase"],
    "Defensor":      ["recuperacion","despeje","falta cometida"],
    "Mediocampista": ["pase","recuperacion","conduccion"],
    "Delantero":     ["remate","gol","centro","conduccion"],
}
COLOR_POS = {"Arquero":"#5D8AA8","Defensor":"#4F7942",
             "Mediocampista":"#C2B280","Delantero":"#C36262"}

# ── Helpers ───────────────────────────────────────────────────────────────────
def draw_pitch(ax):
    ax.set_facecolor(PITCH_BG)
    ax.set_xlim(-2, 102); ax.set_ylim(102, -2)
    ax.set_aspect("equal"); ax.axis("off")
    kw = dict(color="#7A6A5E", linewidth=1.5)
    ax.plot([0,W,W,0,0],[0,0,H,H,0], **kw)
    ax.plot([W/2,W/2],[0,H], **kw)
    ax.add_patch(plt.Circle((W/2,H/2), CR, fill=False, **kw))
    ax.plot(W/2, H/2, "o", color="#7A6A5E", markersize=3)
    for x0,x1 in [(0,AG_X),(W-AG_X,W)]:
        ax.plot([x0,x1,x1,x0,x0],
                [(H-AG_Y)/2,(H-AG_Y)/2,(H+AG_Y)/2,(H+AG_Y)/2,(H-AG_Y)/2], **kw)
    for x0,x1 in [(0,AC_X),(W-AC_X,W)]:
        ax.plot([x0,x1,x1,x0,x0],
                [(H-AC_Y)/2,(H-AC_Y)/2,(H+AC_Y)/2,(H+AC_Y)/2,(H-AC_Y)/2], **kw)
    ax.plot([0,0],[(H-ARCO)/2,(H+ARCO)/2], color="#7A6A5E", linewidth=3.5)
    ax.plot([W,W],[(H-ARCO)/2,(H+ARCO)/2], color="#7A6A5E", linewidth=3.5)

def fig_to_buf(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf

# ── Gráfico 1: Mapa de pases ──────────────────────────────────────────────────
def grafico_pases(df_p, ax=None):
    pases = df_p[df_p["Event"] == "pase"].copy()
    # forzar numérico
    for col in ["X","Y","X2","Y2"]:
        pases[col] = pd.to_numeric(pases[col], errors="coerce")

    is_standalone = ax is None
    if is_standalone:
        fig, ax = plt.subplots(figsize=(10, 6.9))
        fig.patch.set_facecolor("#FAF7F2")
    else:
        fig = ax.figure
    draw_pitch(ax)

    completos = 0; incompletos = 0
    for _, row in pases.iterrows():
        x1, y1 = float(row["X"]), float(row["Y"])
        x2, y2 = row["X2"], row["Y2"]
        if pd.isna(x1) or pd.isna(y1): continue
        if pd.notna(x2) and pd.notna(y2):
            x2, y2 = float(x2), float(y2)
            # ver si el siguiente evento es recuperacion (pase completo)
            idx = row.name
            sig_event = ""
            if idx + 1 < len(df_p):
                sig_event = str(df_p.iloc[idx + 1]["Event"]).lower()
            color = "#2E6F40" if sig_event not in ["perdida",""] else "#C93B3B"
            if color == "#2E6F40": completos += 1
            else: incompletos += 1
            dx, dy = x2 - x1, y2 - y1
            ax.annotate("",
                xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=color,
                    lw=1.5,
                    mutation_scale=10,
                ),
            )
        else:
            # pase sin destino — punto simple
            ax.plot(x1, y1, "o", color="#C93B3B", markersize=4, alpha=0.6)
            incompletos += 1

    legend = [
        mpatches.Patch(color="#2E6F40", label=f"Pase completo ({completos})"),
        mpatches.Patch(color="#C93B3B", label=f"Pase incompleto ({incompletos})"),
    ]
    ax.legend(handles=legend, loc="upper left", framealpha=0.9,
              facecolor="#FAF7F2", edgecolor="#7A6A5E", labelcolor="#3D2C24", fontsize=8)
    if is_standalone:
        ax.set_title("Mapa de pases", color="#3D2C24", fontsize=11, pad=8, fontfamily="serif")
    return fig

# ── Gráfico 2: Heatmap ────────────────────────────────────────────────────────
def grafico_heatmap(df_p, ax=None):
    is_standalone = ax is None
    if is_standalone:
        fig, ax = plt.subplots(figsize=(10, 6.9))
        fig.patch.set_facecolor("#FAF7F2")
    else:
        fig = ax.figure
    draw_pitch(ax)
    nx, ny = 13, 9
    xs = np.linspace(0, W, nx+1); ys = np.linspace(0, H, ny+1)
    grid = np.zeros((ny, nx))
    for _, row in df_p.iterrows():
        try:
            xi = min(int(float(row["X"]) / W * nx), nx-1)
            yi = min(int(float(row["Y"]) / H * ny), ny-1)
            grid[yi, xi] += 1
        except: pass
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "heat", [(0,"none"),(0.01,"#FFCC0044"),(0.5,"#FF660088"),(1,"#A83232CC")])
    xc = [(xs[i]+xs[i+1])/2 for i in range(nx)]
    yc = [(ys[i]+ys[i+1])/2 for i in range(ny)]
    ax.pcolormesh(xc, yc, grid, cmap=cmap, shading="nearest", zorder=2, alpha=0.8)
    if is_standalone:
        ax.set_title("Zonas de actividad", color="#3D2C24", fontsize=11, pad=8, fontfamily="serif")
    return fig

# ── Gráfico 3: Protagonistas ──────────────────────────────────────────────────
def grafico_protagonistas(df_p, pos_map, axes=None):
    jugadores_top = []
    for jugador in df_p["Player"].unique():
        dj  = df_p[df_p["Player"] == jugador]
        pos = pos_map.get(jugador, "")
        met = METRICAS_POS.get(pos, ["pase","recuperacion","remate"])
        score = sum(len(dj[dj["Event"] == m]) for m in met)
        jugadores_top.append((jugador, pos, score, met))
    jugadores_top.sort(key=lambda x: x[2], reverse=True)
    top3 = jugadores_top[:3]

    is_standalone = axes is None
    if is_standalone:
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))
        fig.patch.set_facecolor("#FAF7F2")
    else:
        fig = axes[0].figure
    for i, (jugador, pos, score, met) in enumerate(top3):
        ax = axes[i]
        ax.set_facecolor("#F2EEE7")
        dj   = df_p[df_p["Player"] == jugador]
        vals = [len(dj[dj["Event"] == m]) for m in met[:4]]
        labs = [m.capitalize() for m in met[:4]]
        color = COLOR_POS.get(pos, "#7A6A5E")
        bars = ax.barh(labs, vals, color=color, alpha=0.85)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_width()+0.1, bar.get_y()+bar.get_height()/2,
                    str(val), va="center", color="#3D2C24", fontsize=9, fontfamily="monospace")
        ax.set_title(f"{jugador}\n{pos or '—'}", color="#3D2C24", fontsize=9, pad=6, fontfamily="serif")
        ax.tick_params(colors="#3D2C24", labelsize=8)
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.set_xlim(0, max(vals or [1]) * 1.35)
    if is_standalone:
        fig.suptitle("Protagonistas del partido", color="#3D2C24", fontsize=12, y=1.02, fontfamily="serif")
        fig.tight_layout()
    return fig

# ── Gráfico 4: Actividad por minuto ──────────────────────────────────────────
def grafico_actividad(df_p, ax=None):
    is_standalone = ax is None
    if is_standalone:
        fig, ax = plt.subplots(figsize=(10, 3))
        fig.patch.set_facecolor("#FAF7F2")
    else:
        fig = ax.figure
    ax.set_facecolor("#F2EEE7")
    act = df_p.groupby("Mins")["Event"].count()
    ax.bar(act.index.astype(float), act.values, color="#7A6A5E", width=0.8)
    ax.axvline(45, color="#A83232", linestyle="--", linewidth=1, alpha=0.7, label="HT")
    ax.set_xlabel("Minuto", color="#3D2C24", fontsize=9, fontfamily="serif")
    ax.set_ylabel("Eventos", color="#3D2C24", fontsize=9, fontfamily="serif")
    if is_standalone:
        ax.set_title("Actividad por minuto", color="#3D2C24", fontsize=11, fontfamily="serif")
    ax.tick_params(colors="#3D2C24", labelsize=8)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.legend(facecolor="#FAF7F2", edgecolor="#7A6A5E", labelcolor="#3D2C24", fontsize=8)
    if is_standalone:
        fig.tight_layout()
    return fig

# ── Generar Imagen ────────────────────────────────────────────────────────────
def generar_imagen(df_p, rival, condicion, resultado, pos_map, num_fecha):
    buf = io.BytesIO()
    # Formato vertical de alta resolución (estilo infografía crema): 12" x 18"
    fig = plt.figure(figsize=(12, 18), facecolor="#FAF7F2")
    
    # Calcular KPIs
    pases_t    = len(df_p[df_p["Event"] == "pase"])
    recup_t    = len(df_p[df_p["Event"] == "recuperacion"])
    perdidas_t = len(df_p[df_p["Event"] == "perdida"])
    remates_t  = len(df_p[df_p["Event"] == "remate"])
    goles_t    = len(df_p[df_p["Event"] == "gol"])
    faltas_t   = len(df_p[df_p["Event"] == "falta cometida"])
    ratio      = round(pases_t / perdidas_t, 1) if perdidas_t > 0 else "—"

    # Calcular observaciones
    obs = []
    if ratio != "—":
        r = float(ratio)
        if r < 3:   obs.append("• Ratio pase/pérdida bajo. Trabajar salida desde el fondo y circuitos de circulación.")
        elif r >= 5: obs.append("• Buen cuidado de la pelota. El equipo circuló con criterio.")
    despejes = len(df_p[df_p["Event"] == "despeje"])
    if despejes > 15: obs.append(f"• {despejes} despejes. El equipo soportó presión. Revisar bloque defensivo.")
    if faltas_t > 8:  obs.append(f"• {faltas_t} faltas cometidas. Riesgo disciplinario elevado.")
    if remates_t > 0: obs.append(f"• {remates_t} remates generados. {'Buena llegada al área.' if remates_t >= 5 else 'Llegada escasa al área rival.'}")
    if not obs:       obs.append("• Sin alertas tácticas relevantes en este partido.")

    # 1. Encabezado
    if os.path.exists(ESCUDO_PATH):
        try:
            from PIL import Image as PILImage
            img = PILImage.open(ESCUDO_PATH)
            logo_ax = fig.add_axes([0.05, 0.91, 0.05, 0.05])
            logo_ax.imshow(img)
            logo_ax.axis("off")
        except Exception:
            pass

    header_ax = fig.add_axes([0.05, 0.90, 0.90, 0.08])
    header_ax.axis("off")
    
    header_ax.text(0.5, 0.70, f"Estrella de Berisso vs {rival}", 
                   color="#8A2525", fontsize=22, fontweight="bold", ha="center", va="center", fontfamily="serif")
    
    partido_txt = f"Fecha {num_fecha}  ·  {condicion}"
    if resultado: partido_txt += f"  ·  Resultado: {resultado}"
    header_ax.text(0.5, 0.25, partido_txt, 
                   color="#3D2C24", fontsize=11, fontweight="bold", ha="center", va="center", fontfamily="serif")

    # Línea divisoria roja
    fig.add_axes([0.05, 0.89, 0.90, 0.002], facecolor="#8A2525").axis("off")

    # Títulos de la Fila 1
    fig.text(0.05, 0.865, "Mapa de Pases", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")
    fig.text(0.415, 0.865, "Métricas", color="#3D2C24", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")
    fig.text(0.62, 0.865, "Zonas de Actividad", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")

    # 2. Fila 1 Subplots: Mapa Pases, Tabla KPIs, Heatmap
    ax_pases = fig.add_axes([0.05, 0.48, 0.33, 0.37])
    ax_table = fig.add_axes([0.415, 0.48, 0.17, 0.37])
    ax_heatmap = fig.add_axes([0.62, 0.48, 0.33, 0.37])
    
    grafico_pases(df_p, ax=ax_pases)
    grafico_heatmap(df_p, ax=ax_heatmap)

    # Dibujar tabla vertical de Estadísticas
    ax_table.axis("off")
    ax_table.text(0.05, 0.92, "Métrica", color="#3D2C24", fontsize=11, fontweight="bold", ha="left", fontfamily="monospace")
    ax_table.text(0.95, 0.92, "Valor", color="#3D2C24", fontsize=11, fontweight="bold", ha="right", fontfamily="monospace")
    ax_table.plot([0.01, 0.99], [0.85, 0.85], color="#7A6A5E", linewidth=1.5)
    
    kpis_table_data = [
        ("Pases", str(pases_t), True),
        ("Recuperaciones", str(recup_t), False),
        ("Pérdidas", str(perdidas_t), False),
        ("Ratio P/P", str(ratio), False),
        ("Remates", str(remates_t), False),
        ("Goles", str(goles_t), goles_t > 0),
        ("Faltas", str(faltas_t), False)
    ]
    y_val = 0.73
    for label, val, accent in kpis_table_data:
        ax_table.text(0.05, y_val, label, color="#3D2C24", fontsize=10, ha="left", fontfamily="monospace")
        val_color = "#A83232" if accent else "#3D2C24"
        ax_table.text(0.95, y_val, val, color=val_color, fontsize=10, fontweight="bold", ha="right", fontfamily="monospace")
        ax_table.plot([0.01, 0.99], [y_val - 0.05, y_val - 0.05], color="#7A6A5E", linewidth=0.5, linestyle=":")
        y_val -= 0.10

    # Títulos de la Fila 2
    fig.text(0.05, 0.435, "Actividad por Minuto", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")
    fig.text(0.52, 0.435, "Protagonistas del Partido", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")

    # 3. Fila 2 Subplots: Actividad y Protagonistas
    ax_act = fig.add_axes([0.05, 0.20, 0.43, 0.22])
    ax_p1 = fig.add_axes([0.52, 0.20, 0.13, 0.22])
    ax_p2 = fig.add_axes([0.67, 0.20, 0.13, 0.22])
    ax_p3 = fig.add_axes([0.82, 0.20, 0.13, 0.22])
    
    grafico_actividad(df_p, ax=ax_act)
    grafico_protagonistas(df_p, pos_map, axes=[ax_p1, ax_p2, ax_p3])

    # Título de la Fila 3
    fig.text(0.05, 0.165, "Observaciones del Analista", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")

    # 4. Fila 3: Observaciones
    obs_ax = fig.add_axes([0.05, 0.06, 0.90, 0.09])
    obs_ax.axis("off")
    import matplotlib.patches as patches
    rect_obs = patches.FancyBboxPatch(
        (0.0, 0.05), 1.0, 0.9,
        boxstyle="round,pad=0.01",
        facecolor="#F2EEE7", edgecolor="#7A6A5E", linewidth=1
    )
    obs_ax.add_patch(rect_obs)
    
    y_pos = 0.75
    for o in obs:
        obs_ax.text(
            0.03, y_pos, o,
            color="#3D2C24", fontsize=10.5, ha="left", va="center", fontfamily="serif"
        )
        y_pos -= 0.22

    # Línea divisoria inferior
    fig.add_axes([0.05, 0.045, 0.90, 0.001], facecolor="#7A6A5E").axis("off")

    # 5. Firma / Pie de página
    fig.text(0.05, 0.024, "IAO Footbal Analytics", color="#8A2525", fontsize=12, ha="left", va="center", fontweight="bold", fontfamily="serif")
    fig.text(0.05, 0.012, "video-analisis-app.streamlit.app", color="#7A6A5E", fontsize=9, ha="left", va="center", fontfamily="serif")
    
    fig.text(0.5, 0.018, "IAO", color="#8A2525", fontsize=24, ha="center", va="center", fontfamily="serif", fontstyle="italic", fontweight="bold")
    
    fig.text(0.95, 0.018, "Análisis de Video y Datos", color="#3D2C24", fontsize=10, ha="right", va="center", fontfamily="serif")

    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf

# Generar y mostrar la imagen del reporte directamente
img_buf = generar_imagen(df_p, rival, condicion, resultado, pos_map, num_fecha)
st.image(img_buf, use_container_width=True)
