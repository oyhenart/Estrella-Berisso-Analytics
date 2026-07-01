"""
════════════════════════════════════════════════════════════════════════════
 REPORTE DE JUGADOR — para pegar dentro de 8_Player_review.py
════════════════════════════════════════════════════════════════════════════
Estilo idéntico al reporte de equipo (7_Reporte_imagen.py): cancha dibujada
a mano, paleta #FAF7F2 / #8A2525, firma "IAO Footbal Analytics".

Instrucciones de integración (3 pasos):

  1) IMPORTS — agregar arriba de todo en 8_Player_review.py, junto a los
     imports existentes:

        import io
        import math
        import numpy as np
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

  2) FUNCIONES — pegar el bloque "# ── FUNCIONES DE REPORTE" completo
     (más abajo) en cualquier lugar del archivo, antes de "# ── Carga
     global" (así ya están definidas cuando arranca la app).

  3) UI — pegar el bloque "# ── BLOQUE UI: REPORTE" al final del archivo
     (después de la sección de videos), fuera de los `with col_stats:` /
     `with col_videos:`, para que el reporte ocupe todo el ancho.
════════════════════════════════════════════════════════════════════════════
"""

import io
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# ════════════════════════════════════════════════════════════════════════
# FUNCIONES DE REPORTE
# ════════════════════════════════════════════════════════════════════════

# ── Constantes de cancha (idénticas a 7_Reporte_imagen.py) ────────────────
W, H = 100, 100
AG_X = 12.7; AG_Y = 44.8; AC_X = 4.2; AC_Y = 20.4; ARCO = 8.1; CR = 7.0
PITCH_BG = "#F2EEE7"


def draw_pitch(ax):
    ax.set_facecolor(PITCH_BG)
    ax.set_xlim(-2, 102); ax.set_ylim(102, -2)
    ax.set_aspect("equal"); ax.axis("off")
    kw = dict(color="#7A6A5E", linewidth=1.5)
    ax.plot([0, W, W, 0, 0], [0, 0, H, H, 0], **kw)
    ax.plot([W / 2, W / 2], [0, H], **kw)
    ax.add_patch(plt.Circle((W / 2, H / 2), CR, fill=False, **kw))
    ax.plot(W / 2, H / 2, "o", color="#7A6A5E", markersize=3)
    for x0, x1 in [(0, AG_X), (W - AG_X, W)]:
        ax.plot([x0, x1, x1, x0, x0],
                [(H - AG_Y) / 2, (H - AG_Y) / 2, (H + AG_Y) / 2, (H + AG_Y) / 2, (H - AG_Y) / 2], **kw)
    for x0, x1 in [(0, AC_X), (W - AC_X, W)]:
        ax.plot([x0, x1, x1, x0, x0],
                [(H - AC_Y) / 2, (H - AC_Y) / 2, (H + AC_Y) / 2, (H + AC_Y) / 2, (H - AC_Y) / 2], **kw)
    ax.plot([0, 0], [(H - ARCO) / 2, (H + ARCO) / 2], color="#7A6A5E", linewidth=3.5)
    ax.plot([W, W], [(H - ARCO) / 2, (H + ARCO) / 2], color="#7A6A5E", linewidth=3.5)


def pase_completo(df_p, idx, x_dest, y_dest, tolerancia=5, ventana=4):
    """Heurística ya usada en 7_Reporte_imagen.py: un pase se considera
    completo si, dentro de las próximas `ventana` filas del PARTIDO
    (cualquier jugador), aparece un evento cerca del destino."""
    for j in range(idx + 1, min(idx + ventana + 1, len(df_p))):
        sig = df_p.iloc[j]
        try:
            x_sig = float(sig["X"]); y_sig = float(sig["Y"])
        except Exception:
            continue
        if math.sqrt((x_dest - x_sig) ** 2 + (y_dest - y_sig) ** 2) <= tolerancia:
            return True
    return False


def clasificar_pases_partido(df_partido: pd.DataFrame) -> pd.DataFrame:
    """Agrega pase_ok (bool) a TODOS los pases del partido, no solo los del
    jugador — la heurística necesita el evento siguiente en el partido,
    sea de quien sea, para saber si el pase llegó a destino."""
    df_partido = df_partido.reset_index(drop=True).copy()
    df_partido["pase_ok"] = False
    for idx, row in df_partido.iterrows():
        if str(row["Event"]).lower() != "pase":
            continue
        if pd.isna(row["X2"]) or pd.isna(row["Y2"]):
            continue
        ok = pase_completo(df_partido, idx, float(row["X2"]), float(row["Y2"]))
        df_partido.at[idx, "pase_ok"] = ok
    return df_partido


def stats_jugador_reporte(jugador: str, df_clasificado: pd.DataFrame) -> dict:
    jp = df_clasificado[df_clasificado["Player"].str.lower() == jugador.lower()]
    pases = jp[jp["Event"] == "pase"]
    return {
        "pases": len(pases),
        "pases_ok": int(pases["pase_ok"].sum()) if "pase_ok" in pases.columns else 0,
        "recuperaciones": len(jp[jp["Event"] == "recuperacion"]),
        "perdidas": len(jp[jp["Event"] == "perdida"]),
        "remates": len(jp[jp["Event"].isin(["remate", "gol"])]),
        "goles": len(jp[jp["Event"] == "gol"]),
        "asistencias": len(jp[jp["Event"] == "asistencia"]),
        "faltas_cometidas": len(jp[jp["Event"] == "falta cometida"]),
        "despejes": len(jp[jp["Event"] == "despeje"]),
    }


def grafico_pases_jugador(jp_pases: pd.DataFrame, ax):
    draw_pitch(ax)
    completos = incompletos = 0
    for _, row in jp_pases.iterrows():
        x1, y1, x2, y2 = row.get("X"), row.get("Y"), row.get("X2"), row.get("Y2")
        if any(pd.isna(v) for v in [x1, y1, x2, y2]):
            continue
        ok = bool(row.get("pase_ok", False))
        color = "#2E6F40" if ok else "#C93B3B"
        alpha = 0.8 if ok else 0.5
        if ok:
            completos += 1
        else:
            incompletos += 1
        ax.annotate("", xy=(float(y2), float(x2)), xytext=(float(y1), float(x1)),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.5, alpha=alpha))
        ax.plot(float(y1), float(x1), "o", color=color, markersize=4, alpha=alpha)
    ax.legend(handles=[
        mpatches.Patch(color="#2E6F40", label=f"Completo ({completos})"),
        mpatches.Patch(color="#C93B3B", label=f"Incompleto ({incompletos})"),
    ], loc="upper left", framealpha=0.9, facecolor="#FAF7F2",
       edgecolor="#7A6A5E", labelcolor="#3D2C24", fontsize=8)


def grafico_calor_jugador(jp: pd.DataFrame, ax):
    draw_pitch(ax)
    xs = pd.to_numeric(jp["X"], errors="coerce")
    ys = pd.to_numeric(jp["Y"], errors="coerce")
    validos = xs.notna() & ys.notna()
    if validos.sum() < 3:
        ax.text(50, 50, "Datos insuficientes", ha="center", va="center",
                color="#7A6A5E", fontsize=9)
        return
    nx, ny = 9, 13
    grid = np.zeros((ny, nx))
    for x, y in zip(xs[validos], ys[validos]):
        xi = min(int(y / 100 * nx), nx - 1)
        yi = min(int(x / 100 * ny), ny - 1)
        grid[yi, xi] += 1
    grid_masked = np.where(grid == 0, np.nan, grid)
    xc = np.linspace(0, 100, nx + 1); xc = (xc[:-1] + xc[1:]) / 2
    yc = np.linspace(0, 100, ny + 1); yc = (yc[:-1] + yc[1:]) / 2
    cmap = plt.cm.YlOrRd.copy(); cmap.set_bad(alpha=0)
    ax.pcolormesh(xc, yc, grid_masked, cmap=cmap, shading="nearest", zorder=2, alpha=0.85)


def grafico_remates_jugador(jp: pd.DataFrame, ax):
    draw_pitch(ax)
    remates = jp[jp["Event"].isin(["remate", "gol"])]
    goles = no_goles = 0
    for _, row in remates.iterrows():
        x, y = row.get("X"), row.get("Y")
        if pd.isna(x) or pd.isna(y):
            continue
        es_gol = row["Event"] == "gol"
        color = "#2E6F40" if es_gol else "#C93B3B"
        if es_gol:
            goles += 1
        else:
            no_goles += 1
        ax.scatter(float(y), float(x), color=color, marker="o" if es_gol else "x",
                   s=140 if es_gol else 70, zorder=5,
                   alpha=0.9 if es_gol else 0.6, edgecolors="#FAF7F2")
    ax.legend(handles=[
        mpatches.Patch(color="#2E6F40", label=f"Gol ({goles})"),
        mpatches.Patch(color="#C93B3B", label=f"No convirtió ({no_goles})"),
    ], loc="upper left", framealpha=0.9, facecolor="#FAF7F2",
       edgecolor="#7A6A5E", labelcolor="#3D2C24", fontsize=8)


def grafico_actividad_jugador(jp_partido: pd.DataFrame, ax):
    """Solo modo PARTIDO: eventos del jugador por minuto."""
    ax.set_facecolor(PITCH_BG)
    if jp_partido.empty:
        ax.text(0.5, 0.5, "Sin eventos", ha="center", va="center", transform=ax.transAxes,
                color="#7A6A5E")
        return
    act = jp_partido.groupby("Mins")["Event"].count()
    ax.bar(act.index.astype(float), act.values, color="#7A6A5E", width=0.8)
    ax.set_xlabel("Minuto", color="#3D2C24", fontsize=9, fontfamily="serif")
    ax.set_ylabel("Eventos", color="#3D2C24", fontsize=9, fontfamily="serif")
    ax.tick_params(colors="#3D2C24", labelsize=8)
    for sp in ax.spines.values():
        sp.set_visible(False)


def grafico_evolucion_temporada(jp_todas: pd.DataFrame, ax):
    """Solo modo TEMPORADA: goles+asistencias vs. pérdidas, por fecha."""
    ax.set_facecolor(PITCH_BG)
    fechas = sorted(jp_todas["fecha"].unique())
    if not fechas:
        ax.text(0.5, 0.5, "Sin partidos", ha="center", va="center", transform=ax.transAxes,
                color="#7A6A5E")
        return
    ga = [len(jp_todas[(jp_todas["fecha"] == f) & (jp_todas["Event"].isin(["gol", "asistencia"]))])
          for f in fechas]
    perd = [len(jp_todas[(jp_todas["fecha"] == f) & (jp_todas["Event"] == "perdida")])
            for f in fechas]
    x = np.arange(len(fechas))
    ax.bar(x - 0.18, ga, width=0.36, color="#2E6F40", label="Goles + Asist.")
    ax.bar(x + 0.18, perd, width=0.36, color="#C93B3B", label="Pérdidas")
    ax.set_xticks(x); ax.set_xticklabels([f"F{int(f)}" for f in fechas], fontsize=8, color="#3D2C24")
    ax.tick_params(colors="#3D2C24", labelsize=8)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.legend(facecolor="#FAF7F2", edgecolor="#7A6A5E", labelcolor="#3D2C24", fontsize=8)


def generar_imagen_jugador(jugador: str, row_jug, eventos: pd.DataFrame,
                            modo: str = "partido", num_fecha=None) -> io.BytesIO:
    """
    modo: "partido" | "temporada"
    Devuelve un BytesIO con el reporte en PNG, estilo IAO Footbal Analytics.
    """
    buf = io.BytesIO()
    fig = plt.figure(figsize=(12, 15), facecolor="#FAF7F2")

    j_all = eventos[eventos["Player"].str.lower() == jugador.lower()]

    if modo == "partido" and num_fecha is not None:
        df_partido = eventos[eventos["fecha"] == num_fecha]
        df_clas    = clasificar_pases_partido(df_partido)
        jp         = df_clas[df_clas["Player"].str.lower() == jugador.lower()]
        jp_pases   = jp[jp["Event"] == "pase"]
        stats      = stats_jugador_reporte(jugador, df_clas)
        subtitulo  = f"Fecha {int(num_fecha)}"
    else:
        clasificados = [clasificar_pases_partido(eventos[eventos["fecha"] == f])
                         for f in sorted(j_all["fecha"].unique())]
        df_clas   = pd.concat(clasificados, ignore_index=True) if clasificados else eventos.iloc[0:0].copy()
        jp        = df_clas[df_clas["Player"].str.lower() == jugador.lower()] if not df_clas.empty else df_clas
        jp_pases  = jp[jp["Event"] == "pase"] if not jp.empty else jp
        stats     = stats_jugador_reporte(jugador, df_clas) if not df_clas.empty else stats_jugador_reporte(jugador, eventos.iloc[0:0])
        n_partidos = j_all["fecha"].nunique()
        subtitulo  = f"Temporada · {n_partidos} partido{'s' if n_partidos != 1 else ''}"

    ratio = round(stats["pases"] / stats["perdidas"], 1) if stats["perdidas"] > 0 else "—"

    posicion = str(row_jug.get("posicion", "—"))
    camiseta = row_jug.get("camiseta", "—")

    # Encabezado
    hax = fig.add_axes([0.05, 0.94, 0.90, 0.05]); hax.axis("off")
    hax.text(0.5, 0.65, f"#{camiseta} {jugador}", color="#8A2525", fontsize=22,
             fontweight="bold", ha="center", va="center", fontfamily="serif")
    hax.text(0.5, 0.15, f"{posicion}  ·  {subtitulo}", color="#3D2C24", fontsize=11,
             fontweight="bold", ha="center", va="center", fontfamily="serif")
    fig.add_axes([0.05, 0.935, 0.90, 0.002], facecolor="#8A2525").axis("off")

    # Fila 1: Pases | KPIs | Calor
    fig.text(0.05, 0.90, "Mapa de Pases", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")
    fig.text(0.415, 0.90, "Estadísticas", color="#3D2C24", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")
    fig.text(0.62, 0.90, "Mapa de Calor", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")

    ax_pases = fig.add_axes([0.05, 0.70, 0.33, 0.19])
    ax_table = fig.add_axes([0.415, 0.70, 0.17, 0.19])
    ax_calor = fig.add_axes([0.62, 0.70, 0.33, 0.19])

    grafico_pases_jugador(jp_pases, ax_pases)
    grafico_calor_jugador(jp, ax_calor)

    ax_table.axis("off")
    ax_table.text(0.05, 0.92, "Métrica", color="#3D2C24", fontsize=10, fontweight="bold", ha="left", fontfamily="monospace")
    ax_table.text(0.95, 0.92, "Valor", color="#3D2C24", fontsize=10, fontweight="bold", ha="right", fontfamily="monospace")
    ax_table.plot([0.01, 0.99], [0.87, 0.87], color="#7A6A5E", linewidth=1.5)
    kpis = [
        ("Pases", str(stats["pases"]), False),
        ("Pases OK", str(stats["pases_ok"]), False),
        ("Pérdidas", str(stats["perdidas"]), False),
        ("Ratio P/P", str(ratio), False),
        ("Recuperac.", str(stats["recuperaciones"]), False),
        ("Remates", str(stats["remates"]), False),
        ("Goles", str(stats["goles"]), stats["goles"] > 0),
        ("Asistencias", str(stats["asistencias"]), stats["asistencias"] > 0),
        ("Faltas com.", str(stats["faltas_cometidas"]), False),
    ]
    y_val = 0.80
    for label, val, accent in kpis:
        ax_table.text(0.05, y_val, label, color="#3D2C24", fontsize=9, ha="left", fontfamily="monospace")
        ax_table.text(0.95, y_val, val, color="#A83232" if accent else "#3D2C24",
                      fontweight="bold", ha="right", fontfamily="monospace")
        ax_table.plot([0.01, 0.99], [y_val - 0.045, y_val - 0.045], color="#7A6A5E", linewidth=0.5, linestyle=":")
        y_val -= 0.088

    # Fila 2: Actividad (partido) / Evolución (temporada)
    if modo == "partido" and num_fecha is not None:
        fig.text(0.05, 0.485, "Actividad por Minuto", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")
        ax_act = fig.add_axes([0.05, 0.36, 0.90, 0.11])
        grafico_actividad_jugador(jp, ax_act)
    else:
        fig.text(0.05, 0.485, "Evolución por Fecha", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")
        ax_evo = fig.add_axes([0.05, 0.36, 0.90, 0.11])
        grafico_evolucion_temporada(jp, ax_evo)

    # Fila 3: Remates
    fig.text(0.05, 0.31, "Mapa de Remates", color="#8A2525", fontsize=12, fontweight="bold", ha="left", fontfamily="serif")
    ax_remates = fig.add_axes([0.30, 0.06, 0.40, 0.24])
    grafico_remates_jugador(jp, ax_remates)

    fig.add_axes([0.05, 0.045, 0.90, 0.002], facecolor="#7A6A5E").axis("off")

    # Firma (misma línea que 7_Reporte_imagen.py)
    fig.text(0.05, 0.020, "IAO Footbal Analytics", color="#8A2525", fontsize=12,
             ha="left", va="center", fontweight="bold", fontfamily="serif")
    fig.text(0.05, 0.005, "video-analisis-app.streamlit.app", color="#7A6A5E", fontsize=9,
             ha="left", va="center", fontfamily="serif")
    fig.text(0.95, 0.012, "Estrella de Berisso", color="#3D2C24", fontsize=10,
             ha="right", va="center", fontfamily="serif")

    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf


# ════════════════════════════════════════════════════════════════════════
# BLOQUE UI: REPORTE
# (pegar al final de 8_Player_review.py, después de la sección de videos,
#  fuera de los `with col_stats:` / `with col_videos:`)
# ════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.markdown("<div style='height:1px;background:#1F2937;margin-bottom:20px'></div>",
            unsafe_allow_html=True)
st.markdown("""'"""'"""'.format() if False else '' # placeholder, ver bloque real abajo sin f-strings anidados
