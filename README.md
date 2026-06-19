# ⚽ Estrella de Berisso — Football Analytics

**Analista de Datos y Rendimiento | Israel Oyhenart**  
*Documentación del trabajo analítico realizado en el Club Atlético Estrella de Berisso*

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/israel-oyhenart/)
[![Portfolio](https://img.shields.io/badge/Portfolio-2563EB?style=for-the-badge&logo=google-chrome&logoColor=white)](https://oyhenart.github.io/iao-analytics/)
[![Dashboard](https://img.shields.io/badge/Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://estrella-cpa.streamlit.app)

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

## 📋 Sobre este repositorio

Este repositorio documenta mi trabajo como **Analista de Datos y Video Analista** en el Club Atlético Estrella de Berisso, comenzando en el primer equipo en el **Torneo Promocional Amateur 2026**.

El enfoque no es solo analizar lo que sucede en el campo, sino construir **sistemas de reportería reproducibles** que transformen datos y video en inteligencia táctica accionable para el cuerpo técnico.

---

## 🗂️ Estructura del repositorio

```
code/                             # 🔄 Torneo Promocional Amateur 2026
    ├── app.py                        # Punto de entrada del dashboard
    ├── requirements.txt
    ├── components/
    │   └── layout.py
    ├── .streamlit/
    │   └── config.toml
    ├── data/
    │   ├── events_clean.csv          # Eventos por partido (generado post-partido)
    │   ├── Jugadores.csv             # Plantilla del equipo
    │   ├── fixture.csv               # Fixture y resultados
    │   ├── sanciones_lesiones.csv    # Bajas por sanción o lesión
    │   └── videos.csv                # Recortes del juego
    ├── static/
    │   ├── escudos/                  # Escudos de los equipos que enfrentamos
    │   ├── escudo.png
    │   └── fotos/                    # Fotos de jugadores
    └── pages/
        ├── 1_Plantel_ficha.py         # Estadísticas por jugador
        ├── 2_Mapa_Cancha.py           # Mapa de eventos + heatmap
        ├── 4_Fixture.py               # Fixture y resultados
        ├── 5_Alertas.py               # Sanciones y lesiones
        ├── 6_Videos.py                # Recortes de videos
        └── 7_Reporte.py               # Reporte automatizado
```

---

## Torneo Promocional Amateur 2026

### Contexto

Pipeline de datos completo para el seguimiento del primer equipo en el **Torneo Promocional Amateur 2026**. La fuente principal de datos es el **video** (partidos locales filmados + transmisiones de visitante), registrado con **LongoMatch** y volcado a FCPython.

### Pipeline de trabajo

```
Video (LongoMatch) → Carga manual FCPython → Python ETL → Dashboard Streamlit → Cuerpo técnico
```

### 🚀 Dashboard en vivo

**[estrella-cpa.streamlit.app](https://estrella-cpa.streamlit.app)**

| Página | Descripción |
|---|---|
| Inicio | Métricas generales del partido |
| Estadísticas | Eventos por jugador, participación y actividad por minuto |
| Mapa de cancha | Posicionamiento, líneas de pase y heatmap por zonas |
| Plantilla | Tarjetas de jugadores con foto, número y posición |
| Fixture | Resultados y próximos partidos del Torneo Promocional |
| Alertas | Sanciones y lesiones con fecha de regreso |
| Videos | Recortes de videos |

#### Cómo correr el dashboard localmente

```bash
pip install streamlit pandas plotly numpy
cd code
streamlit run app.py
```

---

## 🛠️ Tech Stack

### Datos y procesamiento
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org)
[![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white)](https://jupyter.org)

### Visualización y dashboard
[![Streamlit](https://img.shields.io/badge/Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://estrella-cpa.streamlit.app)
[![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-ffffff?style=for-the-badge&logo=matplotlib&logoColor=black)](https://matplotlib.org)

### Video y reportería
[![LongoMatch](https://img.shields.io/badge/LongoMatch-2E7D32?style=for-the-badge&logo=play&logoColor=white)](https://longomatch.com)
[![FCPython](https://img.shields.io/badge/FCPython-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://fcpython.com)

---

## 👤 Autor

**Israel Oyhenart**  
Analista de Datos y Rendimiento aplicado al Fútbol  
Buenos Aires, Argentina

[linkedin.com/in/israel-oyhenart](https://www.linkedin.com/in/israel-oyhenart)

---

*Este repositorio tiene fines de documentación profesional y desarrollo analítico. Los datos publicados cuentan con autorización del Club Atlético Estrella de Berisso.*
