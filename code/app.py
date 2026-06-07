import streamlit as st
import pandas as pd
import os
from datetime import date
from components.layout import inject_css, render_sidebar, render_header

st.set_page_config(
    page_title="Estrella FC · Dashboard",
    page_icon="⚽",
    layout="wide"
)

inject_css()

BASE = os.path.dirname(os.path.abspath(__file__))
render_sidebar(BASE)
render_header("Torneo Promocional Amateur 2026", "Panel de análisis")

DATA_PATH    = os.path.join(BASE, "data", "events_clean.csv")
FIXTURE_PATH = os.path.join(BASE, "data", "fixture.csv")
ALERTAS_PATH = os.path.join(BASE, "data", "sanciones_lesiones.csv")

@st.cache_data
def cargar_datos():
    df = pd.read_csv(DATA_PATH)
    df["tiempo_total"] = df["Mins"] * 60 + df["Secs"]
    return df

@st.cache_data(ttl=0)
def cargar_fixture():
    return pd.read_csv(FIXTURE_PATH)

@st.cache_data(ttl=0)
def cargar_alertas():
    df = pd.read_csv(ALERTAS_PATH)
    if not df.empty:
        df["fecha_regreso"] = pd.to_datetime(df["fecha_regreso"], dayfirst=True, errors="coerce")
    return df

fixture = cargar_fixture()
alertas = cargar_alertas()
hoy     = pd.Timestamp(date.today())

# ── Helpers visuales ──────────────────────────────────────────────────────────
def card(label, value, sub=None, accent=False):
    border = "#E23E3E" if accent else "#374151"
    val_color = "#E23E3E" if accent else "#F9FAFB"
    sub_html = f"<div style='font-size:0.72em;color:#6B7280;margin-top:4px'>{sub}</div>" if sub else ""
    return f"""
    <div style='background:#1F2937;border-left:3px solid {border};
                border-radius:4px;padding:14px 18px;height:100%'>
        <div style='font-size:0.6em;color:#6B7280;text-transform:uppercase;
                    letter-spacing:2px;margin-bottom:6px'>{label}</div>
        <div style='font-size:1.8em;font-weight:800;color:{val_color};
                    letter-spacing:-0.5px;line-height:1'>{value}</div>
        {sub_html}
    </div>"""

def section(title):
    st.markdown(f"""
    <p style='font-size:0.65em;font-weight:600;color:#6B7280;
              text-transform:uppercase;letter-spacing:3px;margin:0 0 12px 0'>
        {title}
    </p>""", unsafe_allow_html=True)

def divider():
    st.markdown("<div style='margin:24px 0;height:1px;background:#1F2937'></div>",
                unsafe_allow_html=True)

# ── Estado en el torneo ───────────────────────────────────────────────────────
jugados   = fixture[fixture["estado"] == "Jugado"]
pendientes= fixture[fixture["estado"] == "Pendiente"]

ganados   = len(jugados[jugados["goles_favor"] > jugados["goles_contra"]])
empatados = len(jugados[jugados["goles_favor"] == jugados["goles_contra"]])
perdidos  = len(jugados[jugados["goles_favor"] < jugados["goles_contra"]])
puntos    = ganados * 3 + empatados
gf = int(jugados["goles_favor"].sum())  if not jugados.empty else 0
gc = int(jugados["goles_contra"].sum()) if not jugados.empty else 0

def racha_badges(jugados):
    if jugados.empty:
        return "<span style='color:#6B7280'>Sin partidos jugados</span>"
    colores = {"W": "#34D399", "D": "#FCD34D", "L": "#F87171"}
    badges = ""
    for _, r in jugados.tail(3).iterrows():
        if r["goles_favor"] > r["goles_contra"]:   res = "W"
        elif r["goles_favor"] == r["goles_contra"]: res = "D"
        else:                                        res = "L"
        badges += f"<span style='background:{colores[res]};color:#111827;font-size:0.72em;font-weight:700;padding:3px 9px;border-radius:3px;margin-right:4px'>{res}</span>"
    return badges

section("Estado en el torneo")

if jugados.empty:
    st.markdown("<div style='background:#1F2937;border-left:3px solid #374151;border-radius:4px;padding:14px 18px;color:#6B7280'>Aún no se jugaron partidos.</div>", unsafe_allow_html=True)
else:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(card("Puntos", puntos, accent=True), unsafe_allow_html=True)
    c2.markdown(card("Partidos", f"{ganados}G · {empatados}E · {perdidos}P"), unsafe_allow_html=True)
    c3.markdown(card("Goles", f"{gf} — {gc}", sub="favor — contra"), unsafe_allow_html=True)
    c4.markdown(card("Diferencia", f"{gf-gc:+d}", accent=(gf >= gc)), unsafe_allow_html=True)
    c5.markdown(f"""
    <div style='background:#1F2937;border-left:3px solid #374151;border-radius:4px;padding:14px 18px'>
        <div style='font-size:0.6em;color:#6B7280;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px'>Racha</div>
        {racha_badges(jugados)}
    </div>""", unsafe_allow_html=True)

divider()

# ── Próximo partido + disponibilidad ─────────────────────────────────────────
col_prox, col_disp = st.columns([1, 1])

with col_prox:
    section("Próximo partido")
    if pendientes.empty:
        st.markdown("<div style='background:#1F2937;border-left:3px solid #374151;border-radius:4px;padding:14px 18px;color:#6B7280'>No hay partidos pendientes.</div>", unsafe_allow_html=True)
    else:
        p = pendientes.iloc[0]
        icono = "🏠" if p["condicion"] == "Local" else "✈️"
        color_cond = "#34D399" if p["condicion"] == "Local" else "#60A5FA"
        st.markdown(f"""
        <div style='background:#1F2937;border-radius:6px;padding:20px 24px'>
            <div style='font-size:0.62em;color:#6B7280;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px'>Fecha {int(p["fecha"])}</div>
            <div style='font-size:1.4em;font-weight:800;color:#F9FAFB;margin-bottom:10px'>
                {icono} vs <span style='color:#E23E3E'>{p["rival"]}</span>
            </div>
            <span style='background:{color_cond}22;color:{color_cond};font-size:0.72em;font-weight:600;padding:3px 10px;border-radius:3px;letter-spacing:1px'>{p["condicion"]}</span>
        </div>""", unsafe_allow_html=True)

with col_disp:
    section("Disponibilidad del plantel")
    bajas_tipos = ["lesión","lesion","sanción","sancion","roja directa"]
    bajas = alertas[alertas["tipo"].str.lower().isin(bajas_tipos)] if not alertas.empty else pd.DataFrame()
    bajas_activas = bajas[bajas["fecha_regreso"].isna() | (bajas["fecha_regreso"] >= hoy)] if not bajas.empty else pd.DataFrame()

    amarillas = alertas[alertas["tipo"].str.lower() == "amarilla"] if not alertas.empty else pd.DataFrame()
    en_riesgo = []
    if not amarillas.empty:
        for jugador, grupo in amarillas.groupby("nombre"):
            sanciones_j = len(bajas[bajas["nombre"] == jugador]) if not bajas.empty else 0
            umbral = [5,4,3,2][min(sanciones_j, 3)]
            if len(grupo) >= umbral - 1:
                en_riesgo.append(jugador.title())

    if bajas_activas.empty and not en_riesgo:
        st.markdown("""
        <div style='background:#1F2937;border-left:3px solid #34D399;border-radius:4px;padding:14px 18px'>
            <span style='color:#34D399;font-weight:700'>✓ Plantel completo</span>
            <span style='color:#6B7280;font-size:0.85em;margin-left:8px'>Sin bajas ni riesgos.</span>
        </div>""", unsafe_allow_html=True)
    else:
        items = ""
        for _, row in bajas_activas.iterrows():
            icono = "🤕" if row["tipo"].lower() in ["lesión","lesion"] else "🟥"
            regreso = row["fecha_regreso"].strftime("%d/%m") if pd.notna(row["fecha_regreso"]) else "indef."
            items += f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #374151'><span style='color:#F9FAFB'>{icono} {str(row['nombre']).title()}</span><span style='color:#6B7280;font-size:0.82em'>{row['tipo']} · {regreso}</span></div>"
        for j in en_riesgo:
            items += f"<div style='padding:5px 0;border-bottom:1px solid #374151;color:#FCD34D'>⚠ {j} — riesgo suspensión</div>"
        st.markdown(f"""
        <div style='background:#1F2937;border-left:3px solid #F87171;border-radius:4px;padding:14px 18px'>
            <div style='font-size:0.6em;color:#6B7280;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px'>Novedades ({len(bajas_activas) + len(en_riesgo)})</div>
            {items}
        </div>""", unsafe_allow_html=True)

divider()

# ── Último partido analizado ──────────────────────────────────────────────────
if not os.path.exists(DATA_PATH):
    st.info("⏳ Las estadísticas estarán disponibles a partir del primer partido.")
    st.stop()

df = cargar_datos()
ultima_fecha  = df["fecha"].max()
df_ultimo     = df[df["fecha"] == ultima_fecha]
rival_row     = jugados[jugados["fecha"] == ultima_fecha]
rival_txt     = rival_row["rival"].values[0] if len(rival_row) else f"Fecha {ultima_fecha}"

pases         = len(df_ultimo[df_ultimo["Event"] == "pase"])
perdidas      = len(df_ultimo[df_ultimo["Event"] == "perdida"])
recuperaciones= len(df_ultimo[df_ultimo["Event"] == "recuperacion"])
ratio         = round(pases / perdidas, 1) if perdidas > 0 else "—"
top5          = df_ultimo.groupby("Player")["Event"].count().sort_values(ascending=False).head(5)

section(f"Último partido analizado · vs {rival_txt}")

c1, c2, c3, c4 = st.columns(4)
c1.markdown(card("Pases", pases, sub=f"{perdidas} pérdidas"), unsafe_allow_html=True)
c2.markdown(card("Ratio pase / pérdida", ratio), unsafe_allow_html=True)
c3.markdown(card("Recuperaciones", recuperaciones), unsafe_allow_html=True)
c4.markdown(card("Jugadores activos", df_ultimo["Player"].nunique()), unsafe_allow_html=True)

st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)

col_top, col_sug = st.columns([1, 1])

with col_top:
    section("Más activos en el partido")
    max_val  = top5.max()
    bars_html = ""
    for jugador, eventos in top5.items():
        pct = int(eventos / max_val * 100)
        bars_html += f"""
        <div style='margin-bottom:10px'>
            <div style='display:flex;justify-content:space-between;margin-bottom:3px'>
                <span style='font-size:0.85em;color:#F9FAFB;font-weight:600'>{jugador}</span>
                <span style='font-size:0.8em;color:#6B7280'>{eventos} eventos</span>
            </div>
            <div style='background:#374151;border-radius:2px;height:4px'>
                <div style='background:#E23E3E;width:{pct}%;height:4px;border-radius:2px'></div>
            </div>
        </div>"""
    st.markdown(f"<div style='background:#1F2937;border-radius:6px;padding:16px 20px'>{bars_html}</div>", unsafe_allow_html=True)

with col_sug:
    section("Sugerencias del video analista")

    # Generar sugerencias basadas en datos
    sugerencias_dt = []
    sugerencias_presidencia = []

    if ratio != "—":
        if float(ratio) < 3:
            sugerencias_dt.append("⚠ Ratio pase/pérdida bajo. Revisar salida desde el fondo y circuitos de juego en el próximo entrenamiento.")
        elif float(ratio) >= 5:
            sugerencias_dt.append("✓ Buen cuidado de la pelota. Mantener la dinámica de circulación.")

    if recuperaciones > 0:
        rec_por_jugador = df_ultimo[df_ultimo["Event"] == "recuperacion"].groupby("Player").size()
        top_rec = rec_por_jugador.idxmax()
        sugerencias_dt.append(f"💪 {top_rec} fue el jugador con más recuperaciones. Considerar como referencia defensiva para el próximo partido.")

    despejes = len(df_ultimo[df_ultimo["Event"] == "despeje"])
    if despejes > 15:
        sugerencias_dt.append(f"🔴 {despejes} despejes registrados. El equipo estuvo bajo presión. Analizar el bloque defensivo.")

    faltas = len(df_ultimo[df_ultimo["Event"] == "falta cometida"])
    if faltas > 8:
        sugerencias_dt.append(f"🟡 {faltas} faltas cometidas. Riesgo disciplinario alto — revisar posicionamiento defensivo.")

    if not sugerencias_dt:
        sugerencias_dt.append("Sin alertas tácticas relevantes en este partido.")

    # Presidencia
    sugerencias_presidencia.append(f"📊 El equipo registró {pases} acciones de pase en el partido — indicador de intención de juego asociado.")
    if len(jugados) > 0:
        if puntos / (len(jugados) * 3) >= 0.5:
            sugerencias_presidencia.append("✓ El rendimiento en puntos está por encima del 50% del máximo posible.")
        else:
            sugerencias_presidencia.append("⚠ El rendimiento en puntos está por debajo del 50% del máximo posible. Se recomienda reforzar el trabajo táctico.")
    sugerencias_presidencia.append(f"👥 {df_ultimo['Player'].nunique()} jugadores registraron actividad en el último partido analizado.")

    # Render
    dt_html = "".join([f"<div style='padding:7px 0;border-bottom:1px solid #374151;font-size:0.83em;color:#D1D5DB'>{s}</div>" for s in sugerencias_dt])
    pres_html = "".join([f"<div style='padding:7px 0;border-bottom:1px solid #374151;font-size:0.83em;color:#D1D5DB'>{s}</div>" for s in sugerencias_presidencia])

    tab_dt, tab_pres = st.tabs(["🎯 Para el cuerpo técnico", "🏛 Para presidencia"])
    with tab_dt:
        st.markdown(f"<div style='background:#1F2937;border-radius:6px;padding:14px 18px'>{dt_html}</div>", unsafe_allow_html=True)
    with tab_pres:
        st.markdown(f"<div style='background:#1F2937;border-radius:6px;padding:14px 18px'>{pres_html}</div>", unsafe_allow_html=True)