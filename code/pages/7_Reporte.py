import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from components.layout import inject_css, render_sidebar

st.set_page_config(page_title="Reporte PDF", page_icon="📄", layout="wide")
inject_css()

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
render_sidebar(BASE)

DATA_PATH    = os.path.join(BASE, "data", "events_clean.csv")
FIXTURE_PATH = os.path.join(BASE, "data", "fixture.csv")
JUGADORES_PATH = os.path.join(BASE, "data", "Jugadores.csv")
ESCUDO_PATH  = os.path.join(BASE, "static", "escudo.png")

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
    df = pd.read_csv(DATA_PATH)
    return df

@st.cache_data(ttl=0)
def cargar_fixture():
    return pd.read_csv(FIXTURE_PATH)

@st.cache_data(ttl=0)
def cargar_jugadores():
    df = pd.read_csv(JUGADORES_PATH)
    df["nombre"] = df["nombre"].str.strip().str.title()
    df["posicion"] = df["posicion"].str.strip().str.title()
    return df

df = cargar_datos()
fixture = cargar_fixture()
jugadores_df = cargar_jugadores()
pos_map = dict(zip(jugadores_df["nombre"], jugadores_df["posicion"]))

# ── Selector de fecha ─────────────────────────────────────────────────────────
fechas = sorted(df["fecha"].unique().tolist())
fecha_sel = st.selectbox("Seleccioná el partido", [f"Fecha {f}" for f in fechas])
num_fecha = int(fecha_sel.replace("Fecha ", ""))

df_p = df[df["fecha"] == num_fecha].copy()
fixture_row = fixture[fixture["fecha"] == num_fecha]
rival = fixture_row["rival"].values[0] if not fixture_row.empty else "Rival"
condicion = fixture_row["condicion"].values[0] if not fixture_row.empty else ""
resultado = ""
if not fixture_row.empty and fixture_row["estado"].values[0] == "Jugado":
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

# ── Funciones de gráficos ─────────────────────────────────────────────────────
PITCH_COLOR = "#2D6A4F"
LINE_COLOR  = "white"
W, H = 100, 100
AG_X=12.7; AG_Y=44.8; AC_X=4.2; AC_Y=20.4; ARCO=8.1; CR=7.0

def draw_pitch(ax, color=PITCH_COLOR):
    ax.set_facecolor(color)
    ax.set_xlim(-2, 102); ax.set_ylim(102, -2)
    ax.set_aspect("equal"); ax.axis("off")
    kw = dict(color=LINE_COLOR, linewidth=1.2)
    ax.plot([0,W,W,0,0], [0,0,H,H,0], **kw)
    ax.plot([W/2,W/2], [0,H], **kw)
    circle = plt.Circle((W/2, H/2), CR, fill=False, **kw)
    ax.add_patch(circle)
    ax.plot([W/2], [H/2], 'o', color=LINE_COLOR, markersize=2)
    for x0, x1 in [(0, AG_X), (W-AG_X, W)]:
        ax.plot([x0,x1,x1,x0,x0],
                [(H-AG_Y)/2, (H-AG_Y)/2, (H+AG_Y)/2, (H+AG_Y)/2, (H-AG_Y)/2], **kw)
    for x0, x1 in [(0, AC_X), (W-AC_X, W)]:
        ax.plot([x0,x1,x1,x0,x0],
                [(H-AC_Y)/2, (H-AC_Y)/2, (H+AC_Y)/2, (H+AC_Y)/2, (H-AC_Y)/2], **kw)
    ax.plot([0,0], [(H-ARCO)/2, (H+ARCO)/2], color=LINE_COLOR, linewidth=3)
    ax.plot([W,W], [(H-ARCO)/2, (H+ARCO)/2], color=LINE_COLOR, linewidth=3)

def fig_to_img(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf

def grafico_pases(df_p):
    pases = df_p[df_p["Event"] == "pase"].copy()
    perdidas = df_p[df_p["Event"] == "perdida"].copy()

    fig, ax = plt.subplots(figsize=(10, 6.9))
    fig.patch.set_facecolor("#111827")
    draw_pitch(ax)

    # Pases completos (verde) — pase seguido de recepción de compañero
    completados, incompletos = [], []
    indices = pases.index.tolist()
    for idx in indices:
        pos = df_p.index.get_loc(idx)
        if pos + 1 < len(df_p):
            sig = df_p.iloc[pos + 1]
            if sig["Event"] == "recuperacion" or (pd.notna(df_p.iloc[pos]["X2"])):
                completados.append(idx)
            else:
                incompletos.append(idx)
        else:
            incompletos.append(idx)

    for idx in completados:
        row = df_p.loc[idx]
        if pd.notna(row["X2"]) and pd.notna(row["Y2"]):
            ax.annotate("", xy=(row["X2"], row["Y2"]), xytext=(row["X"], row["Y"]),
                        arrowprops=dict(arrowstyle="-|>", color="#34D399", lw=1.2))
    for idx in incompletos:
        row = df_p.loc[idx]
        if pd.notna(row["X2"]) and pd.notna(row["Y2"]):
            ax.annotate("", xy=(row["X2"], row["Y2"]), xytext=(row["X"], row["Y"]),
                        arrowprops=dict(arrowstyle="-|>", color="#F87171", lw=1.2))

    legend = [
        mpatches.Patch(color="#34D399", label=f"Pase completo ({len(completados)})"),
        mpatches.Patch(color="#F87171", label=f"Pase incompleto ({len(incompletos)})"),
    ]
    ax.legend(handles=legend, loc="upper left", framealpha=0.3,
              facecolor="#1F2937", edgecolor="none", labelcolor="white", fontsize=8)
    ax.set_title("Mapa de pases", color="white", fontsize=11, pad=8)
    fig.tight_layout()
    return fig_to_img(fig)

def grafico_heatmap(df_p):
    fig, ax = plt.subplots(figsize=(10, 6.9))
    fig.patch.set_facecolor("#111827")
    draw_pitch(ax)

    nx, ny = 13, 9
    xs = np.linspace(0, W, nx+1); ys = np.linspace(0, H, ny+1)
    grid = np.zeros((ny, nx))
    for _, row in df_p.iterrows():
        if pd.notna(row["X"]) and pd.notna(row["Y"]):
            xi = min(int(row["X"] / W * nx), nx-1)
            yi = min(int(row["Y"] / H * ny), ny-1)
            grid[yi, xi] += 1

    xc = [(xs[i]+xs[i+1])/2 for i in range(nx)]
    yc = [(ys[i]+ys[i+1])/2 for i in range(ny)]
    ax.pcolormesh(xc, yc, grid,
                  cmap=matplotlib.colors.LinearSegmentedColormap.from_list(
                      "heat", ["none","#FFFF0088","#FF8C00BB","#C80000DD"]),
                  shading="nearest", zorder=2, alpha=0.8)
    ax.set_title("Zonas de actividad", color="white", fontsize=11, pad=8)
    fig.tight_layout()
    return fig_to_img(fig)

def grafico_protagonistas(df_p, pos_map):
    METRICAS = {
        "Arquero":       ["despeje","recuperacion","pase"],
        "Defensor":      ["recuperacion","despeje","falta cometida"],
        "Mediocampista": ["pase","recuperacion","conduccion"],
        "Delantero":     ["remate","gol","centro","conduccion"],
    }
    COLORES = {"Arquero":"#60A5FA","Defensor":"#34D399",
               "Mediocampista":"#FCD34D","Delantero":"#F87171"}

    jugadores_top = []
    for jugador in df_p["Player"].unique():
        dj = df_p[df_p["Player"] == jugador]
        pos = pos_map.get(jugador, "")
        metricas = METRICAS.get(pos, ["pase","recuperacion","remate"])
        score = sum(len(dj[dj["Event"] == m]) for m in metricas)
        jugadores_top.append((jugador, pos, score, metricas, len(dj)))
    jugadores_top.sort(key=lambda x: x[2], reverse=True)
    top3 = jugadores_top[:3]

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    fig.patch.set_facecolor("#111827")

    for i, (jugador, pos, score, metricas, total) in enumerate(top3):
        ax = axes[i]
        ax.set_facecolor("#1F2937")
        dj = df_p[df_p["Player"] == jugador]
        vals = [len(dj[dj["Event"] == m]) for m in metricas[:4]]
        labels = [m.capitalize() for m in metricas[:4]]
        color = COLORES.get(pos, "#9CA3AF")
        bars = ax.barh(labels, vals, color=color, alpha=0.8)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                    str(val), va="center", color="white", fontsize=9)
        ax.set_title(f"{jugador}\n{pos or '—'}", color="white", fontsize=9, pad=6)
        ax.tick_params(colors="white", labelsize=8)
        ax.spines[:].set_visible(False)
        ax.set_xlim(0, max(vals or [1]) * 1.3)
        for spine in ax.spines.values():
            spine.set_edgecolor("#374151")

    fig.suptitle("Protagonistas del partido", color="white", fontsize=12, y=1.02)
    fig.tight_layout()
    return fig_to_img(fig)

def grafico_actividad(df_p):
    fig, ax = plt.subplots(figsize=(10, 3))
    fig.patch.set_facecolor("#111827")
    ax.set_facecolor("#1F2937")
    act = df_p.groupby("Mins")["Event"].count()
    ax.bar(act.index, act.values, color="#374151", width=0.8)
    ax.axvline(45, color="#E23E3E", linestyle="--", linewidth=1, alpha=0.7, label="HT")
    ax.set_xlabel("Minuto", color="white", fontsize=9)
    ax.set_ylabel("Eventos", color="white", fontsize=9)
    ax.set_title("Actividad por minuto", color="white", fontsize=11)
    ax.tick_params(colors="white", labelsize=8)
    ax.spines[:].set_visible(False)
    ax.legend(facecolor="#1F2937", edgecolor="none", labelcolor="white", fontsize=8)
    fig.tight_layout()
    return fig_to_img(fig)

# ── Generar PDF ───────────────────────────────────────────────────────────────
def generar_pdf(df_p, fixture_row, rival, condicion, resultado, pos_map):
    buf = io.BytesIO()

    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=1.5*cm, rightMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    DARK   = colors.HexColor("#111827")
    ACCENT = colors.HexColor("#E23E3E")
    LIGHT  = colors.HexColor("#F9FAFB")
    MUTED  = colors.HexColor("#6B7280")

    title_style = ParagraphStyle("title", parent=styles["Normal"],
                                  fontSize=20, fontName="Helvetica-Bold",
                                  textColor=LIGHT, spaceAfter=4)
    sub_style   = ParagraphStyle("sub", parent=styles["Normal"],
                                  fontSize=10, fontName="Helvetica",
                                  textColor=MUTED, spaceAfter=12)
    section_style = ParagraphStyle("section", parent=styles["Normal"],
                                    fontSize=11, fontName="Helvetica-Bold",
                                    textColor=ACCENT, spaceBefore=14, spaceAfter=6)
    body_style  = ParagraphStyle("body", parent=styles["Normal"],
                                  fontSize=9, fontName="Helvetica",
                                  textColor=LIGHT, spaceAfter=4)

    story = []

    # Header
    header_data = [["", "Club Atlético Estrella de Berisso\nReporte Post-Partido"]]
    if os.path.exists(ESCUDO_PATH):
        escudo = RLImage(ESCUDO_PATH, width=1.5*cm, height=1.5*cm)
        header_data = [[escudo, Paragraph(
            "<b>Club Atlético Estrella de Berisso</b><br/>Reporte Post-Partido",
            ParagraphStyle("h", fontSize=14, fontName="Helvetica-Bold",
                           textColor=LIGHT, leading=18))]]

    header_table = Table(header_data, colWidths=[2*cm, 14*cm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#1F2937")),
        ("ROUNDEDCORNERS", [4]),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3*cm))

    # Datos del partido
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.2*cm))

    partido_info = f"<b>Fecha {num_fecha}</b> &nbsp;·&nbsp; Estrella de Berisso vs {rival} &nbsp;·&nbsp; {condicion}"
    if resultado:
        partido_info += f" &nbsp;·&nbsp; <b>{resultado}</b>"
    story.append(Paragraph(partido_info, body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#374151")))
    story.append(Spacer(1, 0.3*cm))

    # KPIs resumen
    pases_t    = len(df_p[df_p["Event"] == "pase"])
    recup_t    = len(df_p[df_p["Event"] == "recuperacion"])
    perdidas_t = len(df_p[df_p["Event"] == "perdida"])
    remates_t  = len(df_p[df_p["Event"] == "remate"])
    goles_t    = len(df_p[df_p["Event"] == "gol"])
    faltas_t   = len(df_p[df_p["Event"] == "falta cometida"])
    ratio      = round(pases_t / perdidas_t, 1) if perdidas_t > 0 else "—"

    kpi_data = [
        ["Pases", "Recuperaciones", "Pérdidas", "Ratio P/P", "Remates", "Goles", "Faltas"],
        [str(pases_t), str(recup_t), str(perdidas_t), str(ratio), str(remates_t), str(goles_t), str(faltas_t)],
    ]
    kpi_table = Table(kpi_data, colWidths=[2.6*cm]*7)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1F2937")),
        ("BACKGROUND", (0,1), (-1,1), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#6B7280")),
        ("TEXTCOLOR", (0,1), (-1,1), LIGHT),
        ("FONTNAME",  (0,0), (-1,0), "Helvetica"),
        ("FONTNAME",  (0,1), (-1,1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,0), 7),
        ("FONTSIZE",  (0,1), (-1,1), 14),
        ("ALIGN",     (0,0), (-1,-1), "CENTER"),
        ("VALIGN",    (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("GRID",      (0,0), (-1,-1), 0.5, colors.HexColor("#374151")),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.4*cm))

    # Sección ofensiva
    story.append(Paragraph("Análisis ofensivo", section_style))
    img_pases = grafico_pases(df_p)
    story.append(RLImage(img_pases, width=17*cm, height=11.7*cm))
    story.append(Spacer(1, 0.3*cm))

    # Sección defensiva
    story.append(Paragraph("Zonas de actividad", section_style))
    img_heat = grafico_heatmap(df_p)
    story.append(RLImage(img_heat, width=17*cm, height=11.7*cm))
    story.append(Spacer(1, 0.3*cm))

    # Protagonistas
    story.append(Paragraph("Protagonistas del partido", section_style))
    img_top = grafico_protagonistas(df_p, pos_map)
    story.append(RLImage(img_top, width=17*cm, height=5.7*cm))
    story.append(Spacer(1, 0.3*cm))

    # Actividad por minuto
    story.append(Paragraph("Actividad por minuto", section_style))
    img_act = grafico_actividad(df_p)
    story.append(RLImage(img_act, width=17*cm, height=5*cm))
    story.append(Spacer(1, 0.3*cm))

    # Sugerencias automáticas
    story.append(Paragraph("Observaciones del analista", section_style))
    obs = []
    if ratio != "—" and float(ratio) < 3:
        obs.append("• Ratio pase/pérdida bajo. Se recomienda trabajar la salida desde el fondo y los circuitos de circulación.")
    elif ratio != "—" and float(ratio) >= 5:
        obs.append("• Buen cuidado de la pelota. El equipo mantuvo la posesión con criterio.")
    despejes = len(df_p[df_p["Event"] == "despeje"])
    if despejes > 15:
        obs.append(f"• {despejes} despejes registrados. El equipo estuvo bajo presión. Revisar el bloque defensivo.")
    if faltas_t > 8:
        obs.append(f"• {faltas_t} faltas cometidas. Riesgo disciplinario elevado.")
    if remates_t >= 3:
        obs.append(f"• {remates_t} remates generados. {'Buena llegada al área rival.' if remates_t >= 5 else 'Llegada escasa al área rival.'}")
    if not obs:
        obs.append("• Sin alertas tácticas relevantes en este partido.")

    for o in obs:
        story.append(Paragraph(o, body_style))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#374151")))
    story.append(Paragraph("IAO Football Analytics · Transformo datos en decisiones.",
                            ParagraphStyle("footer", fontSize=7, textColor=MUTED,
                                           alignment=TA_CENTER, spaceBefore=6)))

    doc.build(story)
    buf.seek(0)
    return buf

# ── UI ────────────────────────────────────────────────────────────────────────
if st.button("📄 Generar reporte PDF", type="primary"):
    with st.spinner("Generando reporte..."):
        pdf_buf = generar_pdf(df_p, fixture_row, rival, condicion, resultado, pos_map)

    nombre_archivo = f"reporte_estrella_fecha{num_fecha}_vs_{rival.replace(' ','_').lower()}.pdf"
    st.download_button(
        label="⬇ Descargar PDF",
        data=pdf_buf,
        file_name=nombre_archivo,
        mime="application/pdf",
    )
    st.success(f"Reporte generado — {nombre_archivo}")