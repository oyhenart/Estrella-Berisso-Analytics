import streamlit as st
import os


def inject_css():
    st.markdown("""
    <style>
    #MainMenu {visibility:hidden;}
    footer {visibility:hidden;}
    header {visibility:hidden;}
    [data-testid="stSidebarNav"] {display:none;}

    section[data-testid="stSidebar"]{
        background-color:#111827;
        border-right:1px solid #1F2937;
    }

    .block-container{
        padding-top:1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar(base_path):
    escudo_path = os.path.join(base_path, "static", "escudo.png")

    if os.path.exists(escudo_path):
        st.sidebar.image(escudo_path, width=72)

    st.sidebar.markdown("""
    <div style='padding:4px 0 20px 0'>
        <div style='font-size:0.95em;font-weight:700;color:#F9FAFB;line-height:1.4'>
            Club Atlético<br>Estrella de Berisso
        </div>

        <div style='font-size:0.68em;color:#6B7280;text-transform:uppercase;
                    letter-spacing:2px;margin-top:3px'>
            La Cebra
        </div>

        <div style='margin:14px 0;height:1px;
                    background:linear-gradient(to right,#E23E3E55,transparent)'>
        </div>

        <div style='font-size:0.65em;font-weight:600;color:#9CA3AF;
                    text-transform:uppercase;letter-spacing:2px'>
            IAO Football Analytics
        </div>

        <div style='font-size:0.63em;color:#6B7280;
                    margin-top:4px;font-style:italic'>
            Transformo datos en decisiones.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")

    st.sidebar.page_link(
        "app.py",
        label="⚽ Inicio"
    )

    st.sidebar.page_link(
        "pages/1_Estadisticas.py",
        label="📊 Estadísticas"
    )

    st.sidebar.page_link(
        "pages/2_Mapa_cancha.py",
        label="🗺️ Mapa de cancha"
    )

    st.sidebar.page_link(
        "pages/3_Plantilla.py",
        label="👥 Plantilla"
    )

    st.sidebar.page_link(
        "pages/4_Fixture.py",
        label="🗓️ Fixture"
    )

    st.sidebar.page_link(
        "pages/5_Alertas.py",
        label="🚨 Alertas"
    )

    st.sidebar.page_link(
        "pages/6_Videos.py",
        label="🎬 Videos"
    )


def render_header(subtitle, title):
    st.markdown(
        f"""
        <div style='margin-bottom:24px'>

            <p style='font-size:0.68em;
                      font-weight:600;
                      color:#E23E3E;
                      text-transform:uppercase;
                      letter-spacing:3px;
                      margin:0 0 4px 0'>
                {subtitle}
            </p>

            <h1 style='font-size:1.9em;
                       font-weight:800;
                       margin:0;
                       color:#F9FAFB;
                       letter-spacing:-0.5px'>
                {title}
            </h1>

        </div>
        """,
        unsafe_allow_html=True
    )
