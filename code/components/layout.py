# ==========================================
# Archivo: components/layout.py (Optimizado)
# ==========================================
import streamlit as st
import os

# ==========================
# CSS
# ==========================
def inject_css():
    st.markdown("""
<style>
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
[data-testid="stSidebarNav"] { display: none; }
.stApp {
    background: #090e17;
    color: #E5E7EB;
}
.block-container {
    padding-top: 2rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 1450px;
}
section[data-testid="stSidebar"] {
    background: #0d131f;
    border-right: 1px solid rgba(255,255,255,0.03);
}
html, body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ==========================
# SIDEBAR
# ==========================
def render_sidebar(base_path):
    escudo = os.path.join(base_path, "static", "escudo.png")

    if os.path.exists(escudo):
        st.sidebar.image(escudo, width=80)

    st.sidebar.markdown("""
<div style="margin-bottom: 20px;">
    <h3 style="color: #F9FAFB; margin: 0; font-size: 1.25rem; font-weight: 800; line-height: 1.2;">Club Atlético<br>Estrella de Berisso</h3>
    <small style='color:#6B7280; font-weight: 600;'>La Cebra</small>
</div>
<hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.05); margin: 20px 0;">
<div style="margin-bottom: 24px;">
    <div style="color: #E23E3E; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px;">IAO Football Analytics</div>
    <small style='color:#6B7280; font-weight: 500;'>Datos → Decisiones</small>
</div>
""", unsafe_allow_html=True)

    # page_link acepta rutas absolutas al archivo .py
    # base_path = .../code/  →  pages están en .../code/pages/
    paginas = [
        (os.path.join(base_path, "app.py"),                   "⚽ Inicio"),
        (os.path.join(base_path, "pages", "1_Plantel_ficha.py"), "👥 Plantel"),
        (os.path.join(base_path, "pages", "2_Mapa_cancha.py"),   "🗺️ Campo"),
        (os.path.join(base_path, "pages", "3_Plantilla.py"),     "📋 Plantilla"),
        (os.path.join(base_path, "pages", "4_Fixture.py"),       "🗓️ Fixture"),
        (os.path.join(base_path, "pages", "5_Alertas.py"),       "🚨 Alertas"),
        (os.path.join(base_path, "pages", "6_Videos.py"),        "🎬 Videos"),
        (os.path.join(base_path, "pages", "7_Reporte.py"),       "📄 Reporte"),
    ]

    for ruta_abs, nombre in paginas:
        if os.path.exists(ruta_abs):
            st.sidebar.page_link(ruta_abs, label=nombre)

# ==========================
# HEADER
# ==========================
def render_header(subtitle, title):
    st.markdown(f"""
<div style="margin-bottom: 24px;">
    <div style="color:#E23E3E; font-size:.85rem; font-weight:700; text-transform: uppercase; letter-spacing: 2px;">
        {subtitle}
    </div>
    <h1 style="color:white; margin-top:6px; font-weight: 800; font-size: 2.2rem; letter-spacing: -0.5px;">
        {title}
    </h1>
</div>
""", unsafe_allow_html=True)
