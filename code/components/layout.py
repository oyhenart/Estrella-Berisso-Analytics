import streamlit as st
import os


# ==========================
# CSS
# ==========================

def inject_css():

    st.markdown("""
<style>

#MainMenu{
visibility:hidden;
}

footer{
visibility:hidden;
}

[data-testid="stSidebarNav"]{
display:none;
}

.stApp{
background:
linear-gradient(
180deg,
#09111F,
#111827
);
}

.block-container{
padding-top:2rem;
padding-left:2rem;
padding-right:2rem;
max-width:1500px;
}

section[data-testid="stSidebar"]{

background:
linear-gradient(
180deg,
#09111F,
#111827
);

border-right:
1px solid rgba(255,255,255,.05);

}

html,
body{

font-family:
sans-serif;

}

</style>
""",
unsafe_allow_html=True)


# ==========================
# SIDEBAR
# ==========================

def render_sidebar(base_path):

    escudo = os.path.join(
        base_path,
        "static",
        "escudo.png"
    )

    if os.path.exists(escudo):

        st.sidebar.image(
            escudo,
            width=80
        )

    st.sidebar.markdown(
        """
Club Atlético  
**Estrella de Berisso**

<small style='color:#6B7280'>
La Cebra
</small>

---

IAO Football Analytics

<small style='color:#6B7280'>
Datos → decisiones
</small>

""",
unsafe_allow_html=True
    )

    paginas = [

        ("app.py","⚽ Inicio"),

        ("pages/1_Estadisticas.py","📊 Estadísticas"),

        ("pages/2_Mapa_cancha.py","🗺️ Campo"),

        ("pages/3_Plantilla.py","👥 Plantilla"),

        ("pages/4_Fixture.py","🗓️ Fixture"),

        ("pages/5_Alertas.py","🚨 Alertas"),

        ("pages/6_Videos.py","🎬 Videos"),

        ("pages/7_Reporte.py","📄 Reporte")

    ]

    for ruta, nombre in paginas:

        st.sidebar.page_link(
            ruta,
            label=nombre
        )


# ==========================
# HEADER
# ==========================

def render_header(
    subtitle,
    title
):

    st.markdown(
f"""

<div>

<div style="
color:#E23E3E;
font-size:.8rem;
font-weight:700;
">

{subtitle}

</div>

<h1 style="
color:white;
margin-top:8px;
">

{title}

</h1>

</div>

""",
unsafe_allow_html=True
)
