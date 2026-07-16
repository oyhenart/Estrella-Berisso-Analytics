"""
radar_percentil_prototipo.py — Prototipo: radar por percentil (estilo Opta Analyst)
=====================================================================================
Para integrar en 1_Plantel_ficha.py, reemplazando (u ofreciendo como alternativa a)
la función radar_jugador() actual, que normaliza contra una escala fija hardcodeada
(ESCALA_RADAR). Acá en cambio:

  1) Todas las métricas se normalizan "por 90 minutos" (per90), para que sean
     comparables entre jugadores con distinta cantidad de minutos jugados.
  2) El eje del radar no es el valor bruto sino el PERCENTIL del jugador
     respecto al resto del plantel EN SU MISMA POSICIÓN — igual que hacen
     los radares de Opta Analyst, pero comparando contra tu propio plantel
     en vez de contra las 5 grandes ligas europeas (que sería una referencia
     sin sentido para un torneo amateur).
  3) Se filtra la muestra de comparación por minutos mínimos jugados, para
     que un jugador con 10 minutos y 1 gol no distorsione el percentil de
     nadie ni el suyo propio.
  4) El tamaño de la muestra de comparación (n) queda explícito en el
     gráfico — importante para que el cuerpo técnico calibre cuánto
     confiar en un percentil calculado sobre 5-6 jugadores.

REQUIERE: la función calcular_minutos(nombre, eventos) que ya existe en
1_Plantel_ficha.py — se pasa como parámetro para no duplicar esa lógica acá
(ver nota sobre duplicación de lógica entre páginas que ya charlamos).

Motor de gráfico: Barpolar en vez de Scatterpolar — mismo Plotly, cambia el
tipo de traza para lograr los "gajos" tipo torta de los radares de Opta,
en vez de la línea rellena que tenías antes.
"""

import pandas as pd
import plotly.graph_objects as go


# ══════════════════════════════════════════════════════════════════════════
# Configuración: métricas por posición y su categoría (color del gajo)
# ══════════════════════════════════════════════════════════════════════════
METRICAS_RADAR_POS = {
    "Arquero":        ["despeje", "recuperacion", "pase"],
    "Defensor":       ["recuperacion", "despeje", "falta cometida", "pase", "conduccion"],
    "Mediocampista":  ["pase", "recuperacion", "conduccion", "centro", "remate"],
    "Delantero":      ["remate", "gol", "centro", "conduccion", "recuperacion"],
}

# Agrupación temática, igual criterio visual que los radares de Opta
# (ataque / posesión / defensa en vez de un solo color parejo)
CATEGORIA_METRICA = {
    "pase": "posesion", "conduccion": "posesion",
    "centro": "ataque", "remate": "ataque", "gol": "ataque",
    "recuperacion": "defensa", "despeje": "defensa", "falta cometida": "defensa",
}

COLOR_CATEGORIA = {
    "ataque":   "#F87171",
    "posesion": "#818CF8",
    "defensa":  "#F472B6",
}

LABEL_METRICAS = {
    "pase": "Pases", "recuperacion": "Recuperac.", "despeje": "Despejes",
    "falta cometida": "Faltas", "conduccion": "Cond.", "remate": "Remates",
    "gol": "Goles", "centro": "Centros",
}

EVENTOS_BASE = ["pase", "recuperacion", "conduccion", "despeje",
                "falta cometida", "remate", "gol", "centro"]


# ══════════════════════════════════════════════════════════════════════════
# Paso 1 — Tabla per-90 de todo el plantel (una vez por sesión, cacheada)
# ══════════════════════════════════════════════════════════════════════════
def stats_per90_plantel(eventos: pd.DataFrame, jugadores: pd.DataFrame,
                         calcular_minutos_fn) -> pd.DataFrame:
    """
    Devuelve un DataFrame con una fila por jugador: minutos jugados en la
    temporada y cada métrica de evento normalizada a "por 90 minutos".

    calcular_minutos_fn: pasar la función calcular_minutos ya existente en
    1_Plantel_ficha.py, para reutilizar esa lógica en vez de duplicarla.
    """
    filas = []
    for _, row in jugadores.iterrows():
        nombre = row["nombre"]
        minutos = calcular_minutos_fn(nombre, eventos)
        j = eventos[eventos["Player"].str.lower() == nombre.lower()]
        factor90 = (90 / minutos) if minutos > 0 else 0

        fila = {"jugador": nombre, "posicion": row["posicion"], "minutos": minutos}
        for ev in EVENTOS_BASE:
            cantidad = len(j[j["Event"] == ev])
            fila[f"{ev}_p90"] = round(cantidad * factor90, 2)
        filas.append(fila)
    return pd.DataFrame(filas)


# ══════════════════════════════════════════════════════════════════════════
# Paso 2 — Percentil de un jugador contra su posición
# ══════════════════════════════════════════════════════════════════════════
def percentil_jugador(nombre: str, posicion: str, stats_p90: pd.DataFrame,
                       metricas: list, minutos_minimos: int = 90) -> dict:
    """
    Percentil del jugador en cada métrica, respecto a los demás jugadores
    de SU MISMA POSICIÓN con al menos `minutos_minimos` jugados. Devuelve
    también el tamaño de esa muestra de comparación (n_muestra), clave
    para no mostrar un percentil "de élite" calculado sobre 3 jugadores.
    """
    grupo = stats_p90[
        (stats_p90["posicion"] == posicion) & (stats_p90["minutos"] >= minutos_minimos)
    ]
    n_muestra = len(grupo)
    resultado = {"n_muestra": n_muestra, "percentiles": {}, "valores_p90": {}}
    if n_muestra == 0:
        return resultado

    fila_jug = stats_p90[stats_p90["jugador"] == nombre]
    if fila_jug.empty:
        return resultado
    fila_jug = fila_jug.iloc[0]

    for m in metricas:
        col = f"{m}_p90"
        valor = fila_jug[col]
        pct = (grupo[col] <= valor).mean() * 100
        resultado["percentiles"][m] = round(pct)
        resultado["valores_p90"][m] = valor
    return resultado


# ══════════════════════════════════════════════════════════════════════════
# Paso 3 — Gráfico Barpolar (radar tipo Opta) con percentiles
# ══════════════════════════════════════════════════════════════════════════
def radar_percentil_jugador(nombre: str, posicion: str, stats_p90: pd.DataFrame,
                             minutos_minimos: int = 90,
                             metricas: list | None = None) -> go.Figure:
    """
    Radar de gajos coloreados por categoría (ataque / posesión / defensa),
    con el percentil como longitud del gajo y el valor per-90 real en el
    hover. El título deja explícito contra cuántos jugadores se compara.
    """
    metricas = metricas or METRICAS_RADAR_POS.get(posicion, EVENTOS_BASE[:5])
    datos = percentil_jugador(nombre, posicion, stats_p90, metricas, minutos_minimos)
    n = datos["n_muestra"]

    # Con muestra muy chica el percentil no es confiable — se avisa en vez
    # de graficar un número que puede inducir a error de lectura.
    if n < 3:
        fig = go.Figure()
        fig.add_annotation(
            text=(f"Muestra insuficiente para comparar<br>"
                  f"({n} jugador/es en {posicion} con ≥{minutos_minimos}' jugados)"),
            showarrow=False, font=dict(color="#9CA3AF", size=13),
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=300,
                           xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    cats = [LABEL_METRICAS.get(m, m) for m in metricas]
    pcts = [datos["percentiles"].get(m, 0) for m in metricas]
    valores = [datos["valores_p90"].get(m, 0) for m in metricas]
    colores = [COLOR_CATEGORIA.get(CATEGORIA_METRICA.get(m, "posesion"), "#9CA3AF")
               for m in metricas]

    fig = go.Figure(go.Barpolar(
        r=pcts, theta=cats,
        marker_color=colores, marker_line_color="#111827", marker_line_width=1,
        opacity=0.9,
        customdata=valores,
        hovertemplate="%{theta}<br>Percentil: %{r}<br>Valor /90: %{customdata}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(
            text=f"vs. {n} jugador(es) de {posicion.lower()} en el plantel · ≥{minutos_minimos}' jugados",
            font=dict(size=11, color="#6B7280"), x=0.5,
        ),
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False,
                             gridcolor="#374151"),
            angularaxis=dict(gridcolor="#374151", color="#9CA3AF"),
            bgcolor="#111827",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF", size=12, family="Inter"),
        margin=dict(l=30, r=30, t=40, b=30),
        height=320,
        showlegend=False,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════
# Ejemplo de integración en 1_Plantel_ficha.py
# ══════════════════════════════════════════════════════════════════════════
"""
1) Cachear la tabla per-90 de todo el plantel UNA vez, junto a la carga
   global de datos (donde ya tenés `eventos = cargar_eventos()`, etc.):

    @st.cache_data(ttl=0)
    def _stats_per90_cache(eventos, jugadores):
        return stats_per90_plantel(eventos, jugadores, calcular_minutos)

    stats_p90 = _stats_per90_cache(eventos, jugadores)

2) En la sección "Radar de rendimiento" de la ficha, reemplazar:

    fig_r = radar_jugador(nombre, posicion, eventos, color)

   por:

    fig_r = radar_percentil_jugador(nombre, posicion, stats_p90,
                                     minutos_minimos=90)

3) El umbral `minutos_minimos=90` (equivalente a 1 partido completo) es
   ajustable — con un plantel amateur chico, quizás convenga bajarlo a 45-60
   para no perder demasiados jugadores de la muestra de comparación. Es un
   trade-off entre tamaño de muestra y calidad del dato: charlarlo con el
   cuerpo técnico antes de fijarlo.
"""
