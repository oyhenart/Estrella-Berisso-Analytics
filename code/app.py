# ==========================
# 1) IMPORTS
# ==========================
import streamlit as st
import pandas as pd
import os
from datetime import date

# ==========================
# 2) STREAMLIT CONFIG
# ==========================
st.set_page_config(
    page_title="Estrella FC · Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

from components.layout import (
    inject_css,
    render_sidebar,
    render_header,
    render_mobile_nav       # ← LÍNEA NUEVA
)
 
inject_css()
BASE = os.path.dirname(os.path.abspath(__file__))
render_sidebar(BASE)
render_mobile_nav()         # ← LÍNEA NUEVA
render_header("Torneo Promocional Amateur 2026", "Panel de análisis")

# ==========================
# 3) CONFIG DEL EQUIPO / DT ACTUAL
# ==========================
# Nombre del equipo tal como aparece en tabla_posiciones.csv, para destacar su fila.
NOMBRE_EQUIPO = "Estrella de Berisso"

# DT actual, usado para filtrar los indicadores de "Estado competitivo" y que
# reflejen solo los partidos dirigidos por él (no arrastran la gestión anterior).
# TODO Israel: confirmame el nombre exacto de la columna en fixture.csv que
# identifica al DT de cada partido (asumí "dt" acá abajo) y que el valor
# guardado ahí sea efectivamente "Zein" (o una variante que tenga que matchear).
DT_ACTUAL = "Zein"
COLUMNA_DT = "dt"

# ==========================
# 4) UI HELPERS (Evitan saltos de línea/sangrías que rompen el render de Markdown)
# ==========================
def card(label, value, sub=None, accent=False):
    glow = "box-shadow: 0 10px 28px rgba(0,0,0,.28);"
    accent_bg = "background: linear-gradient(180deg, rgba(226,62,62,.08), #111827);" if accent else "background: #111827;"
    sub_html = f"<div style='margin-top:8px; color:#9CA3AF; font-size:.78rem;'>{sub}</div>" if sub else ""
    return f"<div style='{accent_bg} border:1px solid rgba(255,255,255,.04); border-radius:14px; padding:22px; min-height:135px; {glow}'><div style='color:#6B7280; font-size:.70rem; text-transform:uppercase; letter-spacing:2px; font-weight:600;'>{label}</div><div style='margin-top:12px; font-size:2.15rem; font-weight:800; color:#F8FAFC; line-height:1;'>{value}</div>{sub_html}</div>"

def section(title):
    st.markdown(f"<div style='margin-top:28px; margin-bottom:14px; color:#6B7280; font-size:.70rem; font-weight:700; text-transform:uppercase; letter-spacing:3px;'>{title}</div>", unsafe_allow_html=True)

def divider():
    st.markdown("<div style='margin:30px 0; height:1px; background:linear-gradient(to right, rgba(255,255,255,.06), transparent);'></div>", unsafe_allow_html=True)

def insight(text, level="neutral"):
    colors = {"good":"#22C55E", "warn":"#EAB308", "bad":"#EF4444", "neutral":"#3B82F6"}
    return f"<div style='background:#111827; border-left:4px solid {colors[level]}; border-radius:10px; padding:14px 16px; margin-bottom:10px; color:#D1D5DB; font-size:.86rem; line-height:1.55;'>{text}</div>"

def racha_visual(df):
    if df.empty:
        return "<span style='color:#6B7280; font-size:.78rem;'>Sin datos</span>"
    salida = ""
    colores = {"W":"#22C55E", "D":"#F59E0B", "L":"#EF4444"}
    for _, r in df.tail(3).iterrows():
        if r["goles_favor"] > r["goles_contra"]: res = "W"
        elif r["goles_favor"] == r["goles_contra"]: res = "D"
        else: res = "L"
        salida += f"<span style='background:{colores[res]}; color:#111827; padding:4px 8px; border-radius:6px; font-size:.78rem; font-weight:800; margin-right:6px; display:inline-block;'>{res}</span>"
    return salida

# ==========================
# 4.1) ESCUDOS
# ==========================
ESCUDOS_PATH = os.path.join(BASE, "static", "escudos")

import base64

def escudo_a_base64(ruta):
    """Convierte un archivo de imagen a base64 para insertarlo inline en HTML."""
    if not ruta or not os.path.exists(ruta):
        return None
    ext = os.path.splitext(ruta)[1].lower().replace(".", "")
    mime = "jpeg" if ext in ["jpg", "jpeg"] else ext
    with open(ruta, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{mime};base64,{data}"

def buscar_escudo(nombre_rival):
    """Busca el archivo de escudo para un rival, tolerando mayúsculas/minúsculas y extensión."""
    if not nombre_rival or not os.path.isdir(ESCUDOS_PATH):
        return None
    candidatos = [
        f"{nombre_rival}.png",
        f"{nombre_rival}.jpg",
        f"{nombre_rival}.jpeg",
        f"{nombre_rival}.webp",
    ]
    archivos_existentes = os.listdir(ESCUDOS_PATH)
    archivos_lower = {a.lower(): a for a in archivos_existentes}

    for candidato in candidatos:
        ruta = os.path.join(ESCUDOS_PATH, candidato)
        if os.path.exists(ruta):
            return ruta
        if candidato.lower() in archivos_lower:
            return os.path.join(ESCUDOS_PATH, archivos_lower[candidato.lower()])
    return None

# ==========================
# 5) PATHS
# ==========================
DATA_PATH = os.path.join(BASE, "data", "events_clean.csv")
FIXTURE_PATH = os.path.join(BASE, "data", "fixture.csv")
ALERTAS_PATH = os.path.join(BASE, "data", "sanciones_lesiones.csv")
JUGADORES_PATH = os.path.join(BASE, "data", "Jugadores.csv")
TABLA_POSICIONES_PATH = os.path.join(BASE, "data", "tabla_posiciones.csv")

# ==========================
# 6) CACHE DATA
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

@st.cache_data(ttl=0)
def cargar_jugadores():
    if not os.path.exists(JUGADORES_PATH): return pd.DataFrame()
    return pd.read_csv(JUGADORES_PATH)

@st.cache_data(ttl=0)
def cargar_tabla_posiciones():
    if not os.path.exists(TABLA_POSICIONES_PATH): return pd.DataFrame()
    df = pd.read_csv(TABLA_POSICIONES_PATH)
    # Si falta la diferencia de gol, la calculamos.
    if "dg" not in df.columns and {"gf", "gc"}.issubset(df.columns):
        df["dg"] = df["gf"] - df["gc"]
    # Ordenamos por puntos y diferencia de gol si no viene un campo "pos" explícito.
    if "pos" not in df.columns and "pts" in df.columns:
        df = df.sort_values(by=["pts", "dg"], ascending=False).reset_index(drop=True)
        df["pos"] = df.index + 1
    return df

# ==========================
# 6.1) RIESGO DE SUSPENSIÓN (con reinicio tras sanción cumplida)
# ==========================
def calcular_riesgo_suspension(alertas, hoy):
    """
    Devuelve la lista de jugadores en riesgo de sanción por amarillas.
    A diferencia de la versión anterior, si el jugador ya cumplió una sanción
    (roja/acumulación de amarillas), las amarillas anteriores a esa sanción
    cumplida ya NO cuentan para el próximo umbral.

    TODO Israel: esto asume que sanciones_lesiones.csv tiene una columna
    "fecha" con la fecha en que ocurrió cada evento (la amarilla, la roja,
    la sanción). Si la columna se llama distinto, decime el nombre real y
    lo ajusto. Si no existe ninguna fecha de evento, no hay forma de saber
    qué amarillas son "de antes" o "de después" de la sanción cumplida, y
    el conteo va a seguir sin poder reiniciarse correctamente.
    """
    riesgo = []
    if alertas.empty or "tipo" not in alertas.columns or "nombre" not in alertas.columns:
        return riesgo

    tipo_lower = alertas["tipo"].str.lower()
    amarillas = alertas[tipo_lower == "amarilla"]
    suspensiones = alertas[tipo_lower.isin(["sanción", "sancion", "roja directa"])]
    tiene_fecha_evento = "fecha" in alertas.columns

    if amarillas.empty:
        return riesgo

    for jugador_name, grupo in amarillas.groupby("nombre"):
        grupo_vigente = grupo

        if tiene_fecha_evento:
            sus_jugador = suspensiones[suspensiones["nombre"] == jugador_name]
            # Sanciones ya cumplidas: sin fecha de regreso, o con fecha de regreso ya pasada.
            cumplidas = sus_jugador[
                sus_jugador["fecha_regreso"].isna() | (sus_jugador["fecha_regreso"] < hoy)
            ]
            if not cumplidas.empty:
                fecha_ultima_cumplida = pd.to_datetime(
                    cumplidas["fecha"], dayfirst=True, errors="coerce"
                ).max()
                fechas_amarillas = pd.to_datetime(grupo["fecha"], dayfirst=True, errors="coerce")
                grupo_vigente = grupo[fechas_amarillas > fecha_ultima_cumplida]

        sanciones_previas = len(suspensiones[suspensiones["nombre"] == jugador_name])
        umbral = [5, 4, 3, 2][min(sanciones_previas, 3)]
        if len(grupo_vigente) >= umbral - 1:
            riesgo.append(jugador_name.title())

    return riesgo

# ==========================
# 7) CARGA GLOBAL
# ==========================
fixture = cargar_fixture()
alertas = cargar_alertas()
df = cargar_eventos()
jugadores = cargar_jugadores()
tabla_posiciones = cargar_tabla_posiciones()
hoy = pd.Timestamp(date.today())

# ==========================
# 8) VALIDACIONES
# ==========================
if fixture.empty:
    st.warning("No se encontró fixture.csv")
    st.stop()

# ==========================
# 9) VARIABLES DERIVADAS
# ==========================
jugados = fixture[fixture["estado"] == "Jugado"]
pendientes = fixture[fixture["estado"] == "Pendiente"]

# Recorte por gestión del DT actual, solo para los indicadores de "Estado competitivo".
if COLUMNA_DT in fixture.columns:
    jugados_dt = jugados[jugados[COLUMNA_DT].astype(str).str.contains(DT_ACTUAL, case=False, na=False)]
else:
    # Fallback: si todavía no existe la columna del DT en el fixture, mostramos todo
    # el historial para no romper el dashboard, pero esto hay que corregirlo.
    jugados_dt = jugados

ganados = len(jugados_dt[jugados_dt["goles_favor"] > jugados_dt["goles_contra"]])
empatados = len(jugados_dt[jugados_dt["goles_favor"] == jugados_dt["goles_contra"]])
perdidos = len(jugados_dt[jugados_dt["goles_favor"] < jugados_dt["goles_contra"]])
puntos = ganados * 3 + empatados
gf = int(jugados_dt["goles_favor"].sum()) if not jugados_dt.empty else 0
gc = int(jugados_dt["goles_contra"].sum()) if not jugados_dt.empty else 0

# ==========================
# 10) RENDER DASHBOARD
# ==========================

# --- ESTADO COMPETITIVO ---
section("Estado competitivo")

if jugados_dt.empty:
    st.markdown(insight(f"Todavía no hay partidos cargados bajo la gestión de {DT_ACTUAL}.", "neutral"), unsafe_allow_html=True)
else:
    total_posibles = len(jugados_dt) * 3
    efectividad = round(puntos / total_posibles * 100) if total_posibles > 0 else 0
    momento = "Positivo" if efectividad >= 55 else "En construcción"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(card("Momento", f"{efectividad}%", sub=f"{momento}", accent=efectividad >= 55), unsafe_allow_html=True)
    with c2:
        st.markdown(card("Producción ofensiva", gf, sub=f"{round(gf/max(len(jugados_dt),1),1)} por partido"), unsafe_allow_html=True)
    with c3:
        st.markdown(card("Solidez defensiva", gc, sub=f"{round(gc/max(len(jugados_dt),1),1)} recibidos"), unsafe_allow_html=True)
    with c4:
        # La tendencia se mantiene con el historial completo, no solo la gestión actual.
        st.markdown(f"<div style='background:#111827; border-radius:14px; padding:22px; min-height:135px; border:1px solid rgba(255,255,255,.04); box-shadow: 0 10px 28px rgba(0,0,0,.28);'><div style='color:#6B7280; font-size:.70rem; text-transform:uppercase; letter-spacing:2px; font-weight:600;'>Tendencia</div><div style='margin-top:14px; display:block;'>{racha_visual(jugados)}</div><div style='margin-top:12px; color:#9CA3AF; font-size:.80rem;'>{ganados}G · {empatados}E · {perdidos}P</div></div>", unsafe_allow_html=True)

divider()

# --- TABLA DEL TORNEO ---
section("Tabla del torneo")

if tabla_posiciones.empty:
    st.markdown(insight("Todavía no cargaste data/tabla_posiciones.csv con la tabla del torneo.", "neutral"), unsafe_allow_html=True)
else:
    filas_html = ""
    for _, row in tabla_posiciones.iterrows():
        es_estrella = NOMBRE_EQUIPO.lower() in str(row.get("equipo", "")).lower()
        fondo = "background: rgba(226,62,62,.12);" if es_estrella else ""
        color_equipo = "#E23E3E" if es_estrella else "#F9FAFB"
        peso = "800" if es_estrella else "500"
        dg_val = int(row["dg"]) if "dg" in row and pd.notna(row["dg"]) else "—"
        dg_str = f"+{dg_val}" if isinstance(dg_val, int) and dg_val > 0 else dg_val
        filas_html += f"""<div style='display:grid; grid-template-columns: 34px 1fr 40px 40px 40px 40px 50px 50px; align-items:center; padding:10px 6px; border-bottom:1px solid rgba(255,255,255,.04); {fondo} font-size:.82rem;'>
            <div style='color:#6B7280; font-weight:700;'>{row.get("pos", "—")}</div>
            <div style='color:{color_equipo}; font-weight:{peso};'>{row.get("equipo", "—")}</div>
            <div style='text-align:center; color:#9CA3AF;'>{row.get("pj", "—")}</div>
            <div style='text-align:center; color:#9CA3AF;'>{row.get("pg", "—")}</div>
            <div style='text-align:center; color:#9CA3AF;'>{row.get("pe", "—")}</div>
            <div style='text-align:center; color:#9CA3AF;'>{row.get("pp", "—")}</div>
            <div style='text-align:center; color:#9CA3AF;'>{dg_str}</div>
            <div style='text-align:center; color:#F9FAFB; font-weight:800;'>{row.get("pts", "—")}</div>
        </div>"""

    encabezado_html = """<div style='display:grid; grid-template-columns: 34px 1fr 40px 40px 40px 40px 50px 50px; padding:0 6px 10px 6px; color:#6B7280; font-size:.68rem; text-transform:uppercase; letter-spacing:1px; font-weight:700;'>
        <div>#</div><div>Equipo</div><div style='text-align:center;'>PJ</div><div style='text-align:center;'>PG</div><div style='text-align:center;'>PE</div><div style='text-align:center;'>PP</div><div style='text-align:center;'>DG</div><div style='text-align:center;'>PTS</div>
    </div>"""

    st.markdown(f"<div style='background:#111827; border-radius:14px; padding:18px; border:1px solid rgba(255,255,255,.04); box-shadow: 0 10px 28px rgba(0,0,0,.28); overflow-x:auto;'>{encabezado_html}{filas_html}</div>", unsafe_allow_html=True)

divider()

# --- PRÓXIMO PARTIDO ---
section("Próximo partido")

if pendientes.empty:
    st.markdown(insight("No hay partidos pendientes cargados.", "neutral"), unsafe_allow_html=True)
else:
    partido = pendientes.iloc[0]
    condicion = str(partido["condicion"])
    rival_next = str(partido["rival"])
    fecha_next = int(partido["fecha"])
    icono = "🏠" if condicion == "Local" else "✈️"
    color_badge = "#22C55E" if condicion == "Local" else "#60A5FA"

    escudo_estrella_b64 = escudo_a_base64(buscar_escudo("Local"))
    escudo_rival_b64 = escudo_a_base64(buscar_escudo(rival_next))

    img_estrella = f"<img src='{escudo_estrella_b64}' style='width:56px; height:56px; object-fit:contain; border-radius:8px;' />" if escudo_estrella_b64 else "<div style='width:56px; height:56px;'></div>"
    img_rival = f"<img src='{escudo_rival_b64}' style='width:56px; height:56px; object-fit:contain; border-radius:8px;' />" if escudo_rival_b64 else "<div style='width:56px; height:56px;'></div>"

    st.markdown(f"""<div style='background:#111827; border-radius:14px; padding:26px; min-height:180px; border:1px solid rgba(255,255,255,.04); box-shadow: 0 10px 28px rgba(0,0,0,.28);'>
        <div style='color:#6B7280; text-transform:uppercase; letter-spacing:2px; font-size:.72rem; margin-bottom:16px;'>Fecha {fecha_next}</div>
        <div style='display:flex; align-items:center; gap:18px;'>
            {img_estrella}
            <div style='font-size:1.7rem; font-weight:800; color:#F9FAFB;'>{icono} vs <span style='color:#E23E3E'>{rival_next}</span></div>
            {img_rival}
        </div>
        <div style='margin-top:18px;'><span style='background:{color_badge}20; color:{color_badge}; padding:8px 14px; border-radius:10px; font-size:.82rem; font-weight:700;'>{condicion}</span></div>
    </div>""", unsafe_allow_html=True)

divider()

# --- DISPONIBILIDAD DEL PLANTEL ---
section("Disponibilidad del plantel")

bajas_tipos = ["lesión", "lesion", "sanción", "sancion", "roja directa"]

if alertas.empty:
    st.markdown(insight("No hay registros de alertas cargados.", "neutral"), unsafe_allow_html=True)
else:
    bajas = alertas[alertas["tipo"].str.lower().isin(bajas_tipos)]
    bajas_activas = bajas[(bajas["fecha_regreso"].isna()) | (bajas["fecha_regreso"] >= hoy)]
    riesgo = calcular_riesgo_suspension(alertas, hoy)

    # Tamaño real del plantel desde Jugadores.csv en lugar del "20" fijo.
    # TODO Israel: si Jugadores.csv tiene una columna tipo "activo"/"estado" para
    # filtrar bajas del club (no confundir con lesión/sanción), decime el nombre
    # y filtro por ahí antes de contar. Por ahora cuento todas las filas del csv.
    if not jugadores.empty:
        total_plantel = len(jugadores)
    else:
        total_plantel = 20  # fallback si todavía no está Jugadores.csv conectado acá

    disponibles = max(0, total_plantel - len(bajas_activas))

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(card("Disponibles", disponibles, "aptos"), unsafe_allow_html=True)
    with c2:
        st.markdown(card("Bajas", len(bajas_activas), "no disponibles", accent=(len(bajas_activas) > 0)), unsafe_allow_html=True)
    with c3:
        st.markdown(card("Riesgo", len(riesgo), "suspensión"), unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    detalle = ""
    for _, row in bajas_activas.iterrows():
        icon = "🤕" if row["tipo"].lower() in ["lesión", "lesion"] else "🟥"
        regreso = row["fecha_regreso"].strftime("%d/%m") if pd.notna(row["fecha_regreso"]) else "Sin fecha"
        detalle += f"<div style='padding:10px 0; border-bottom:1px solid rgba(255,255,255,.04); overflow:hidden;'><span style='color:#F9FAFB'>{icon} {row['nombre'].title()}</span><span style='float:right; color:#9CA3AF;'>{row['tipo']} · {regreso}</span></div>"

    for jugador in riesgo:
        detalle += f"<div style='padding:10px 0; color:#FBBF24; border-bottom:1px solid rgba(255,255,255,.04);'>⚠ {jugador} · riesgo suspensión</div>"

    if detalle == "":
        detalle = "<div style='color:#22C55E; padding:10px 0;'>✓ Plantel completo</div>"

    st.markdown(f"<div style='background:#111827; border-radius:14px; padding:22px; border:1px solid rgba(255,255,255,.04); box-shadow: 0 10px 28px rgba(0,0,0,.28);'>{detalle}</div>", unsafe_allow_html=True)

divider()

# --- ÚLTIMO PARTIDO ANALIZADO ---
section("Último partido analizado")

if df.empty:
    st.markdown(insight("Las estadísticas aparecerán luego del primer partido cargado.", "neutral"), unsafe_allow_html=True)
else:
    ultima_fecha = df["fecha"].max()
    df_ultimo = df[df["fecha"] == ultima_fecha]
    rival_row = jugados[jugados["fecha"] == ultima_fecha]
    rival_last = rival_row["rival"].values[0] if len(rival_row) else f"Fecha {ultima_fecha}"

    pases = len(df_ultimo[df_ultimo["Event"] == "pase"])
    perdidas = len(df_ultimo[df_ultimo["Event"] == "perdida"])
    recuperaciones = len(df_ultimo[df_ultimo["Event"] == "recuperacion"])
    jugadores_num = df_ultimo["Player"].nunique()
    ratio = round(pases / perdidas, 1) if perdidas > 0 else "—"

    escudo_last_b64 = escudo_a_base64(buscar_escudo(rival_last))
    img_last = f"<img src='{escudo_last_b64}' style='width:40px; height:40px; object-fit:contain; border-radius:6px;' />" if escudo_last_b64 else ""
    st.markdown(f"""<div style='display:flex; align-items:center; justify-content:flex-start; gap:10px; margin-bottom:18px;'>
        <div style='color:#9CA3AF; font-size:.9rem;'>Rival analizado: <span style='color:#F9FAFB; font-weight:700'>{rival_last}</span></div>
        {img_last}
    </div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(card("Circulación", pases, "acciones de pase"), unsafe_allow_html=True)
    with c2:
        nivel_val = "alta" if ratio != "—" and ratio >= 5 else "media"
        st.markdown(card("Cuidado balón", ratio, nivel_val), unsafe_allow_html=True)
    with c3:
        st.markdown(card("Recuperaciones", recuperaciones, "fase defensiva"), unsafe_allow_html=True)
    with c4:
        st.markdown(card("Participación", jugadores_num, "jugadores activos"), unsafe_allow_html=True)

divider()
