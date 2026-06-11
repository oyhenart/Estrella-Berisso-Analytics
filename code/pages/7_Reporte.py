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
PITCH_BG = "#2D6A4F"

METRICAS_POS = {
    "Arquero":       ["despeje","recuperacion","pase"],
    "Defensor":      ["recuperacion","despeje","falta cometida"],
    "Mediocampista": ["pase","recuperacion","conduccion"],
    "Delantero":     ["remate","gol","centro","conduccion"],
}
COLOR_POS = {"Arquero":"#60A5FA","Defensor":"#34D399",
             "Mediocampista":"#FCD34D","Delantero":"#F87171"}

# ── Helpers ───────────────────────────────────────────────────────────────────
def draw_pitch(ax):
    ax.set_facecolor(PITCH_BG)
    ax.set_xlim(-2, 102); ax.set_ylim(102, -2)
    ax.set_aspect("equal"); ax.axis("off")
    kw = dict(color="white", linewidth=1.2)
    ax.plot([0,W,W,0,0],[0,0,H,H,0], **kw)
    ax.plot([W/2,W/2],[0,H], **kw)
    ax.add_patch(plt.Circle((W/2,H/2), CR, fill=False, **kw))
    ax.plot(W/2, H/2, "o", color="white", markersize=2)
    for x0,x1 in [(0,AG_X),(W-AG_X,W)]:
        ax.plot([x0,x1,x1,x0,x0],
                [(H-AG_Y)/2,(H-AG_Y)/2,(H+AG_Y)/2,(H+AG_Y)/2,(H-AG_Y)/2], **kw)
    for x0,x1 in [(0,AC_X),(W-AC_X,W)]:
        ax.plot([x0,x1,x1,x0,x0],
                [(H-AC_Y)/2,(H-AC_Y)/2,(H+AC_Y)/2,(H+AC_Y)/2,(H-AC_Y)/2], **kw)
    ax.plot([0,0],[(H-ARCO)/2,(H+ARCO)/2], color="white", linewidth=3)
    ax.plot([W,W],[(H-ARCO)/2,(H+ARCO)/2], color="white", linewidth=3)

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
        fig.patch.set_facecolor("#111827")
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
            color = "#34D399" if sig_event not in ["perdida",""] else "#F87171"
            if color == "#34D399": completos += 1
            else: incompletos += 1
            dx, dy = x2 - x1, y2 - y1
            ax.annotate("",
                xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=color,
                    lw=1.2,
                    mutation_scale=10,
                ),
            )
        else:
            # pase sin destino — punto simple
            ax.plot(x1, y1, "o", color="#F87171", markersize=4, alpha=0.6)
            incompletos += 1

    legend = [
        mpatches.Patch(color="#34D399", label=f"Pase completo ({completos})"),
        mpatches.Patch(color="#F87171", label=f"Pase incompleto ({incompletos})"),
    ]
    ax.legend(handles=legend, loc="upper left", framealpha=0.3,
              facecolor="#1F2937", edgecolor="none", labelcolor="white", fontsize=8)
    if is_standalone:
        ax.set_title("Mapa de pases", color="white", fontsize=11, pad=8)
    return fig

# ── Gráfico 2: Heatmap ────────────────────────────────────────────────────────
def grafico_heatmap(df_p, ax=None):
    is_standalone = ax is None
    if is_standalone:
        fig, ax = plt.subplots(figsize=(10, 6.9))
        fig.patch.set_facecolor("#111827")
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
        "heat", [(0,"none"),(0.01,"#FFFF0088"),(0.5,"#FF8C00BB"),(1,"#C80000DD")])
    xc = [(xs[i]+xs[i+1])/2 for i in range(nx)]
    yc = [(ys[i]+ys[i+1])/2 for i in range(ny)]
    ax.pcolormesh(xc, yc, grid, cmap=cmap, shading="nearest", zorder=2, alpha=0.8)
    if is_standalone:
        ax.set_title("Zonas de actividad", color="white", fontsize=11, pad=8)
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
        fig.patch.set_facecolor("#111827")
    else:
        fig = axes[0].figure
    for i, (jugador, pos, score, met) in enumerate(top3):
        ax = axes[i]
        ax.set_facecolor("#1F2937")
        dj   = df_p[df_p["Player"] == jugador]
        vals = [len(dj[dj["Event"] == m]) for m in met[:4]]
        labs = [m.capitalize() for m in met[:4]]
        color = COLOR_POS.get(pos, "#9CA3AF")
        bars = ax.barh(labs, vals, color=color, alpha=0.85)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_width()+0.1, bar.get_y()+bar.get_height()/2,
                    str(val), va="center", color="white", fontsize=9)
        ax.set_title(f"{jugador}\n{pos or '—'}", color="white", fontsize=9, pad=6)
        ax.tick_params(colors="white", labelsize=8)
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.set_xlim(0, max(vals or [1]) * 1.35)
    if is_standalone:
        fig.suptitle("Protagonistas del partido", color="white", fontsize=12, y=1.02)
        fig.tight_layout()
    return fig

# ── Gráfico 4: Actividad por minuto ──────────────────────────────────────────
def grafico_actividad(df_p, ax=None):
    is_standalone = ax is None
    if is_standalone:
        fig, ax = plt.subplots(figsize=(10, 3))
        fig.patch.set_facecolor("#111827")
    else:
        fig = ax.figure
    ax.set_facecolor("#1F2937")
    act = df_p.groupby("Mins")["Event"].count()
    ax.bar(act.index.astype(float), act.values, color="#374151", width=0.8)
    ax.axvline(45, color="#E23E3E", linestyle="--", linewidth=1, alpha=0.7, label="HT")
    ax.set_xlabel("Minuto", color="white", fontsize=9)
    ax.set_ylabel("Eventos", color="white", fontsize=9)
    if is_standalone:
        ax.set_title("Actividad por minuto", color="white", fontsize=11)
    ax.tick_params(colors="white", labelsize=8)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.legend(facecolor="#1F2937", edgecolor="none", labelcolor="white", fontsize=8)
    if is_standalone:
        fig.tight_layout()
    return fig

# ── Preview en pantalla ───────────────────────────────────────────────────────
def mostrar_preview(df_p, pos_map):
    pases_t    = len(df_p[df_p["Event"] == "pase"])
    recup_t    = len(df_p[df_p["Event"] == "recuperacion"])
    perdidas_t = len(df_p[df_p["Event"] == "perdida"])
    remates_t  = len(df_p[df_p["Event"] == "remate"])
    goles_t    = len(df_p[df_p["Event"] == "gol"])
    faltas_t   = len(df_p[df_p["Event"] == "falta cometida"])
    ratio      = round(pases_t / perdidas_t, 1) if perdidas_t > 0 else "—"

    def kpi(label, value, accent=False):
        c = "#E23E3E" if accent else "#F9FAFB"
        return f"<div style='background:#1F2937;border-left:3px solid {'#E23E3E' if accent else '#374151'};border-radius:4px;padding:12px 16px;text-align:center'><div style='font-size:0.6em;color:#6B7280;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px'>{label}</div><div style='font-size:1.8em;font-weight:800;color:{c}'>{value}</div></div>"

    c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
    c1.markdown(kpi("Pases", pases_t, True), unsafe_allow_html=True)
    c2.markdown(kpi("Recuperaciones", recup_t), unsafe_allow_html=True)
    c3.markdown(kpi("Pérdidas", perdidas_t), unsafe_allow_html=True)
    c4.markdown(kpi("Ratio P/P", ratio), unsafe_allow_html=True)
    c5.markdown(kpi("Remates", remates_t), unsafe_allow_html=True)
    c6.markdown(kpi("Goles", goles_t, goles_t > 0), unsafe_allow_html=True)
    c7.markdown(kpi("Faltas", faltas_t), unsafe_allow_html=True)

    st.markdown("<div style='margin:20px 0'></div>", unsafe_allow_html=True)

    col_izq, col_der = st.columns(2)
    with col_izq:
        st.markdown("<p style='font-size:0.65em;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:3px;margin-bottom:8px'>Mapa de pases</p>", unsafe_allow_html=True)
        fig1 = grafico_pases(df_p)
        st.pyplot(fig1)
    with col_der:
        st.markdown("<p style='font-size:0.65em;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:3px;margin-bottom:8px'>Zonas de actividad</p>", unsafe_allow_html=True)
        fig2 = grafico_heatmap(df_p)
        st.pyplot(fig2)

    st.markdown("<p style='font-size:0.65em;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:3px;margin:20px 0 8px 0'>Protagonistas del partido</p>", unsafe_allow_html=True)
    fig3 = grafico_protagonistas(df_p, pos_map)
    st.pyplot(fig3)

    st.markdown("<p style='font-size:0.65em;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:3px;margin:20px 0 8px 0'>Actividad por minuto</p>", unsafe_allow_html=True)
    fig4 = grafico_actividad(df_p)
    st.pyplot(fig4)

# ── Generar Imagen ────────────────────────────────────────────────────────────
def generar_imagen(df_p, rival, condicion, resultado, pos_map, num_fecha):
    buf = io.BytesIO()
    # Formato vertical de alta resolución: 12 pulgadas de ancho, 28 de alto
    fig = plt.figure(figsize=(12, 28), facecolor="#111827")
    
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
    header_ax = fig.add_axes([0.05, 0.925, 0.90, 0.05])
    header_ax.axis("off")
    
    title_x = 0.05
    if os.path.exists(ESCUDO_PATH):
        try:
            from PIL import Image as PILImage
            img = PILImage.open(ESCUDO_PATH)
            logo_ax = fig.add_axes([0.05, 0.925, 0.06, 0.05])
            logo_ax.imshow(img)
            logo_ax.axis("off")
            title_x = 0.13
        except Exception:
            pass

    header_ax.text(title_x, 0.65, "CLUB ATLÉTICO ESTRELLA DE BERISSO", 
                   color="#F9FAFB", fontsize=18, fontweight="bold", ha="left", va="center")
    header_ax.text(title_x, 0.25, "Reporte Post-Partido", 
                   color="#E23E3E", fontsize=13, fontweight="bold", ha="left", va="center")
    
    partido_txt = f"Fecha {num_fecha}  ·  vs {rival}  ·  {condicion}"
    if resultado: partido_txt += f"  ·  {resultado}"
    header_ax.text(0.95, 0.45, partido_txt, 
                   color="#9CA3AF", fontsize=11, fontweight="bold", ha="right", va="center")

    # Línea divisoria roja
    fig.add_axes([0.05, 0.915, 0.90, 0.002], facecolor="#E23E3E").axis("off")

    # 2. KPIs
    kpi_ax = fig.add_axes([0.05, 0.84, 0.90, 0.06])
    kpi_ax.axis("off")
    kpis = [
        ("PASES", str(pases_t), True),
        ("RECUPERACIONES", str(recup_t), False),
        ("PÉRDIDAS", str(perdidas_t), False),
        ("RATIO P/P", str(ratio), False),
        ("REMATES", str(remates_t), False),
        ("GOLES", str(goles_t), goles_t > 0),
        ("FALTAS", str(faltas_t), False)
    ]
    import matplotlib.patches as patches
    for idx, (label, val, accent) in enumerate(kpis):
        x_start = idx / 7.0 + 0.005
        x_width = 1.0 / 7.0 - 0.01
        
        rect = patches.FancyBboxPatch(
            (x_start, 0.05), x_width, 0.9,
            boxstyle="round,pad=0.01",
            facecolor="#1F2937", edgecolor="#374151", linewidth=1
        )
        kpi_ax.add_patch(rect)
        
        kpi_ax.text(
            x_start + x_width/2, 0.65, label,
            color="#9CA3AF", fontsize=8, ha="center", va="center", fontweight="bold"
        )
        val_color = "#E23E3E" if accent else "#F9FAFB"
        kpi_ax.text(
            x_start + x_width/2, 0.3, val,
            color=val_color, fontsize=16, ha="center", va="center", fontweight="bold"
        )

    # Título Sección 1
    fig.text(0.05, 0.815, "Análisis de pases y zonas", color="#E23E3E", fontsize=13, fontweight="bold")

    # 3. Gráficos de pases y heatmap
    ax_pases = fig.add_axes([0.05, 0.52, 0.43, 0.28])
    ax_heatmap = fig.add_axes([0.52, 0.52, 0.43, 0.28])
    grafico_pases(df_p, ax=ax_pases)
    grafico_heatmap(df_p, ax=ax_heatmap)

    # Título Sección 2
    fig.text(0.05, 0.495, "Protagonistas del partido", color="#E23E3E", fontsize=13, fontweight="bold")

    # 4. Protagonistas
    ax_prot1 = fig.add_axes([0.05, 0.36, 0.27, 0.12])
    ax_prot2 = fig.add_axes([0.365, 0.36, 0.27, 0.12])
    ax_prot3 = fig.add_axes([0.68, 0.36, 0.27, 0.12])
    grafico_protagonistas(df_p, pos_map, axes=[ax_prot1, ax_prot2, ax_prot3])

    # Título Sección 3
    fig.text(0.05, 0.325, "Actividad por minuto", color="#E23E3E", fontsize=13, fontweight="bold")

    # 5. Actividad por minuto
    ax_actividad = fig.add_axes([0.05, 0.21, 0.90, 0.10])
    grafico_actividad(df_p, ax=ax_actividad)

    # Título Sección 4
    fig.text(0.05, 0.185, "Observaciones del analista", color="#E23E3E", fontsize=13, fontweight="bold")

    # 6. Observaciones
    obs_ax = fig.add_axes([0.05, 0.05, 0.90, 0.125])
    obs_ax.axis("off")
    rect_obs = patches.FancyBboxPatch(
        (0.0, 0.05), 1.0, 0.9,
        boxstyle="round,pad=0.01",
        facecolor="#1F2937", edgecolor="#374151", linewidth=1
    )
    obs_ax.add_patch(rect_obs)
    
    y_pos = 0.80
    for o in obs:
        obs_ax.text(
            0.03, y_pos, o,
            color="#F9FAFB", fontsize=11, ha="left", va="center"
        )
        y_pos -= 0.18

    # Línea divisoria inferior
    fig.add_axes([0.05, 0.04, 0.90, 0.001], facecolor="#374151").axis("off")

    # 7. Firma / Pie de página
    fig.text(0.5, 0.024, "IAO Footbal Analytics", color="#E23E3E", fontsize=13, ha="center", va="center", fontweight="bold")
    fig.text(0.5, 0.012, "Transformo datos en decisiones.", color="#9CA3AF", fontsize=9, ha="center", va="center", style="italic")

    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf

# ── UI principal ──────────────────────────────────────────────────────────────
col_prev, col_gen = st.columns([1, 1])

with col_prev:
    if st.button("👁 Ver preview", use_container_width=True):
        st.session_state["mostrar_preview"] = True

with col_gen:
    if st.button("🖼 Generar Imagen", type="primary", use_container_width=True):
        with st.spinner("Generando imagen..."):
            img_buf = generar_imagen(df_p, rival, condicion, resultado, pos_map, num_fecha)
        nombre = f"reporte_estrella_f{num_fecha}_vs_{rival.replace(' ','_').lower()}.png"
        st.download_button("⬇ Descargar Imagen", data=img_buf,
                           file_name=nombre, mime="image/png")
        st.success(f"Listo — {nombre}")

if st.session_state.get("mostrar_preview"):
    st.markdown("<div style='margin:20px 0;height:1px;background:#1F2937'></div>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.65em;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:3px;margin-bottom:16px'>Preview del reporte</p>", unsafe_allow_html=True)
    mostrar_preview(df_p, pos_map)
