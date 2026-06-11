import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import os
import math
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

# ── Gráfico 1: Mapa de pases Último Tercio ────────────────────────────────────
def grafico_pases_ultimo_tercio(df_p, ax):
    draw_pitch(ax)
    
    # Ajustamos el recorte visual
    ax.set_xlim(60, 102)
    ax.set_ylim(102, -2)
    
    # Dibujamos un marco para cerrar el recorte
    ax.add_patch(mpatches.Rectangle((60, -2), 42, 104, fill=False, edgecolor="#7A6A5E", lw=2, zorder=10))
    # Línea punteada marcando el inicio del último tercio (66.6)
    ax.plot([66.6, 66.6], [0, 100], color="#7A6A5E", linestyle=":", linewidth=1.2, zorder=2)
    
    pases = df_p[df_p["Event"] == "pase"].copy()
    for col in ["X","Y","X2","Y2"]:
        pases[col] = pd.to_numeric(pases[col], errors="coerce")
    
    completos = 0; incompletos = 0
    
    for idx, row in pases.iterrows():
        x1, y1 = float(row["X"]), float(row["Y"])
        x2, y2 = row["X2"], row["Y2"]
        
        if pd.isna(x1) or pd.isna(y1) or pd.isna(x2) or pd.isna(y2): continue
        
        # Filtro estricto: Solo pases que NACEN en el último tercio
        if x1 < 66.6:
            continue
            
        sig_event = ""
        if idx + 1 < len(df_p):
            sig_event = str(df_p.iloc[idx + 1]["Event"]).lower()
        complete = sig_event not in ["perdida",""]
        
        color = "#2E6F40" if complete else "#C93B3B"
        alpha = 0.8 if complete else 0.5
        
        if complete: completos += 1
        else: incompletos += 1
        
        ax.annotate("",
            xy=(float(x2), float(y2)), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="->", color=color, lw=1.5, alpha=alpha)
        )
        ax.plot(x1, y1, "o", color=color, markersize=3, alpha=alpha)

    legend = [
        mpatches.Patch(color="#2E6F40", label=f"Completo ({completos})"),
        mpatches.Patch(color="#C93B3B", label=f"Incompleto ({incompletos})"),
    ]
    ax.legend(handles=legend, loc="upper left", framealpha=0.9,
              facecolor="#FAF7F2", edgecolor="#7A6A5E", labelcolor="#3D2C24", fontsize=8)

# ── Gráfico 2: Heatmap Presión en Campo Rival (Mitad de cancha) ───────────────
def grafico_presion_rival(df_p, ax):
    draw_pitch(ax)
    
    ax.set_xlim(50, 102)
    ax.set_ylim(102, -2)
    # Marco de recorte para la mitad de cancha
    ax.add_patch(mpatches.Rectangle((50, -2), 52, 104, fill=False, edgecolor="#7A6A5E", lw=2, zorder=10))
    
    nx, ny = 13, 9
    xs = np.linspace(0, W, nx+1); ys = np.linspace(0, H, ny+1)
    grid = np.zeros((ny, nx))
    
    eventos_presion = ["recuperacion", "falta cometida"]
    df_presion = df_p[df_p["Event"].isin(eventos_presion)].copy()
    
    for _, row in df_presion.iterrows():
        try:
            x_val = float(row["X"])
            if x_val < 50: continue
            xi = min(int(x_val / W * nx), nx-1)
            yi = min(int(float(row["Y"]) / H * ny), ny-1)
            grid[yi, xi] += 1
        except: pass
        
    grid_masked = np.where(grid == 0, np.nan, grid)
    xc = [(xs[i]+xs[i+1])/2 for i in range(nx)]
    yc = [(ys[i]+ys[i+1])/2 for i in range(ny)]
    
    cmap = plt.cm.YlOrRd.copy()
    cmap.set_bad(alpha=0)
    
    ax.pcolormesh(xc, yc, grid_masked, cmap=cmap, shading="nearest", zorder=2, alpha=0.8)

# ── Gráfico 3: Actividad por minuto ──────────────────────────────────────────
def grafico_actividad(df_p, ax):
    ax.set_facecolor("#F2EEE7")
    act = df_p.groupby("Mins")["Event"].count()
    bars = ax.bar(act.index.astype(float), act.values, color="#7A6A5E", width=0.8)
    
    if len(act) > 0:
        top_mins = act.nlargest(2)
        for m_min, m_val in top_mins.items():
            events_m = df_p[df_p["Mins"] == m_min]
            if not events_m.empty:
                ev_counts = events_m["Event"].value_counts()
                top_ev = ev_counts.index[0]
                top_cnt = ev_counts.iloc[0]
                
                for bar in bars:
                    if abs(bar.get_x() + bar.get_width()/2 - float(m_min)) < 0.5:
                        bar.set_color("#A83232")
                
                ax.text(float(m_min), m_val + 0.3, f"Min {int(float(m_min))}\n{top_ev.title()} ({top_cnt})",
                        color="#A83232", fontsize=7.5, ha="center", va="bottom", fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.2", facecolor="#FAF7F2", edgecolor="#A83232", lw=0.5, alpha=0.9))

    ax.axvline(45, color="#A83232", linestyle="--", linewidth=1, alpha=0.7, label="HT")
    ax.set_xlabel("Minuto", color="#3D2C24", fontsize=9, fontfamily="serif")
    ax.set_ylabel("Eventos", color="#3D2C24", fontsize=9, fontfamily="serif")
    ax.tick_params(colors="#3D2C24", labelsize=8)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.legend(facecolor="#FAF7F2", edgecolor="#7A6A5E", labelcolor="#3D2C24", fontsize=8)

# ── Gráfico 4: Pases Largos al Último Tercio ──────────────────────────────────
def grafico_pases_largos(df_p, ax):
    draw_pitch(ax)
    
    pases = df_p[df_p["Event"] == "pase"].copy()
    for col in ["X","Y","X2","Y2"]:
        pases[col] = pd.to_numeric(pases[col], errors="coerce")
        
    for idx, row in pases.iterrows():
        x1, y1 = float(row["X"]), float(row["Y"])
        x2, y2 = row["X2"], row["Y2"]
        
        if pd.isna(x1) or pd.isna(y1) or pd.isna(x2) or pd.isna(y2): continue
        x2, y2 = float(x2), float(y2)
        
        distancia = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        if x2 >= 66.6 and distancia >= 30: 
            sig_event = ""
            if idx + 1 < len(df_p):
                sig_event = str(df_p.iloc[idx + 1]["Event"]).lower()
            complete = sig_event not in ["perdida",""]
            
            color = "#1D4ED8" if complete else "#9CA3AF"
            ax.annotate("",
                xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.5, alpha=0.8)
            )
            ax.plot(x1, y1, "o", color=color, markersize=4)

# ── Gráfico 5: Mapa de Remates en el Área ─────────────────────────────────────
def grafico_remates(df_p, ax):
    draw_pitch(ax)
    
    # Mostramos toda la mitad de cancha para no perder la referencia del área
    ax.set_xlim(50, 102)
    ax.set_ylim(102, -2)
    # Marco de recorte para la mitad de cancha
    ax.add_patch(mpatches.Rectangle((50, -2), 52, 104, fill=False, edgecolor="#7A6A5E", lw=2, zorder=10))
    
    remates = df_p[df_p["Event"].isin(["remate", "gol"])].copy()
    for col in ["X","Y"]:
        remates[col] = pd.to_numeric(remates[col], errors="coerce")
        
    for _, row in remates.iterrows():
        x, y = float(row["X"]), float(row["Y"])
        if pd.isna(x) or pd.isna(y): continue
        
        es_gol = (row["Event"] == "gol")
        color = "#C93B3B" if es_gol else "#4B5563"
        marker = "o" if es_gol else "x"
        size = 120 if es_gol else 60
        
        ax.scatter(x, y, color=color, marker=marker, s=size, zorder=5, alpha=0.9, edgecolors="#FAF7F2")

# ── Generar Imagen General ────────────────────────────────────────────────────
def generar_imagen(df_p, rival, condicion, resultado, num_fecha):
    buf = io.BytesIO()
    fig = plt.figure(figsize=(12, 22), facecolor="#FAF7F2")
    
    pases_t    = len(df_p[df_p["Event"] == "pase"])
    recup_t    = len(df_p[df_p["Event"] == "recuperacion"])
    perdidas_t = len(df_p[df_p["Event"] == "perdida"])
    remates_t  = len(df_p[df_p["Event"] == "remate"]) + len(df_p[df_p["Event"] == "gol"])
    goles_t    = len(df_p[df_p["Event"] == "gol"])
    faltas_t   = len(df_p[df_p["Event"] == "falta cometida"])
    ratio      = round(pases_t / perdidas_t, 1) if perdidas_t > 0 else "—"

    # 1. Encabezado
    if os.path.exists(ESCUDO_PATH):
        try:
            from PIL import Image as PILImage
            img = PILImage.open(ESCUDO_PATH)
            logo_ax = fig.add_axes([0.05, 0.92, 0.05, 0.027])
            logo_ax.imshow(img)
            logo_ax.set_aspect("equal")
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

    fig.add_axes([0.05, 0.89, 0.90, 0.002], facecolor="#8A2525").axis("off")

    # Títulos Fila 1
    fig.text(0.05, 0.865, "Pases en el Último Tercio", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")
    fig.text(0.415, 0.865, "Estadísticas", color="#3D2C24", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")
    fig.text(0.62, 0.865, "Presión en Campo Rival", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")

    # 2. Fila 1 Subplots
    ax_pases = fig.add_axes([0.05, 0.57, 0.33, 0.28])
    ax_table = fig.add_axes([0.415, 0.57, 0.17, 0.28])
    ax_heatmap = fig.add_axes([0.62, 0.57, 0.33, 0.28])
    
    grafico_pases_ultimo_tercio(df_p, ax=ax_pases)
    grafico_presion_rival(df_p, ax=ax_heatmap)

    # Tabla vertical de Estadísticas
    ax_table.axis("off")
    ax_table.text(0.05, 0.88, "Métrica", color="#3D2C24", fontsize=10, fontweight="bold", ha="left", fontfamily="monospace")
    ax_table.text(0.95, 0.88, "Valor", color="#3D2C24", fontsize=10, fontweight="bold", ha="right", fontfamily="monospace")
    ax_table.plot([0.01, 0.99], [0.82, 0.82], color="#7A6A5E", linewidth=1.5)
    
    kpis_table_data = [
        ("Pases", str(pases_t), True),
        ("Recuperaciones", str(recup_t), False),
        ("Pérdidas", str(perdidas_t), False),
        ("Ratio P/P", str(ratio), False),
        ("Remates", str(remates_t), False),
        ("Goles", str(goles_t), goles_t > 0),
        ("Faltas", str(faltas_t), False)
    ]
    y_val = 0.70
    for label, val, accent in kpis_table_data:
        ax_table.text(0.05, y_val, label, color="#3D2C24", fontsize=10, ha="left", fontfamily="monospace")
        val_color = "#A83232" if accent else "#3D2C24"
        ax_table.text(0.95, y_val, val, color=val_color, fontweight="bold", ha="right", fontfamily="monospace")
        ax_table.plot([0.01, 0.99], [y_val - 0.05, y_val - 0.05], color="#7A6A5E", linewidth=0.5, linestyle=":")
        y_val -= 0.10

    # Título Fila 2
    fig.text(0.05, 0.535, "Actividad por Minuto", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")

    # 3. Fila 2 Subplot: Actividad
    ax_act = fig.add_axes([0.05, 0.39, 0.90, 0.13])
    grafico_actividad(df_p, ax=ax_act)

    # Títulos Fila 3
    fig.text(0.05, 0.345, "Pases Largos al Último Tercio (>30m)", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")
    fig.text(0.55, 0.345, "Mapa de Remates en el Área", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")

    # 4. Fila 3 Subplots: Pases Largos y Remates
    ax_largos = fig.add_axes([0.05, 0.08, 0.40, 0.24])
    ax_remates = fig.add_axes([0.55, 0.08, 0.40, 0.24])
    
    grafico_pases_largos(df_p, ax_largos)
    grafico_remates(df_p, ax_remates)

    fig.add_axes([0.05, 0.055, 0.90, 0.001], facecolor="#7A6A5E").axis("off")

    # 5. Firma
    fig.text(0.05, 0.024, "IAO Footbal Analytics", color="#8A2525", fontsize=12, ha="left", va="center", fontweight="bold", fontfamily="serif")
    fig.text(0.05, 0.012, "video-analisis-app.streamlit.app", color="#7A6A5E", fontsize=9, ha="left", va="center", fontfamily="serif")
    fig.text(0.5, 0.018, "IAO", color="#8A2525", fontsize=24, ha="center", va="center", fontfamily="serif", fontstyle="italic", fontweight="bold")
    fig.text(0.95, 0.018, "Análisis de Video y Datos", color="#3D2C24", fontsize=10, ha="right", va="center", fontfamily="serif")

    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf

img_buf = generar_imagen(df_p, rival, condicion, resultado, num_fecha)
st.image(img_buf, use_container_width=True)
