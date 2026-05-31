# Estrella de Berisso 

**Analista de Datos y Rendimiento | Israel Oyhenart**  
*Documentación del trabajo analítico realizado en el Club Atlético Estrella de Berisso*

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/israel-oyhenart/)
[![Portfolio](https://img.shields.io/badge/Portfolio-2563EB?style=for-the-badge&logo=google-chrome&logoColor=white)](https://oyhenart.github.io/iao-analytics/)

---

## ⚠️ Aviso legal y de privacidad

Este repositorio es de **carácter público** con fines de documentación profesional y desarrollo analítico. Se aplican las siguientes condiciones:

- Los **datos de jugadores son anonimizados** o utilizados con consentimiento expreso del Club Atlético Estrella de Berisso y sus integrantes.
- Este repositorio **no contiene información personal sensible** (DNI, datos de salud, domicilios, ni información financiera de ningún jugador o integrante del club).
- Los nombres que puedan aparecer en los datasets corresponden a **apodos o nombres de pila de uso interno** acordados con el club para fines analíticos.
- El **Club Atlético Estrella de Berisso** mantiene la propiedad institucional de los datos generados en contexto oficial. Este repositorio documenta el trabajo técnico y metodológico del analista.
- Queda prohibida la **reutilización comercial** de los datos, visualizaciones o reportes sin autorización expresa del club y del autor.
- El código fuente (scripts de Python, dashboards) se publica bajo licencia **MIT** y puede ser reutilizado libremente con atribución.

---

## Sobre este repositorio

Este repositorio documenta mi trabajo como **Analista de Datos y Video Analista** en el Club Atlético Estrella de Berisso, comenzando en las divisiones juveniles y con proyección al primer equipo en el **Torneo Promocional Amateur**.

El enfoque no es solo analizar lo que sucede en el campo, sino construir **sistemas de reportería reproducibles** que transformen datos y video en inteligencia táctica accionable para el cuerpo técnico.

---

## Estructura del repositorio

```
Estrella-Berisso-Analytics/
│
└── torneo_promocional/               # 🔄 En desarrollo
    ├── data/
    │   ├── raw/                      # Datos crudos por partido
    │   └── cleaned/                  # Datos procesados
    ├── dashboard/                    # 🆕 Dashboard interactivo (Streamlit)
    │   ├── app.py                    # Punto de entrada
    │   ├── pages/
    │   │   ├── 1_Estadisticas.py
    │   │   └── 2_Mapa_Cancha.py
    │   └── data/
    │       └── events_clean.csv
```

---

## Torneo Promocional Amateur

### Contexto

Pipeline de datos completo para el seguimiento del primer equipo en el **Torneo Promocional Amateur**. La fuente principal de datos es el **video** (partidos locales filmados + transmisiones de visitante), registrado y codificado con **LongoMatch** y volcado a FCPython.

### Pipeline de trabajo

```
Video (LongoMatch) → Carga manual FCPython → Python ETL → Dashboard Streamlit → Cuerpo técnico
```

### Dashboard interactivo

El dashboard está construido con **Streamlit** y permite al cuerpo técnico consultar en tiempo real:

- **Estadísticas por jugador** — eventos, participación, actividad por minuto
- **Mapa de eventos en cancha** — posicionamiento, líneas de pase, zonas de actividad
- **Heatmap por zonas** — grilla proporcional a la cancha real (130x90)

#### Cómo correr el dashboard localmente

```bash
# Instalar dependencias
pip install streamlit pandas plotly numpy

# Navegar a la carpeta del dashboard
cd torneo_promocional/dashboard

# Correr la app
streamlit run app.py
```

### Módulos en desarrollo

- **Análisis táctico propio** — posicionamiento, presión, circuitos de juego
- **Scouting de rivales** — tendencias y patrones por partido
- **Reporte HTML post-partido** — documento interactivo con visualizaciones entregable al cuerpo técnico

---

## 🛠️ Tech Stack

### Datos y procesamiento
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org)
[![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white)](https://jupyter.org)

### Visualización y dashboard
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-ffffff?style=for-the-badge&logo=matplotlib&logoColor=black)](https://matplotlib.org)

### Video y reportería
[![LongoMatch](https://img.shields.io/badge/LongoMatch-2E7D32?style=for-the-badge&logo=play&logoColor=white)](https://longomatch.com)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)

---

## 🔄 Próximos pasos

- [x] Dashboard Streamlit con mapa de cancha y estadísticas
- [ ] Páginas de Alertas y Fixture en el dashboard
- [ ] Primer pipeline completo del Torneo Promocional

---

## 👤 Autor

**Israel Oyhenart**  
Analista de Datos y Rendimiento aplicado al Fútbol  
Buenos Aires, Argentina

[linkedin.com/in/israel-oyhenart](https://www.linkedin.com/in/israel-oyhenart)

---

*Este repositorio tiene fines de documentación profesional y desarrollo analítico. Los datos publicados cuentan con autorización del Club Atlético Estrella de Berisso.*
