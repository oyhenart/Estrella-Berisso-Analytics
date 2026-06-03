import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="Alertas", page_icon="🚨", layout="wide")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@st.cache_data(ttl=0)
def cargar_alertas():
    df = pd.read_csv(os.path.join(BASE, "data", "sanciones_lesiones.csv"))
    if not df.empty and "fecha_regreso" in df.columns:
        df["fecha_regreso"] = pd.to_datetime(df["fecha_regreso"], dayfirst=True, errors="coerce")
    return df

def umbral_suspension(sanciones_cumplidas):
    """Devuelve cuántas amarillas se necesitan para la próxima suspensión."""
    if sanciones_cumplidas == 0:
        return 5
    elif sanciones_cumplidas == 1:
        return 4
    elif sanciones_cumplidas == 2:
        return 3
    else:
        return 2

# --- Sidebar ---
escudo_path = os.path.join(BASE, "static", "escudo.png")
if os.path.exists(escudo_path):
    st.sidebar.image(escudo_path, width=72)
st.sidebar.markdown("""
<div style='padding: 6px 0 20px 0'>
    <div style='font-size:1.05em; font-weight:700; color:#EEEEEE; line-height:1.3'>Club Atlético<br>Estrella de Berisso</div>
    <div style='font-size:0.72em; color:#555; text-transform:uppercase; letter-spacing:2px; margin-top:3px'>La Cebra</div>
    <div style='margin: 16px 0; height:1px; background:linear-gradient(to right, #E63946, transparent)'></div>
    <div style='font-size:0.7em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:2px'>IAO Football Analytics</div>
    <div style='font-size:0.68em; color:#444; margin-top:4px; font-style:italic'>Transformo datos en decisiones.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style='margin-bottom:28px'>
    <p style='font-size:0.72em; font-weight:600; color:#E63946; text-transform:uppercase; letter-spacing:3px; margin:0 0 6px 0'>Plantel</p>
    <h1 style='font-size:2em; font-weight:800; margin:0; color:#EEEEEE; letter-spacing:-0.5px'>Alertas</h1>
</div>
""", unsafe_allow_html=True)

df = cargar_alertas()

if df.empty:
    st.info("✅ Sin novedades. No hay tarjetas, sanciones ni lesiones registradas.")
    st.stop()

hoy = pd.Timestamp(date.today())

# --- Separar por tipo ---
amarillas = df[df["tipo"].str.lower() == "amarilla"].copy()
sanciones = df[df["tipo"].str.lower().isin(["sanción", "sancion", "roja directa"])].copy()
lesiones = df[df["tipo"].str.lower().isin(["lesión", "lesion"])].copy()

# --- Métricas globales ---
bajas_activas = 0
if not sanciones.empty:
    bajas_activas += len(sanciones[sanciones["fecha_regreso"].isna() | (sanciones["fecha_regreso"] >= hoy)])
if not lesiones.empty:
    bajas_activas += len(lesiones[lesiones["fecha_regreso"].isna() | (lesiones["fecha_regreso"] >= hoy)])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Bajas activas", bajas_activas)
col2.metric("Lesionados", len(lesiones[lesiones["fecha_regreso"].isna() | (lesiones["fecha_regreso"] >= hoy)]) if not lesiones.empty else 0)
col3.metric("Sancionados", len(sanciones[sanciones["fecha_regreso"].isna() | (sanciones["fecha_regreso"] >= hoy)]) if not sanciones.empty else 0)
col4.metric("Con amarillas", amarillas["nombre"].nunique() if not amarillas.empty else 0)

st.divider()

# --- Tarjetas amarillas ---
if not amarillas.empty:
    st.subheader("🟨 Tarjetas amarillas acumuladas")

    resumen = []
    for jugador, grupo in amarillas.groupby("nombre"):
        total = len(grupo)
        # Calcular cuántas sanciones ya cumplió este jugador
        sanciones_jugador = len(sanciones[sanciones["nombre"] == jugador]) if not sanciones.empty else 0
        umbral = umbral_suspension(sanciones_jugador)
        # Amarillas dentro del ciclo actual (después de la última sanción cumplida)
        amarillas_ciclo = total - sum([5, 4, 3, 2][:sanciones_jugador]) if sanciones_jugador > 0 else total
        amarillas_ciclo = max(amarillas_ciclo, 0)
        faltan = umbral - amarillas_ciclo

        if faltan <= 0:
            estado = "🔴 SUSPENDIDO"
        elif faltan == 1:
            estado = "🟠 EN RIESGO"
        else:
            estado = "🟡 Seguimiento"

        resumen.append({
            "Jugador": jugador.title(),
            "Amarillas totales": total,
            "Amarillas en ciclo": amarillas_ciclo,
            "Umbral": umbral,
            "Faltan para suspensión": max(faltan, 0),
            "Estado": estado,
        })

    df_resumen = pd.DataFrame(resumen).sort_values("Amarillas en ciclo", ascending=False)
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)
    st.divider()

# --- Sanciones activas ---
if not sanciones.empty:
    activas = sanciones[sanciones["fecha_regreso"].isna() | (sanciones["fecha_regreso"] >= hoy)]
    if not activas.empty:
        st.subheader("🟥 Sancionados")
        for _, row in activas.iterrows():
            regreso = row["fecha_regreso"].strftime("%d/%m/%Y") if pd.notna(row["fecha_regreso"]) else "Sin fecha definida"
            col1, col2, col3 = st.columns([2, 4, 2])
            col1.markdown(f"🟥 **{str(row['nombre']).title()}**")
            col2.markdown(row["motivo"])
            col3.markdown(f"📅 Regresa: **{regreso}**")
        st.divider()

# --- Lesiones activas ---
if not lesiones.empty:
    activas = lesiones[lesiones["fecha_regreso"].isna() | (lesiones["fecha_regreso"] >= hoy)]
    if not activas.empty:
        st.subheader("🤕 Lesionados")
        for _, row in activas.iterrows():
            regreso = row["fecha_regreso"].strftime("%d/%m/%Y") if pd.notna(row["fecha_regreso"]) else "Sin fecha definida"
            col1, col2, col3 = st.columns([2, 4, 2])
            col1.markdown(f"🤕 **{str(row['nombre']).title()}**")
            col2.markdown(row["motivo"])
            col3.markdown(f"📅 Regresa: **{regreso}**")
        st.divider()

# --- Historial ---
with st.expander("Ver historial completo"):
    st.dataframe(df, use_container_width=True, hide_index=True)