import streamlit as st
import os

# ==========================
# CSS INJECTION
# ==========================
def inject_css():
    st.markdown("""
<style>
/* Reset and Font styling */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Hide default Streamlit elements */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
[data-testid="stSidebarNav"] { display: none; }

/* Main app background */
.stApp {
    background: #090e17; /* Solid dark, executive feel */
    color: #E5E7EB;
}

/* Main container padding */
.block-container {
    padding-top: 2rem !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    padding-bottom: 4rem !important;
    max-width: 1400px;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: #0d131f;
    border-right: 1px solid rgba(255,255,255,0.03);
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: #374151;
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: #4B5563;
}
</style>
""", unsafe_allow_html=True)

# ==========================
# SIDEBAR RENDER
# ==========================
def render_sidebar(base_path):
    
    escudo = os.path.join(base_path, "static", "escudo.png")
    
    with st.sidebar:
        st.markdown("<div style='padding-top: 1rem;'></div>", unsafe_allow_html=True)
        
        if os.path.exists(escudo):
            st.image(escudo, width=70)
            
        st.markdown(
            """
            <div style="margin-bottom: 2rem;">
                <div style="font-size: 1.1rem; font-weight: 800; color: #F9FAFB; line-height: 1.2;">
                    Club Atlético<br>Estrella de Berisso
                </div>
                <div style="color: #9CA3AF; font-size: 0.8rem; font-weight: 500; margin-top: 4px;">
                    La Cebra
                </div>
            </div>
            
            <div style="height: 1px; background: rgba(255,255,255,0.05); margin: 1.5rem 0;"></div>
            
            <div style="margin-bottom: 1.5rem;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #E23E3E; text-transform: uppercase; letter-spacing: 1px;">
                    IAO Football Analytics
                </div>
                <div style="color: #6B7280; font-size: 0.75rem; font-weight: 500; margin-top: 2px;">
                    Datos → Decisiones
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        paginas = [
            ("app.py", "⚽ Inicio"),
            ("pages/1_Estadisticas.py", "📊 Estadísticas"),
            ("pages/2_Mapa_cancha.py", "🗺️ Campo"),
            ("pages/3_Plantilla.py", "👥 Plantilla"),
            ("pages/4_Fixture.py", "🗓️ Fixture"),
            ("pages/5_Alertas.py", "🚨 Alertas"),
            ("pages/6_Videos.py", "🎬 Videos"),
            ("pages/7_Reporte.py", "📄 Reporte")
        ]

        for ruta, nombre in paginas:
            st.page_link(ruta, label=nombre)

# ==========================
# HEADER RENDER
# ==========================
def render_header(subtitle, title):
    st.markdown(
        f"""
        <div style="margin-bottom: 1rem;">
            <div style="color: #E23E3E; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2px;">
                {subtitle}
            </div>
            <h1 style="color: #F8FAFC; margin-top: 4px; font-size: 2.2rem; font-weight: 800; letter-spacing: -0.5px;">
                {title}
            </h1>
        </div>
        """,
        unsafe_allow_html=True
    )
