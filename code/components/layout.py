# ==========================================
# Archivo: components/layout.py (con soporte mobile + st_yled)
# ==========================================
import streamlit as st
import os

# ── FIX: Streamlit quitó st.bokeh_chart en versiones recientes, pero
# st_yled todavía lo referencia al importar -> rompe toda la app.
# Este shim evita el AttributeError sin tocar requirements.txt.
if not hasattr(st, "bokeh_chart"):
    st.bokeh_chart = lambda *args, **kwargs: None

import st_yled  # ← librería de theming, no usa iframes/React (liviana)

# ==========================
# THEME (st_yled) — se llama UNA sola vez por render, es solo CSS/config
# ==========================
def init_theme():
    """
    Inicializa st_yled. Busca .streamlit/st-styled.css si existe (opcional).
    No agrega componentes React ni iframes -> no impacta performance en mobile.
    Si más adelante querés un theme predefinido, podés probar:
        st_yled.init(theme="bauhaus")
    Por ahora lo dejamos neutro para no pisar tus colores actuales (#E23E3E, etc).
    """
    st_yled.init()

# ==========================
# CSS (tu sistema actual, intacto)
# ==========================
def inject_css():
    init_theme()  # ← se ejecuta antes del CSS propio, no interfiere con él

    st.markdown("""
<style>
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
[data-testid="stSidebarNav"] { display: none; }

/* ── BOTÓN HAMBURGUESA MOBILE ── */
/* Reubicado arriba a la DERECHA de la barra de nav, para no pisar
   los íconos del mobile-nav (que ahora vive arriba, centrado/izquierda) */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    background: #E23E3E !important;
    border-radius: 10px !important;
    width: 40px !important;
    height: 40px !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 4px 14px rgba(226,62,62,.45) !important;
    top: 8px !important;
    right: 10px !important;
    left: auto !important;
    position: fixed !important;
    z-index: 10000 !important;
}
[data-testid="collapsedControl"] svg {
    fill: white !important;
    stroke: white !important;
}

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

/* ── MOBILE ── */
@media (max-width: 768px) {
    .block-container {
        /* espacio para la barra fija de arriba (56px) + aire */
        padding-top: 4.75rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-bottom: 1.5rem !important;
    }
    div[data-testid="column"] {
        min-width: 0 !important;
    }
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
# MOBILE NAV (barra superior, ya no inferior)
# ==========================
def render_mobile_nav():
    st.markdown("""
<style>
@media (max-width: 768px) {
    .mobile-nav {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 9998;
        background: #0d131f;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        padding: 8px 54px 8px 10px; /* deja hueco a la derecha para el hamburger */
        display: flex;
        justify-content: space-around;
        align-items: center;
        overflow-x: auto;
    }
    .mobile-nav a {
        color: #9CA3AF;
        text-decoration: none;
        font-size: 0.62rem;
        font-weight: 700;
        text-align: center;
        display: flex;
        flex-direction: column;
        gap: 2px;
        line-height: 1.1;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        flex-shrink: 0;
        padding: 0 4px;
    }
    .mobile-nav a .icon { font-size: 1.1rem; }
}
@media (min-width: 769px) {
    .mobile-nav { display: none; }
}
</style>
<div class="mobile-nav">
    <a href="/"><span class="icon">⚽</span>Inicio</a>
    <a href="/Plantel_ficha"><span class="icon">👥</span>Plantel</a>
    <a href="/Mapa_cancha"><span class="icon">🗺️</span>Campo</a>
    <a href="/Fixture"><span class="icon">🗓️</span>Fixture</a>
    <a href="/Alertas"><span class="icon">🚨</span>Alertas</a>
    <a href="/Reporte"><span class="icon">📄</span>Reporte</a>
</div>
""", unsafe_allow_html=True)

# ==========================
# SIDEBAR
# ==========================
def buscar_escudo_local(base_path):
    """Busca el escudo propio (Local.*) tolerando mayúsculas/minúsculas y extensión."""
    escudos_dir = os.path.join(base_path, "static", "escudos")
    if not os.path.isdir(escudos_dir):
        return None
    candidatos = ["Local.png", "Local.jpg", "Local.jpeg", "Local.webp"]
    archivos_existentes = os.listdir(escudos_dir)
    archivos_lower = {a.lower(): a for a in archivos_existentes}
    for candidato in candidatos:
        ruta = os.path.join(escudos_dir, candidato)
        if os.path.exists(ruta):
            return ruta
        if candidato.lower() in archivos_lower:
            return os.path.join(escudos_dir, archivos_lower[candidato.lower()])
    return None

def render_sidebar(base_path):
    escudo = buscar_escudo_local(base_path)
    if escudo:
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
    paginas = [
        (os.path.join(base_path, "app.py"),                          "Inicio"),
        (os.path.join(base_path, "pages", "1_Plantel_ficha.py"),     "Plantel"),
        (os.path.join(base_path, "pages", "2_Mapa_cancha.py"),       "Campo"),
        (os.path.join(base_path, "pages", "3_Rendimiento_fisico.py"),"Físico"),
        (os.path.join(base_path, "pages", "4_Fixture.py"),           "Fixture"),
        (os.path.join(base_path, "pages", "5_Alertas.py"),           "Alertas"),
        (os.path.join(base_path, "pages", "6_Videos.py"),            "Videos"),
        (os.path.join(base_path, "pages", "7_Reporte.py"),           "Reporte"),
        (os.path.join(base_path, "pages", "8_Player_review.py"),     "Review"),
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
