# ==========================
# 1) IMPORTS & CONFIG
# ==========================
import streamlit as st

st.set_page_config(
    page_title="Estrella FC · Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import os
from datetime import date

# ==========================
# 2) LAYOUT INIT
# ==========================
from components.layout import (
    inject_css,
    render_sidebar,
    render_header
)

inject_css()

BASE = os.path.dirname(os.path.abspath(__file__))

render_sidebar(BASE)

render_header(
    "Torneo Promocional Amateur 2026",
    "Panel de análisis"
)

# ==========================
# 3) UI HELPERS
# ==========================
def card(label, value, sub=None, accent=False):
    glow = "box-shadow: 0 8px 24px rgba(0,0,0,.2);"
    accent_bg = "background: linear-gradient(180deg, rgba(226,62,62,.06), #111827);" if accent else "background: #111827;"
    
    sub_html = f"""
        <div style="margin-top:8px; color:#9CA3AF; font-size:.8rem; font-weight:500;">
            {sub}
        </div>
    """ if sub else ""

    return f"""
    <div style="
        {accent_bg}
        border: 1px solid rgba(255,255,255,.05);
        border-radius: 12px;
        padding: 24px;
        min-height: 140px;
        {glow}
    ">
        <div style="color:#6B7280; font-size:.75rem; text-transform:uppercase; letter-spacing:1.5px; font-weight:600;">
            {label}
        </div>
        <div style="margin-top:12px; font-size:2.4rem; font-weight:800; color:#F8FAFC; line-height:1;">
            {value}
        </div>
        {sub_html}
    </div>
    """

def section(title):
    st.markdown(
        f"""
        <div style="margin-top: 2rem; margin-bottom: 1.5rem; color:#9CA3AF; font-size:.8rem; font-weight:700; text-transform:uppercase; letter-spacing:2px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">
            {title}
        </div>
        """,
        unsafe_allow_html=True
    )

def insight(text, level="neutral"):
    colors = {"good":"#10B981", "warn":"#F59E0B", "bad":"#EF4444", "neutral":"#3B82F6"}
    return f"""
    <div style="
        background: #1F2937;
        border-left: 4px solid {colors[level]};
        border-radius: 6px;
        padding: 16px 20px;
        margin-bottom: 12px;
        color: #E5E7EB;
        font-size: .9rem;
        line-height: 1.6;
        box-shadow: 0 4px 6px rgba(0,0,0,.1);
    ">
        {text}
    </div>
    """

def racha_visual(df):
    if df.empty:
        return "<span style='color:#6B7280; font-size:0.9rem;'>Sin datos</span>"
    salida = ""
    colores = {"W":"#10B981", "D":"#F59E0B", "L":"#EF4444"}
    
    for _, r in df.tail(3).iterrows():
        if r["goles_favor"] > r["goles_contra"]: res = "W"
        elif r["goles_favor"] == r["goles_contra"]: res = "D"
        else: res = "L"
        
        salida += f"""
        <span style="
            background: {colores[res]}20;
            color: {colores[res]};
            border: 1px solid {colores[res]}40;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: .85rem;
            font-weight: 700;
            margin-right: 8px;
        ">
            {res}
        </span>
        """
    return salida

# ==========================
# 4) PATHS
# ==========================
DATA_PATH = os.path.join(BASE, "data", "events_clean.csv")
FIXTURE_PATH = os.path.join(BASE, "data", "fixture.csv")
ALERTAS_PATH = os.path.join(BASE, "data", "sanciones_lesiones.csv")

# ==========================
# 5) CACHE DATA
# ==========================
@st.cache_data
def cargar_eventos():
    if not os.path.exists(DATA_PATH): return pd.DataFrame()
    df = pd.read_csv(DATA_PATH)
    if "Mins" in df.columns and "Secs" in df.columns:
        df["tiempo_total"] = df["Mins"] * 60 + df["Secs"]
    return df

@st.cache_data(ttl=0)
def cargar_fixture():
    if not os.path.exists(FIXTURE_PATH): return pd.DataFrame()
    return pd.read_csv(FIXTURE_PATH)

@st.cache_data(ttl=0)
def cargar_alertas():
    if not os.path.exists(ALERTAS_PATH): return pd.DataFrame()
    df = pd.read_csv(ALERTAS_PATH)
    if not df.empty and "fecha_regreso" in df.columns:
        df["fecha_regreso"] = pd.to_datetime(df["fecha_regreso"], dayfirst=True, errors="coerce")
    return df

# ==========================
# 6) CARGA GLOBAL
# ==========================
fixture = cargar_fixture()
alertas = cargar_alertas()
df = cargar_eventos()
hoy = pd.Timestamp(date.today())

# ==========================
# 7) VALIDACIONES
# ==========================
if fixture.empty:
    st.markdown(insight("No se encontró el archivo de fixture.csv", "warn"), unsafe_allow_html=True)
    st.stop()

# ==========================
# 8) VARIABLES DERIVADAS
# ==========================
jugados = fixture[fixture["estado"] == "Jugado"]
pendientes = fixture[fixture["estado"] == "Pendiente"]

ganados = len(jugados[jugados["goles_favor"] > jugados["goles_contra"]])
empatados = len(jugados[jugados["goles_favor"] == jugados["goles_contra"]])
perdidos = len(jugados[jugados["goles_favor"] < jugados["goles_contra"]])
puntos = ganados * 3 + empatados
gf = int(jugados["goles_favor"].sum()) if not jugados.empty else 0
gc = int(jugados["goles_contra"].sum()) if not jugados.empty else 0

# ==========================
# 9) RENDER DASHBOARD
# ==========================

# --- ESTADO COMPETITIVO ---
section("Estado competitivo")

if jugados.empty:
    st.markdown(insight("Todavía no hay partidos cargados para generar indicadores.", "neutral"), unsafe_allow_html=True)
else:
    total_posibles = len(jugados) * 3
    efectividad = round(puntos / total_posibles * 100) if total_posibles > 0 else 0
    momento = "Positivo" if efectividad >= 55 else "En construcción"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(card("Momento", f"{efectividad}%", sub=f"{momento}", accent=efectividad >= 55), unsafe_allow_html=True)
    with c2:
        st.markdown(card("Producción ofensiva", gf, sub=f"{round(gf/max(len(jugados),1),1)} por partido"), unsafe_allow_html=True)
    with c3:
        st.markdown(card("Solidez defensiva", gc, sub=f"{round(gc/max(len(jugados),1),1)} recibidos"), unsafe_allow_html=True)
    with c4:
        st.markdown(
            f"""
            <div style="background:#111827; border-radius:12px; padding:24px; min-height:140px; border:1px solid rgba(255,255,255,.05); box-shadow:0 8px 24px rgba(0,0,0,.2);">
                <div style="color:#6B7280; font-size:.75rem; text-transform:uppercase; letter-spacing:1.5px; font-weight:600;">Tendencia</div>
                <div style="margin-top:20px; display:flex; align-items:center;">
                    {racha_visual(jugados)}
                </div>
                <div style="margin-top:16px; color:#9CA3AF; font-size:.85rem; font-weight:500;">
                    {ganados}G · {empatados}E · {perdidos}P
                </div>
            </div>
            """, unsafe_allow_html=True
        )


# --- PRÓXIMO PARTIDO ---
section("Próximo partido")

if pendientes.empty:
    st.markdown(insight("No hay partidos pendientes cargados.", "neutral"), unsafe_allow_html=True)
else:
    partido = pendientes.iloc[0]
    condicion = str(partido["condicion"])
    rival = str(partido["rival"])
    fecha = int(partido["fecha"])
    
    icono = "🏠" if condicion == "Local" else "✈️"
    color_badge = "#10B981" if condicion == "Local" else "#3B82F6"

    col_match, col_info = st.columns([1.4, 1])
    with col_match:
        st.markdown(
            f"""
            <div style="background:#111827; border-radius:12px; padding:30px; min-height:180px; border:1px solid rgba(255,255,255,.05); box-shadow:0 8px 24px rgba(0,0,0,.2);">
                <div style="color:#9CA3AF; text-transform:uppercase; letter-spacing:1.5px; font-size:.8rem; font-weight:600; margin-bottom:12px;">
                    Fecha {fecha}
                </div>
                <div style="font-size:2.2rem; font-weight:800; color:#F9FAFB; letter-spacing:-0.5px;">
                    {icono} vs <span style="color:#E23E3E">{rival}</span>
                </div>
                <div style="margin-top:24px;">
                    <span style="background:{color_badge}15; color:{color_badge}; border:1px solid {color_badge}30; padding:8px 16px; border-radius:8px; font-size:.85rem; font-weight:700; text-transform:uppercase; letter-spacing:1px;">
                        {condicion}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True
        )
    with col_info:
        st.markdown(
            """
            <div style="background:#111827; border-radius:12px; padding:30px; min-height:180px; border:1px solid rgba(255,255,255,.05); box-shadow:0 8px 24px rgba(0,0,0,.2);">
                <div style="color:#9CA3AF; text-transform:uppercase; letter-spacing:1.5px; font-size:.8rem; font-weight:600; margin-bottom:20px;">
                    Checklist Previa
                </div>
                <div style="color:#E5E7EB; line-height:2; font-size:.95rem; font-weight:500;">
                    ✓ Confirmar disponibilidad del plantel<br>
                    ✓ Preparar corte de video del rival<br>
                    ✓ Revisar tendencia reciente y bloque defensivo
                </div>
            </div>
            """, unsafe_allow_html=True
        )


# --- DISPONIBILIDAD DEL PLANTEL ---
section("Disponibilidad del plantel")

bajas_tipos = ["lesión", "lesion", "sanción", "sancion", "roja directa"]

if alertas.empty:
    st.markdown(insight("No hay registros de alertas cargados.", "neutral"), unsafe_allow_html=True)
else:
    bajas = alertas[alertas["tipo"].str.lower().isin(bajas_tipos)]
    bajas_activas = bajas[(bajas["fecha_regreso"].isna()) | (bajas["fecha_regreso"] >= hoy)]
    amarillas = alertas[alertas["tipo"].str.lower() == "amarilla"]
    
    riesgo = []
    if not amarillas.empty:
        for jugador, grupo in amarillas.groupby("nombre"):
            sanciones = len(bajas[bajas["nombre"] == jugador])
            umbral = [5, 4, 3, 2][min(sanciones, 3)]
            if len(grupo) >= umbral - 1:
                riesgo.append(jugador.title())

    disponibles = max(0, 20 - len(bajas_activas))

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(card("Disponibles", disponibles, "Aptos para competir"), unsafe_allow_html=True)
    with c2:
        st.markdown(card("Bajas", len(bajas_activas), "No disponibles", accent=(len(bajas_activas) > 0)), unsafe_allow_html=True)
    with c3:
        st.markdown(card("Riesgo", len(riesgo), "Al límite de amonestaciones"), unsafe_allow_html=True)

    detalle = ""
    for _, row in bajas_activas.iterrows():
        icon = "🤕" if row["tipo"].lower() in ["lesión", "lesion"] else "🟥"
        regreso = row["fecha_regreso"].strftime("%d/%m") if pd.notna(row["fecha_regreso"]) else "Sin fecha"
        detalle += f"""
        <div style='padding:12px 0; border-bottom:1px solid rgba(255,255,255,.05); display:flex; justify-content:space-between; align-items:center;'>
            <span style='color:#F9FAFB; font-weight:500; font-size:.95rem;'>{icon} {row["nombre"].title()}</span>
            <span style='color:#9CA3AF; font-size:.85rem; font-weight:500; background:#1F2937; padding:4px 10px; border-radius:4px;'>{row["tipo"].upper()} · {regreso}</span>
        </div>
        """
    for jugador in riesgo:
        detalle += f"""
        <div style='padding:12px 0; border-bottom:1px solid rgba(255,255,255,.05); display:flex; justify-content:space-between; align-items:center;'>
            <span style='color:#FBBF24; font-weight:500; font-size:.95rem;'>⚠ {jugador}</span>
            <span style='color:#FBBF24; font-size:.85rem; font-weight:600; background:rgba(251,191,36,.1); padding:4px 10px; border-radius:4px;'>RIESGO SUSPENSIÓN</span>
        </div>
        """

    if detalle == "":
        detalle = "<div style='color:#10B981; padding:16px 0; font-weight:600;'>✓ Plantel completo a disposición.</div>"

    st.markdown(
        f"""
        <div style="background:#111827; border-radius:12px; padding:12px 24px; border:1px solid rgba(255,255,255,.05); box-shadow:0 8px 24px rgba(0,0,0,.2); margin-top: 1rem;">
            {detalle}
        </div>
        """, unsafe_allow_html=True
    )


# --- ÚLTIMO PARTIDO ANALIZADO ---
section("Último partido analizado")

if df.empty:
    st.markdown(insight("Las estadísticas aparecerán luego del primer partido cargado.", "neutral"), unsafe_allow_html=True)
else:
    ultima_fecha = df["fecha"].max()
    df_ultimo = df[df["fecha"] == ultima_fecha]
    rival_row = jugados[jugados["fecha"] == ultima_fecha]
    rival_text = rival_row["rival"].values[0] if len(rival_row) else f"Fecha {ultima_fecha}"

    pases = len(df_ultimo[df_ultimo["Event"] == "pase"])
    perdidas = len(df_ultimo[df_ultimo["Event"] == "perdida"])
    recuperaciones = len(df_ultimo[df_ultimo["Event"] == "recuperacion"])
    jugadores_activos = df_ultimo["Player"].nunique()
    ratio = round(pases / perdidas, 1) if perdidas > 0 else "—"

    st.markdown(
        f"""
        <div style="color:#9CA3AF; margin-bottom:20px; font-size:.95rem; font-weight:500;">
            Rival analizado: <span style="color:#E23E3E; font-weight:700; background:rgba(226,62,62,.1); padding:4px 10px; border-radius:6px; margin-left:8px;">{rival_text}</span>
        </div>
        """, unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(card("Circulación", pases, "Acciones de pase"), unsafe_allow_html=True)
    with c2:
        nivel_ratio = "Alta" if ratio != "—" and ratio >= 5 else "Media" if ratio != "—" and ratio >= 3 else "Baja"
        st.markdown(card("Cuidado balón", ratio, f"Seguridad: {nivel_ratio}"), unsafe_allow_html=True)
    with c3:
        st.markdown(card("Recuperaciones", recuperaciones, "Fase defensiva"), unsafe_allow_html=True)
    with c4:
        st.markdown(card("Participación", jugadores_activos, "Jugadores activos"), unsafe_allow_html=True)

    # Sub-sección: Influencia
    st.markdown("<div style='margin-top:2rem; margin-bottom:1rem; color:#6B7280; font-size:.75rem; text-transform:uppercase; letter-spacing:1.5px; font-weight:600;'>Influencia en el juego (Top 5 Volúmen)</div>", unsafe_allow_html=True)
    
    top = df_ultimo.groupby("Player")["Event"].count().sort_values(ascending=False).head(5)
    contenido = ""
    maximo = top.max() if not top.empty else 1

    for jugador, valor in top.items():
        ancho = int(valor / maximo * 100)
        contenido += f"""
        <div style='margin-bottom:16px;'>
            <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-size:.9rem;'>
                <span style='color:#F9FAFB; font-weight:600'>{jugador}</span>
                <span style='color:#9CA3AF; font-weight:500;'>{valor} acciones</span>
            </div>
            <div style='background:#1F2937; height:8px; border-radius:99px; overflow:hidden;'>
                <div style='width:{ancho}%; background:#E23E3E; height:100%; border-radius:99px; transition: width 0.5s ease;'></div>
            </div>
        </div>
        """

    st.markdown(
        f"""
        <div style="background:#111827; border-radius:12px; padding:24px; border:1px solid rgba(255,255,255,.05); box-shadow:0 8px 24px rgba(0,0,0,.2);">
            {contenido}
        </div>
        """, unsafe_allow_html=True
    )


# --- CONCLUSIONES ---
section("Conclusiones del análisis")

if df.empty:
    st.markdown(insight("Todavía no hay eventos suficientes para generar observaciones.", "neutral"), unsafe_allow_html=True)
else:
    conclusiones = []

    # Cuidado de balón
    if ratio != "—":
        if ratio >= 5:
            conclusiones.append(("good", "Buena relación pase/pérdida. El equipo sostuvo la circulación con un bajo volumen de pérdidas relativas."))
        elif ratio >= 3:
            conclusiones.append(("warn", "Relación pase/pérdida intermedia. Existieron secuencias de posesión con interrupciones frecuentes."))
        else:
            conclusiones.append(("bad", "Relación pase/pérdida baja. El volumen de pérdidas condicionó la continuidad estructural."))

    # Recuperaciones
    if recuperaciones > 25:
        conclusiones.append(("good", f"Alta frecuencia de recuperación ({recuperaciones}). El bloque defensivo logró interceder constantemente."))
    elif recuperaciones < 10:
        conclusiones.append(("warn", f"Baja frecuencia de recuperación ({recuperaciones}). Revisar alturas de presión y duelos defensivos."))

    # Despejes
    despejes = len(df_ultimo[df_ultimo["Event"] == "despeje"])
    if despejes >= 15:
        conclusiones.append(("warn", f"Alto volumen de despejes ({despejes}). El equipo transitó pasajes prolongados de hundimiento defensivo."))

    # Disciplina
    faltas = len(df_ultimo[df_ultimo["Event"] == "falta cometida"])
    if faltas >= 8:
        conclusiones.append(("warn", f"Incremento del riesgo disciplinario. Se cometieron {faltas} infracciones en fase de contención."))

    # Jugador referencia
    if recuperaciones > 0:
        top_rec = df_ultimo[df_ultimo["Event"] == "recuperacion"].groupby("Player").size()
        if not top_rec.empty:
            jugador_clave = top_rec.idxmax()
            cant_rec = int(top_rec.max())
            conclusiones.append(("neutral", f"{jugador_clave} actuó como referencia en la recuperación ({cant_rec} intervenciones exitosas)."))

    if not conclusiones:
        conclusiones.append(("neutral", "La muestra actual no arroja desviaciones estadísticas significativas respecto a la media."))

    izq, der = st.columns([1.5, 1])
    
    with izq:
        html_obs = ""
        for nivel, texto in conclusiones:
            html_obs += insight(texto, nivel)
        st.markdown(html_obs, unsafe_allow_html=True)
        
    with der:
        st.markdown(
            f"""
            <div style="background:#111827; border-radius:12px; padding:24px; border:1px solid rgba(255,255,255,.05); box-shadow:0 8px 24px rgba(0,0,0,.2); height: 100%;">
                <div style="color:#6B7280; text-transform:uppercase; letter-spacing:1.5px; font-size:.75rem; font-weight:600; margin-bottom:20px; border-bottom:1px solid rgba(255,255,255,.05); padding-bottom:10px;">
                    Resumen Cuantitativo
                </div>
                <div style="color:#D1D5DB; font-size:1rem; line-height:2.2;">
                    <div style="display:flex; justify-content:space-between;"><span>Acciones de pase:</span> <strong style="color:#F9FAFB;">{pases}</strong></div>
                    <div style="display:flex; justify-content:space-between;"><span>Pérdidas de balón:</span> <strong style="color:#F9FAFB;">{perdidas}</strong></div>
                    <div style="display:flex; justify-content:space-between;"><span>Recuperaciones:</span> <strong style="color:#F9FAFB;">{recuperaciones}</strong></div>
                    <div style="display:flex; justify-content:space-between;"><span>Intervenciones (Top):</span> <strong style="color:#F9FAFB;">{maximo}</strong></div>
                </div>
            </div>
            """, unsafe_allow_html=True
        )

st.markdown("<div style='margin-bottom: 4rem;'></div>", unsafe_allow_html=True)
