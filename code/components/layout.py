# ==========================
# L1) IMPORTS
# ==========================

import streamlit as st
import os
# ==========================
# L2) CSS GLOBAL
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
#0B1120,
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
#0B1120,
#111827
);

border-right:
1px solid rgba(255,255,255,.05);

}

button[role="tab"]{

background:#111827;

border:none;

border-radius:10px;

}

button[aria-selected="true"]{

background:#E23E3E;

}

::-webkit-scrollbar{
width:8px;
}

::-webkit-scrollbar-thumb{

background:#374151;

border-radius:999px;

}

html,
body{

font-family:
Inter,
sans-serif;

}

</style>
""",
unsafe_allow_html=True)
# ==========================
# L3) SIDEBAR
# ==========================

def render_sidebar(base_path):

    escudo = os.path.join(
        base_path,
        "static",
        "escudo.png"
    )

    if os.path.exists(
        escudo
    ):

        st.sidebar.image(
            escudo,
            width=82
        )

    st.sidebar.markdown(
        """

<div style="

padding-bottom:18px;

">

<div style="

font-size:1.1rem;

font-weight:800;

color:#F9FAFB;

">

Club Atlético

<br>

Estrella de Berisso

</div>


<div style="

margin-top:8px;

color:#6B7280;

letter-spacing:3px;

font-size:.72rem;

text-transform:uppercase;

">

La Cebra

</div>


<div style="

margin-top:20px;

height:1px;

background:

linear-gradient(
to right,
#E23E3E,
transparent
);

">

</div>


<div style="

margin-top:20px;

color:#9CA3AF;

font-size:.72rem;

letter-spacing:2px;

text-transform:uppercase;

">

IAO Football Analytics

</div>


<div style="

margin-top:6px;

color:#6B7280;

font-size:.80rem;

">

Datos → contexto → decisiones

</div>

</div>

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
# L4) HEADER
# ==========================

def render_header(
    subtitle,
    title
):

    st.markdown(
        f"""

<div style="

margin-bottom:34px;

">

<div style="

color:#E23E3E;

font-size:.78rem;

font-weight:700;

letter-spacing:3px;

text-transform:uppercase;

">

{subtitle}

</div>


<div style="

font-size:2.6rem;

font-weight:900;

color:#F9FAFB;

margin-top:8px;

line-height:1;

">

{title}

</div>


<div style="

margin-top:16px;

height:1px;

background:

linear-gradient(
to right,
rgba(226,62,62,.35),
transparent
);

">

</div>


</div>

""",
unsafe_allow_html=True
)











