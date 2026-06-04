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
    st.dataframe(
        df_resumen,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Amarillas totales":
                st.column_config.ProgressColumn(
                    "Amarillas totales",
                    min_value=0,
                    max_value=10
                ),
            "Amarillas en ciclo":
                st.column_config.ProgressColumn(
                    "Amarillas en ciclo",
                    min_value=0,
                    max_value=5
                )
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