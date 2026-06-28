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
from PIL import Image as PILImage
from components.layout import inject_css, render_sidebar

st.set_page_config(page_title="Reporte Imagen", page_icon="🖼", layout="wide")
inject_css()

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
render_sidebar(BASE)

DATA_PATH      = os.path.join(BASE, "data", "events_clean.csv")
FIXTURE_PATH   = os.path.join(BASE, "data", "fixture.csv")
JUGADORES_PATH = os.path.join(BASE, "data", "Jugadores.csv")
ESCUDOS_DIR    = os.path.join(BASE, "static", "escudos")

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

df           = cargar_datos()
fixture      = cargar_fixture()
jugadores_df = cargar_jugadores()
pos_map      = dict(zip(jugadores_df["nombre"], jugadores_df["posicion"]))

# ── Escudos ────────────────────────────────────────────────────────────────
def buscar_escudo(nombre_rival):
    if not nombre_rival or not os.path.isdir(ESCUDOS_DIR):
        return None
    candidatos = [
        f"{nombre_rival}.png", f"{nombre_rival}.jpg",
        f"{nombre_rival}.jpeg", f"{nombre_rival}.webp",
    ]
    archivos_existentes = os.listdir(ESCUDOS_DIR)
    archivos_lower = {a.lower(): a for a in archivos_existentes}
    for candidato in candidatos:
        ruta = os.path.join(ESCUDOS_DIR, candidato)
        if os.path.exists(ruta):
            return ruta
        if candidato.lower() in archivos_lower:
            return os.path.join(ESCUDOS_DIR, archivos_lower[candidato.lower()])
    return None

# ── Selector de partido ───────────────────────────────────────────────────────
fechas    = sorted(df["fecha"].unique().tolist(), reverse=True)
fecha_sel = st.selectbox("Seleccioná el partido", [f"Fecha {f}" for f in fechas])
num_fecha = int(fecha_sel.replace("Fecha ", ""))

df_p        = df[df["fecha"] == num_fecha].copy().reset_index(drop=True)
fixture_row = fixture[fixture["fecha"] == num_fecha]
rival       = fixture_row["rival"].values[0]     if not fixture_row.empty else "Rival"
condicion   = fixture_row["condicion"].values[0] if not fixture_row.empty else ""
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

# ── Normalización de minutos ──────────────────────────────────────────────────
def mins_reales_partido(ep: pd.DataFrame) -> pd.DataFrame:
    m1 = ep[ep["mitad"] == 1]
    m2 = ep[ep["mitad"] == 2]
    if m1.empty or m2.empty:
        ep = ep.copy()
        ep["Mins_real"] = ep["Mins"]
        return ep
    m1_max  = m1["Mins"].max()
    m2_min  = m2["Mins"].min()
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

# ── Helpers Canchas ───────────────────────────────────────────────────────────
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

def draw_half_pitch_horizontal_layout(ax):
    ax.set_facecolor(PITCH_BG)
    ax.set_xlim(-2, 102); ax.set_ylim(48, 102)
    ax.set_aspect("equal"); ax.axis("off")
    kw = dict(color="#7A6A5E", linewidth=1.5)
    ax.plot([0, 100, 100, 0, 0], [50, 50, 100, 100, 50], **kw)
    arc = mpatches.Arc((50, 50), CR*2, CR*2, angle=0, theta1=0, theta2=180, **kw)
    ax.add_patch(arc)
    ax.plot(50, 50, "o", color="#7A6A5E", markersize=3)
    ax.plot([(100-AG_Y)/2,(100-AG_Y)/2,(100+AG_Y)/2,(100+AG_Y)/2],
            [100,100-AG_X,100-AG_X,100], **kw)
    ax.plot([(100-AC_Y)/2,(100-AC_Y)/2,(100+AC_Y)/2,(100+AC_Y)/2],
            [100,100-AC_X,100-AC_X,100], **kw)
    ax.plot([(100-ARCO)/2,(100+ARCO)/2], [100,100], color="#7A6A5E", linewidth=3.5)
    ax.add_patch(mpatches.Rectangle((-2,48),104,54,fill=False,edgecolor="#7A6A5E",lw=2,zorder=10))

def pase_completo(df_p, idx, x_dest, y_dest, tolerancia=5, ventana=4):
    for j in range(idx + 1, min(idx + ventana + 1, len(df_p))):
        sig = df_p.iloc[j]
        try:
            x_sig = float(sig["X"]); y_sig = float(sig["Y"])
        except:
            continue
        if math.sqrt((x_dest - x_sig)**2 + (y_dest - y_sig)**2) <= tolerancia:
            return True
    return False

# ── Gráfico 1: Mapa de pases Último Tercio ───────────────────────────────────
def grafico_pases_ultimo_tercio(df_p, ax):
    draw_half_pitch_horizontal_layout(ax)
    ax.plot([-2,102],[66.6,66.6],color="#7A6A5E",linestyle=":",linewidth=1.2,zorder=2)
    pases = df_p[df_p["Event"] == "pase"].copy()
    for col in ["X","Y","X2","Y2"]:
        pases[col] = pd.to_numeric(pases[col], errors="coerce")
    completos = 0; incompletos = 0
    for idx, row in pases.iterrows():
        orig_x1,orig_y1 = float(row["X"]),float(row["Y"])
        orig_x2,orig_y2 = row["X2"],row["Y2"]
        if any(pd.isna(v) for v in [orig_x1,orig_y1,orig_x2,orig_y2]):
            continue
        if orig_x1 < 66.6: continue
        x2_f, y2_f = float(orig_x2), float(orig_y2)
        if x2_f < 66.6: continue
        x1,y1 = orig_y1,orig_x1
        x2,y2 = float(orig_y2),float(orig_x2)
        complete = pase_completo(df_p,idx,float(orig_x2),float(orig_y2))
        color = "#2E6F40" if complete else "#C93B3B"
        alpha = 0.8 if complete else 0.5
        if complete: completos += 1
        else: incompletos += 1
        ax.annotate("",xy=(x2,y2),xytext=(x1,y1),
                    arrowprops=dict(arrowstyle="->",color=color,lw=1.5,alpha=alpha))
        ax.plot(x1,y1,"o",color=color,markersize=3,alpha=alpha)
    ax.legend(handles=[
        mpatches.Patch(color="#2E6F40",label=f"Completo ({completos})"),
        mpatches.Patch(color="#C93B3B",label=f"Incompleto ({incompletos})"),
    ],loc="upper left",framealpha=0.9,facecolor="#FAF7F2",
              edgecolor="#7A6A5E",labelcolor="#3D2C24",fontsize=8)

# ── Gráfico 2: Heatmap Presión en Campo Rival ────────────────────────────────
def grafico_presion_rival(df_p, ax):
    draw_half_pitch_horizontal_layout(ax)
    nx,ny = 9,13
    xs = np.linspace(0,100,nx+1); ys = np.linspace(0,100,ny+1)
    grid = np.zeros((ny,nx))
    df_presion = df_p[df_p["Event"].isin(["recuperacion","falta cometida"])].copy()
    for _,row in df_presion.iterrows():
        try:
            orig_x,orig_y = float(row["X"]),float(row["Y"])
            if orig_x < 50: continue
            xi = min(int(orig_y/100*nx),nx-1)
            yi = min(int(orig_x/100*ny),ny-1)
            grid[yi,xi] += 1
        except: pass
    grid_masked = np.where(grid==0,np.nan,grid)
    xc = [(xs[i]+xs[i+1])/2 for i in range(nx)]
    yc = [(ys[i]+ys[i+1])/2 for i in range(ny)]
    cmap = plt.cm.YlOrRd.copy(); cmap.set_bad(alpha=0)
    ax.pcolormesh(xc,yc,grid_masked,cmap=cmap,shading="nearest",zorder=2,alpha=0.8)

# ── Gráfico 3: Actividad por minuto ──────────────────────────────────────────
def grafico_actividad(df_p, ax):
    ax.set_facecolor("#F2EEE7")
    df_fixed = mins_reales_partido(df_p)
    act = df_fixed.groupby("Mins_real")["Event"].count()
    bars = ax.bar(act.index.astype(float), act.values, color="#7A6A5E", width=0.8)

    if len(act) > 0:
        top_mins = act.nlargest(2)
        for m_min, m_val in top_mins.items():
            events_m = df_fixed[df_fixed["Mins_real"] == m_min]
            if not events_m.empty:
                ev_counts = events_m["Event"].value_counts()
                top_ev = ev_counts.index[0]; top_cnt = ev_counts.iloc[0]
                for bar in bars:
                    if abs(bar.get_x() + bar.get_width()/2 - float(m_min)) < 0.5:
                        bar.set_color("#A83232")
                ax.text(float(m_min), m_val+0.3,
                        f"Min {int(float(m_min))}\n{top_ev.title()} ({top_cnt})",
                        color="#A83232",fontsize=7.5,ha="center",va="bottom",
                        fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.2",facecolor="#FAF7F2",
                                  edgecolor="#A83232",lw=0.5,alpha=0.9))

    m1 = df_fixed[df_fixed["mitad"]==1]
    ht_line = m1["Mins_real"].max() if not m1.empty else 45
    ax.axvline(ht_line,color="#A83232",linestyle="--",linewidth=1,alpha=0.7,label="HT")
    ax.set_xlabel("Minuto",color="#3D2C24",fontsize=9,fontfamily="serif")
    ax.set_ylabel("Eventos",color="#3D2C24",fontsize=9,fontfamily="serif")
    ax.tick_params(colors="#3D2C24",labelsize=8)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.legend(facecolor="#FAF7F2",edgecolor="#7A6A5E",labelcolor="#3D2C24",fontsize=8)

# ── Gráfico 4: Pases Largos al Último Tercio ─────────────────────────────────
def grafico_pases_largos(df_p, ax):
    draw_pitch(ax)
    pases = df_p[df_p["Event"]=="pase"].copy()
    for col in ["X","Y","X2","Y2"]:
        pases[col] = pd.to_numeric(pases[col],errors="coerce")
    completos=0; incompletos=0
    for idx,row in pases.iterrows():
        x1,y1 = float(row["X"]),float(row["Y"])
        x2,y2 = row["X2"],row["Y2"]
        if any(pd.isna(v) for v in [x1,y1,x2,y2]): continue
        x2,y2 = float(x2),float(y2)
        dist = math.sqrt((x2-x1)**2+(y2-y1)**2)
        if x1<66.6 and x2>=66.6 and dist>=30:
            complete = pase_completo(df_p,idx,x2,y2)
            color = "#2E6F40" if complete else "#C93B3B"
            alpha = 0.8 if complete else 0.5
            if complete: completos+=1
            else: incompletos+=1
            ax.annotate("",xy=(x2,y2),xytext=(x1,y1),
                        arrowprops=dict(arrowstyle="-|>",color=color,lw=1.5,alpha=alpha))
            ax.plot(x1,y1,"o",color=color,markersize=4,alpha=alpha)
    ax.legend(handles=[
        mpatches.Patch(color="#2E6F40",label=f"Completo ({completos})"),
        mpatches.Patch(color="#C93B3B",label=f"Incompleto ({incompletos})"),
    ],loc="upper left",framealpha=0.9,facecolor="#FAF7F2",
              edgecolor="#7A6A5E",labelcolor="#3D2C24",fontsize=8)

# ── Gráfico 5: Mapa de Remates ───────────────────────────────────────────────
def grafico_remates(df_p, ax):
    draw_half_pitch_horizontal_layout(ax)
    remates = df_p[df_p["Event"].isin(["remate","gol"])].copy()
    for col in ["X","Y"]:
        remates[col] = pd.to_numeric(remates[col],errors="coerce")
    goles=0; no_goles=0
    for _,row in remates.iterrows():
        orig_x,orig_y = float(row["X"]),float(row["Y"])
        if pd.isna(orig_x) or pd.isna(orig_y): continue
        x,y = orig_y,orig_x
        es_gol = (row["Event"]=="gol")
        color="#2E6F40" if es_gol else "#C93B3B"
        if es_gol: goles+=1
        else: no_goles+=1
        ax.scatter(x,y,color=color,marker="o" if es_gol else "x",
                   s=120 if es_gol else 60,zorder=5,
                   alpha=0.9 if es_gol else 0.6,edgecolors="#FAF7F2")
    ax.legend(handles=[
        mpatches.Patch(color="#2E6F40",label=f"Gol ({goles})"),
        mpatches.Patch(color="#C93B3B",label=f"No convirtió ({no_goles})"),
    ],loc="upper left",framealpha=0.9,facecolor="#FAF7F2",
              edgecolor="#7A6A5E",labelcolor="#3D2C24",fontsize=8)

# ── NUEVO Gráfico 6: Acciones Generales (estilo LPF) ─────────────────────────
def grafico_acciones_generales(df_p, ax, fixture_row):
    ax.set_facecolor("#FAF7F2")
    ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # Calcular métricas
    pases_t      = len(df_p[df_p["Event"] == "pase"])
    recup_t      = len(df_p[df_p["Event"] == "recuperacion"])
    perdidas_t   = len(df_p[df_p["Event"] == "perdida"])
    remates_t    = len(df_p[df_p["Event"].isin(["remate", "gol"])])
    faltas_t     = len(df_p[df_p["Event"] == "falta cometida"])
    centros_t    = len(df_p[df_p["Event"] == "centro"])
    despejes_t   = len(df_p[df_p["Event"] == "despeje"])
    conducciones_t = len(df_p[df_p["Event"] == "conduccion"])

    goles_t = 0
    if not fixture_row.empty and str(fixture_row["estado"].values[0]) == "Jugado":
        goles_t = int(fixture_row["goles_favor"].values[0])

    metricas = [
        ("Pases totales",    pases_t,       pases_t      / max(pases_t, 1)),
        ("Recuperaciones",   recup_t,       recup_t      / max(recup_t + perdidas_t, 1)),
        ("Pérdidas",         perdidas_t,    1 - perdidas_t / max(recup_t + perdidas_t, 1)),
        ("Remates",          remates_t,     min(remates_t / 20, 1)),
        ("Goles",            goles_t,       min(goles_t / 5, 1)),
        ("Faltas cometidas", faltas_t,      min(faltas_t / 20, 1)),
        ("Centros",          centros_t,     min(centros_t / 15, 1)),
        ("Despejes",         despejes_t,    min(despejes_t / 30, 1)),
        ("Conducciones",     conducciones_t,min(conducciones_t / 30, 1)),
    ]

    n = len(metricas)
    row_h = 0.085
    y_start = 0.96

    # Encabezados
    ax.text(0.02, y_start, "Métrica",   color="#3D2C24", fontsize=8.5, fontweight="bold", va="top", fontfamily="monospace")
    ax.text(0.52, y_start, "Total",     color="#3D2C24", fontsize=8.5, fontweight="bold", va="top", ha="center", fontfamily="monospace")
    ax.text(0.98, y_start, "",          color="#3D2C24", fontsize=8.5, fontweight="bold", va="top", ha="right",  fontfamily="monospace")
    ax.plot([0.01, 0.99], [y_start - 0.03, y_start - 0.03], color="#7A6A5E", lw=1.2)

    for i, (label, val, prop) in enumerate(metricas):
        y = y_start - 0.03 - (i + 1) * row_h
        # Fondo alternado
        if i % 2 == 0:
            ax.add_patch(mpatches.FancyBboxPatch(
                (0.01, y - 0.01), 0.98, row_h * 0.9,
                boxstyle="round,pad=0.005", facecolor="#EDE8E2", edgecolor="none", zorder=0
            ))
        # Texto label y valor
        ax.text(0.03, y + row_h * 0.35, label, color="#3D2C24", fontsize=8, va="center", fontfamily="monospace")
        ax.text(0.52, y + row_h * 0.35, str(val), color="#8A2525" if (label == "Goles" and val > 0) else "#3D2C24",
                fontsize=9, fontweight="bold", va="center", ha="center", fontfamily="monospace")
        # Mini barra proporcional
        bar_x = 0.60; bar_w_max = 0.37; bar_h = row_h * 0.35
        bar_y = y + row_h * 0.15
        ax.add_patch(mpatches.Rectangle((bar_x, bar_y), bar_w_max, bar_h,
                                         facecolor="#D6CFC7", edgecolor="none", zorder=1))
        fill_color = "#8A2525" if label in ("Pérdidas", "Faltas cometidas", "Despejes") else "#2E6F40"
        ax.add_patch(mpatches.Rectangle((bar_x, bar_y), bar_w_max * prop, bar_h,
                                         facecolor=fill_color, edgecolor="none", zorder=2))

# ── NUEVO Gráfico 7: Pelota Parada ───────────────────────────────────────────
def grafico_pelota_parada(df_p, ax):
    ax.set_facecolor("#FAF7F2")
    ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    tl_t      = len(df_p[df_p["Event"] == "tiro libre"])
    corner_t  = len(df_p[df_p["Event"] == "corner"])
    centro_t  = len(df_p[df_p["Event"] == "centro"])
    remate_t  = len(df_p[df_p["Event"].isin(["remate", "gol"])])
    falta_r_t = len(df_p[df_p["Event"] == "falta recibida"])
    falta_c_t = len(df_p[df_p["Event"] == "falta cometida"])

    metricas = [
        ("Tiros libres",      tl_t,     "#2E6F40"),
        ("Corners",           corner_t, "#2E6F40"),
        ("Centros",           centro_t, "#2E6F40"),
        ("Remates totales",   remate_t, "#2E6F40"),
        ("Faltas recibidas",  falta_r_t,"#2E6F40"),
        ("Faltas cometidas",  falta_c_t,"#8A2525"),
    ]

    maximo = max((v for _, v, _ in metricas), default=1) or 1

    y_start = 0.96
    row_h = 0.12
    ax.text(0.02, y_start, "Pelota Parada", color="#8A2525", fontsize=9, fontweight="bold",
            va="top", fontfamily="serif")
    ax.plot([0.01, 0.99], [y_start - 0.04, y_start - 0.04], color="#7A6A5E", lw=1.2)

    for i, (label, val, color) in enumerate(metricas):
        y = y_start - 0.04 - (i + 1) * row_h
        if i % 2 == 0:
            ax.add_patch(mpatches.FancyBboxPatch(
                (0.01, y - 0.01), 0.98, row_h * 0.88,
                boxstyle="round,pad=0.005", facecolor="#EDE8E2", edgecolor="none", zorder=0
            ))
        ax.text(0.03, y + row_h * 0.38, label, color="#3D2C24", fontsize=8, va="center", fontfamily="monospace")
        ax.text(0.97, y + row_h * 0.38, str(val), color=color, fontsize=9,
                fontweight="bold", va="center", ha="right", fontfamily="monospace")
        # barra
        bar_x = 0.58; bar_w_max = 0.36; bar_h = row_h * 0.32; bar_y = y + row_h * 0.12
        ax.add_patch(mpatches.Rectangle((bar_x, bar_y), bar_w_max, bar_h,
                                         facecolor="#D6CFC7", edgecolor="none", zorder=1))
        ax.add_patch(mpatches.Rectangle((bar_x, bar_y), bar_w_max * (val / maximo), bar_h,
                                         facecolor=color, edgecolor="none", zorder=2, alpha=0.85))

# ── NUEVO Gráfico 8: Top 5 Jugadores ─────────────────────────────────────────
def grafico_top5_jugadores(df_p, ax):
    ax.set_facecolor("#FAF7F2")
    ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # Calcular top 5 para cada categoría
    top_pases = (df_p[df_p["Event"] == "pase"]
                 .groupby("Player").size().sort_values(ascending=False).head(5))
    top_recup = (df_p[df_p["Event"] == "recuperacion"]
                 .groupby("Player").size().sort_values(ascending=False).head(5))
    top_perd  = (df_p[df_p["Event"] == "perdida"]
                 .groupby("Player").size().sort_values(ascending=False).head(5))

    categorias = [
        ("Pases",           top_pases, "#2E6F40"),
        ("Recuperaciones",  top_recup, "#A87D2C"),
        ("Pérdidas",        top_perd,  "#8A2525"),
    ]

    col_w = 1.0 / len(categorias)

    for col_i, (titulo, ranking, color) in enumerate(categorias):
        x_base = col_i * col_w
        x_mid  = x_base + col_w / 2

        # Título de columna
        ax.text(x_mid, 0.97, titulo, color=color, fontsize=9, fontweight="bold",
                ha="center", va="top", fontfamily="serif")
        ax.plot([x_base + 0.01, x_base + col_w - 0.01], [0.90, 0.90], color="#7A6A5E", lw=0.8)

        if ranking.empty:
            ax.text(x_mid, 0.75, "Sin datos", color="#9CA3AF", fontsize=8, ha="center", va="center")
            continue

        max_val = ranking.max() or 1
        row_h = 0.14
        y_start = 0.88

        for rank_i, (jugador, val) in enumerate(ranking.items()):
            y = y_start - rank_i * row_h

            # Número de ranking
            ax.text(x_base + 0.02, y - row_h * 0.1,
                    f"{rank_i + 1}.", color="#9CA3AF", fontsize=7.5,
                    va="top", fontfamily="monospace")

            # Nombre (truncado si es largo)
            nombre_display = str(jugador).title()
            if len(nombre_display) > 13:
                nombre_display = nombre_display[:12] + "."
            ax.text(x_base + 0.07, y - row_h * 0.1,
                    nombre_display, color="#3D2C24", fontsize=8,
                    va="top", fontfamily="monospace")

            # Barra
            bar_x   = x_base + 0.03
            bar_y   = y - row_h * 0.62
            bar_max = col_w - 0.06
            bar_h_px = row_h * 0.28

            ax.add_patch(mpatches.Rectangle(
                (bar_x, bar_y), bar_max, bar_h_px,
                facecolor="#D6CFC7", edgecolor="none", zorder=1
            ))
            ax.add_patch(mpatches.Rectangle(
                (bar_x, bar_y), bar_max * (val / max_val), bar_h_px,
                facecolor=color, edgecolor="none", zorder=2, alpha=0.85
            ))

            # Valor al final de la barra
            ax.text(x_base + col_w - 0.02, y - row_h * 0.48,
                    str(int(val)), color=color, fontsize=8,
                    fontweight="bold", va="center", ha="right", fontfamily="monospace")

        # Separador vertical entre columnas
        if col_i < len(categorias) - 1:
            ax.plot([x_base + col_w - 0.01, x_base + col_w - 0.01], [0.05, 0.95],
                    color="#D6CFC7", lw=0.8, linestyle=":")

# ── Generar Imagen ────────────────────────────────────────────────────────────
def generar_imagen(df_p, rival, condicion, resultado, num_fecha, fixture_row):
    buf = io.BytesIO()
    # Altura aumentada de 18 → 26 para dos filas nuevas
    fig = plt.figure(figsize=(12, 26), facecolor="#FAF7F2")

    pases_t    = len(df_p[df_p["Event"]=="pase"])
    recup_t    = len(df_p[df_p["Event"]=="recuperacion"])
    perdidas_t = len(df_p[df_p["Event"]=="perdida"])
    remates_t  = len(df_p[df_p["Event"].isin(["remate","gol"])])
    goles_t    = int(fixture_row["goles_favor"].values[0]) \
                 if not fixture_row.empty and str(fixture_row["estado"].values[0])=="Jugado" else 0
    faltas_t   = len(df_p[df_p["Event"]=="falta cometida"])
    ratio      = round(pases_t/perdidas_t,1) if perdidas_t>0 else "—"

    # ── Encabezado ────────────────────────────────────────────────────────────
    for escudo_nombre, pos_ax in [("Local",[0.05,0.955,0.05,0.025]),
                                   (rival,  [0.90,0.955,0.05,0.025])]:
        path = buscar_escudo(escudo_nombre)
        if path:
            try:
                img = PILImage.open(path).convert("RGBA")
                a = fig.add_axes(pos_ax); a.imshow(img)
                a.set_aspect("equal"); a.axis("off")
            except: pass

    hax = fig.add_axes([0.05,0.940,0.90,0.055]); hax.axis("off")
    hax.text(0.5,0.70,f"Estrella de Berisso vs {rival}",
             color="#8A2525",fontsize=22,fontweight="bold",
             ha="center",va="center",fontfamily="serif")
    ptxt = f"Fecha {num_fecha}  ·  {condicion}"
    if resultado: ptxt += f"  ·  Resultado: {resultado}"
    hax.text(0.5,0.25,ptxt,color="#3D2C24",fontsize=11,fontweight="bold",
             ha="center",va="center",fontfamily="serif")
    fig.add_axes([0.05,0.937,0.90,0.002],facecolor="#8A2525").axis("off")

    # ── FILA 1: Pases último tercio | Stats | Presión ─────────────────────────
    # Coordenadas Y ajustadas para nuevo figsize (todo comprimido proporcionalmente)
    fig.text(0.05, 0.918,"Pases en el Último Tercio", color="#8A2525",fontsize=11,fontweight="bold",ha="left",fontfamily="serif")
    fig.text(0.415,0.918,"Estadísticas",               color="#3D2C24",fontsize=11,fontweight="bold",ha="left",fontfamily="serif")
    fig.text(0.62, 0.918,"Presión en Campo Rival",     color="#8A2525",fontsize=11,fontweight="bold",ha="left",fontfamily="serif")

    ax_pases   = fig.add_axes([0.05, 0.785, 0.33, 0.130])
    ax_table   = fig.add_axes([0.415,0.785, 0.17, 0.130])
    ax_heatmap = fig.add_axes([0.62, 0.785, 0.33, 0.130])
    grafico_pases_ultimo_tercio(df_p, ax_pases)
    grafico_presion_rival(df_p, ax_heatmap)

    ax_table.axis("off")
    ax_table.text(0.05,0.88,"Métrica",color="#3D2C24",fontsize=9,fontweight="bold",ha="left",fontfamily="monospace")
    ax_table.text(0.95,0.88,"Valor",  color="#3D2C24",fontsize=9,fontweight="bold",ha="right",fontfamily="monospace")
    ax_table.plot([0.01,0.99],[0.82,0.82],color="#7A6A5E",linewidth=1.5)
    kpis = [
        ("Pases",         str(pases_t),   True),
        ("Recuperaciones",str(recup_t),   False),
        ("Pérdidas",      str(perdidas_t),False),
        ("Ratio P/P",     str(ratio),     False),
        ("Remates",       str(remates_t), False),
        ("Goles",         str(goles_t),   goles_t>0),
        ("Faltas",        str(faltas_t),  False),
    ]
    y_val = 0.70
    for label,val,accent in kpis:
        ax_table.text(0.05,y_val,label,color="#3D2C24",fontsize=9,ha="left",fontfamily="monospace")
        ax_table.text(0.95,y_val,val,color="#A83232" if accent else "#3D2C24",
                      fontweight="bold",ha="right",fontfamily="monospace")
        ax_table.plot([0.01,0.99],[y_val-0.05,y_val-0.05],color="#7A6A5E",linewidth=0.5,linestyle=":")
        y_val -= 0.10

    # ── FILA 2: Actividad por minuto ──────────────────────────────────────────
    fig.text(0.05,0.760,"Actividad por Minuto",color="#8A2525",fontsize=11,
             fontweight="bold",ha="left",fontfamily="serif")
    ax_act = fig.add_axes([0.05,0.660,0.90,0.095])
    grafico_actividad(df_p, ax_act)

    # ── FILA 3: Pases largos | Remates ───────────────────────────────────────
    fig.text(0.05,0.638,"Pases Largos al Último Tercio (>30m)",color="#8A2525",fontsize=11,fontweight="bold",ha="left",fontfamily="serif")
    fig.text(0.55,0.638,"Mapa de Remates en el Área",          color="#8A2525",fontsize=11,fontweight="bold",ha="left",fontfamily="serif")

    ax_largos  = fig.add_axes([0.05,0.420,0.40,0.215])
    ax_remates = fig.add_axes([0.55,0.420,0.40,0.215])
    grafico_pases_largos(df_p, ax_largos)
    grafico_remates(df_p, ax_remates)

    # ── Separador ─────────────────────────────────────────────────────────────
    fig.add_axes([0.05,0.408,0.90,0.001],facecolor="#7A6A5E").axis("off")

    # ── FILA 4 NUEVA: Acciones Generales | Pelota Parada ─────────────────────
    fig.text(0.05, 0.400,"Acciones Generales", color="#8A2525",fontsize=11,fontweight="bold",ha="left",fontfamily="serif")
    fig.text(0.55, 0.400,"Pelota Parada",       color="#8A2525",fontsize=11,fontweight="bold",ha="left",fontfamily="serif")

    ax_acciones = fig.add_axes([0.05, 0.240, 0.43, 0.155])
    ax_pp       = fig.add_axes([0.55, 0.240, 0.40, 0.155])
    grafico_acciones_generales(df_p, ax_acciones, fixture_row)
    grafico_pelota_parada(df_p, ax_pp)

    # ── Separador ─────────────────────────────────────────────────────────────
    fig.add_axes([0.05,0.228,0.90,0.001],facecolor="#7A6A5E").axis("off")

    # ── FILA 5 NUEVA: Top 5 Jugadores ────────────────────────────────────────
    fig.text(0.05, 0.220,"Top 5 Jugadores por Acción", color="#8A2525",fontsize=11,fontweight="bold",ha="left",fontfamily="serif")

    ax_top5 = fig.add_axes([0.05, 0.075, 0.90, 0.140])
    grafico_top5_jugadores(df_p, ax_top5)

    # ── Separador y Firma ─────────────────────────────────────────────────────
    fig.add_axes([0.05,0.065,0.90,0.001],facecolor="#7A6A5E").axis("off")

    fig.text(0.05,0.040,"IAO Football Analytics",           color="#8A2525",fontsize=12,ha="left",  va="center",fontweight="bold",fontfamily="serif")
    fig.text(0.05,0.022,"video-analisis-app.streamlit.app", color="#7A6A5E",fontsize=9, ha="left",  va="center",fontfamily="serif")
    fig.text(0.5, 0.031,"IAO",                              color="#8A2525",fontsize=24,ha="center",va="center",fontfamily="serif",fontstyle="italic",fontweight="bold")
    fig.text(0.95,0.031,"Análisis de Video y Datos",        color="#3D2C24",fontsize=10,ha="right", va="center",fontfamily="serif")

    fig.savefig(buf,format="png",dpi=150,bbox_inches="tight",facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf

img_buf = generar_imagen(df_p, rival, condicion, resultado, num_fecha, fixture_row)
st.image(img_buf, use_container_width=True)
