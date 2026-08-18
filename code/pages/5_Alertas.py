import streamlit as st
import pandas as pd
import os
from datetime import date

from components.layout import (
    inject_css,
    render_sidebar,
    render_header
)

st.set_page_config(page_title="Alertas", page_icon="🚨", layout="wide")

inject_css()

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
render_sidebar(BASE)

render_header(
    "Plantel",
    "Alertas"
)

@st.cache_data(ttl=0)
def cargar_alertas():
    df = pd.read_csv(os.path.join(BASE, "data", "sanciones_lesiones.csv"))
    if not df.empty and "fecha_regreso" in df.columns:
        df["fecha_regreso"] = pd.to_datetime(df["fecha_regreso"], dayfirst=True, errors="coerce")
    if not df.empty and "fecha_cumplimiento" in df.columns:
        df["fecha_cumplimiento"] = pd.to_datetime(df["fecha_cumplimiento"], dayfirst=True, errors="coerce")
    if not df.empty and "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    return df

def contar_amarillas_ciclo(nombre, df_amarillas, df_sanciones):
    """Cuenta amarillas desde la última sanción cumplida."""
    
    # Obtener sanciones cumplidas del jugador
    sanciones_jugador = df_sanciones[df_sanciones["nombre"] == nombre].copy()
    
    if sanciones_jugador.empty:
        # Sin sanciones: contar todas las amarillas
        amarillas_jugador = df_amarillas[df_amarillas["nombre"] == nombre]
        return len(amarillas_jugador)
    
    # Filtrar sanciones con fecha de cumplimiento
    sanciones_cumplidas = sanciones_jugador[sanciones_jugador["fecha_cumplimiento"].notna()]
    
    if sanciones_cumplidas.empty:
        # No hay sanciones cumplidas aún: contar todas las amarillas
        amarillas_jugador = df_amarillas[df_amarillas["nombre"] == nombre]
        return len(amarillas_jugador)
    
    # Obtener la fecha de la última sanción cumplida
    ultima_sancion = sanciones_cumplidas["fecha_cumplimiento"].max()
    
    # Contar solo amarillas DESPUÉS de esa fecha
    amarillas_jugador = df_amarillas[df_amarillas["nombre"] == nombre].copy()
    
    # Si no tiene columna fecha, asignar la fecha como NaT (se contarán todas)
    if "fecha" not in amarillas_jugador.columns:
        return len(amarillas_jugador)
    
    amarillas_despues = amarillas_jugador[amarillas_jugador["fecha"] > ultima_sancion]
    return len(amarillas_despues)

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
    for jugador in amarillas["nombre"].unique():
        total = len(amarillas[amarillas["nombre"] == jugador])
        
        # Contar sanciones cumplidas del jugador
        sanciones_jugador = sanciones[sanciones["nombre"] == jugador].copy() if not sanciones.empty else pd.DataFrame()
        sanciones_cumplidas = len(sanciones_jugador[sanciones_jugador["fecha_cumplimiento"].notna()]) if not sanciones_jugador.empty else 0
        
        # Obtener umbral según sanciones cumplidas
        umbral = umbral_suspension(sanciones_cumplidas)
        
        # Contar amarillas en el ciclo actual (después de última sanción cumplida)
        amarillas_ciclo = contar_amarillas_ciclo(jugador, amarillas, sanciones) if not sanciones.empty else total
        
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
    st.dataframe(
        df_resumen,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Amarillas totales": st.column_config.NumberColumn("Amarillas totales"),
            "Amarillas en ciclo": st.column_config.NumberColumn("Amarillas en ciclo")
        }
    )
    st.divider()

# --- Sanciones activas ---
if not sanciones.empty:
    activas = sanciones[sanciones["fecha_regreso"].isna() | (sanciones["fecha_regreso"] >= hoy)]
    if not activas.empty:
        st.subheader("🟥 Sancionados")
        for _, row in activas.iterrows():
            regreso = row["fecha_regreso"].strftime("%d/%m/%Y") if pd.notna(row["fecha_regreso"]) else "Sin fecha definida"
            with st.container(border=True):

                col1, col2, col3 = st.columns(
                    [2, 4, 2]
                )

                col1.markdown(f"🟥 **{str(row['nombre']).title()}**")
                col2.markdown(row.get("motivo", "—"))
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
    st.divider()
