# ⚽ Estrella de Berisso — Football Analytics

**Analista de Datos y Rendimiento | Israel Oyhenart**  
*Documentación del trabajo analítico realizado en el Club Atlético Estrella de Berisso*

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/israel-oyhenart/)
[![Portfolio](https://img.shields.io/badge/Portfolio-2563EB?style=for-the-badge&logo=google-chrome&logoColor=white)](https://oyhenart.github.io/iao-analytics/)

---

## 📋 Sobre este repositorio

Este repositorio documenta mi trabajo como **Analista de Datos y Video Analista** en el Club Atlético Estrella de Berisso, comenzando en las divisiones juveniles y con proyección al primer equipo en el **Torneo Promocional Amateur**.

El enfoque no es solo analizar lo que sucede en el campo, sino construir **sistemas de reportería reproducibles** que transformen datos y video en inteligencia táctica accionable para el cuerpo técnico.

---

## 🗂️ Estructura del repositorio

```
Estrella-Berisso-Analytics/
│
├── juveniles/                        # ✅ Trabajo finalizado
│   ├── data/
│   │   ├── raw/                      # Datasets originales de FCPython (.xlsx)
│   │   └── cleaned/                  # Datos procesados y normalizados
│   ├── notebooks/
│   │   ├── 7ma.ipynb
│   │   ├── 8va.ipynb
│   └── outputs/                      # Visualizaciones generadas
│
└── torneo_promocional/               # 🔄 En desarrollo
    ├── data/
    │   ├── raw/                      # Datos crudos por partido
    │   └── cleaned/                  # Datos procesados
    ├── notebooks/
    │   ├── vs-metalurgico.ipynb
    │   ├── vs-atlpilar.ipynb
    ├── src/
    │   ├── parser_fcpython.py        # Procesamiento de datos FCPython
    │   └── viz_utils.py              # Funciones reutilizables de visualización
    ├── outputs/
    │   ├── visualizaciones/
    │   └── reportes/                 # Reportes HTML por partido
    └── workflow/                     # Automatizaciones n8n
```

---

## 📁 Fase 1 — Juveniles

### Contexto
Trabajo desarrollado para las **divisiones juveniles** del club. Los datos fueron obtenidos desde [FCPython](https://fcpython.com/) y procesados con Python.

### Análisis desarrollados

| Notebook | Descripción |
|---|---|
| `8va.ipynb` | Mapas de calor por jugador y zonas de influencia colectiva |
| `8va.ipynb` | Redes de pases y circuitos de juego |
| `7ma.ipynb` | Dashboard integrado de rendimiento por partido |

### Fuente de datos
- **FCPython** — datasets descargados en formato `.csv`

---

## 📁 Fase 2 — Torneo Promocional Amateur

### Contexto
Pipeline de datos completo para el seguimiento del primer equipo en el **Torneo Promocional Amateur**. La fuente principal de datos es el **video** (partidos locales filmados + transmisiones de visitante), registrado y codificado con **LongoMatch** y volcado manualmente a FCPython.

### Pipeline de trabajo

```
Video (LongoMatch) → Carga manual FCPython → Python ETL → Visualizaciones → Reporte HTML
```

### Módulos en desarrollo

- **Análisis táctico propio** — posicionamiento, presión, circuitos de juego
- **Scouting de rivales** — tendencias, debilidades y patrones detectados por partido
- **Reporte HTML post-partido** — documento interactivo con visualizaciones + clips de video embebidos (10 seg), entregable directo al cuerpo técnico

---

## 🛠️ Tech Stack

### Datos y procesamiento
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white)

### Visualización
![Matplotlib](https://img.shields.io/badge/Matplotlib-ffffff?style=for-the-badge&logo=matplotlib&logoColor=black)
![mplsoccer](https://img.shields.io/badge/mplsoccer-2E7D32?style=for-the-badge&logo=python&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)

### Video y reportería
![LongoMatch](https://img.shields.io/badge/LongoMatch-2E7D32?style=for-the-badge&logo=play&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)

### Automatización
![n8n](https://img.shields.io/badge/n8n-FF6D5B?style=for-the-badge&logo=n8n&logoColor=white)

---

## 🔄 Próximos pasos

- [ ] Subir notebooks y outputs de juveniles
- [ ] Primer pipeline completo del Torneo Promocional
- [ ] Template de reporte HTML post-partido con clips embebidos
- [ ] Automatización de reportes semanales vía n8n

---

## 👤 Autor

**Israel Oyhenart**  
Analista de Datos y Rendimiento aplicado al Fútbol  
Buenos Aires, Argentina

[linkedin.com/in/israel-oyhenart](https://www.linkedin.com/in/israel-oyhenart)

---

*Este repositorio tiene fines de documentación profesional y desarrollo analítico.*
