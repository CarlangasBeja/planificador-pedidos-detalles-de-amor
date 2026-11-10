"""Gráficos de Plotly armados como diccionarios.

Los colores se escriben como variables CSS (var(--rojo), etc.) y el navegador
los reemplaza según el tema claro u oscuro antes de dibujar.
"""
from statistics import NormalDist

ROJO, GRIS, TINTA, SUAVE = "var(--rojo)", "var(--gris)", "var(--tinta)", "var(--suave)"
FONDO, REJILLA = "var(--tarjeta)", "var(--rejilla)"


def _layout(**extra):
    base = {
        "paper_bgcolor": FONDO, "plot_bgcolor": FONDO, "font": {"color": TINTA, "size": 12},
        "margin": {"l": 16, "r": 16, "t": 30, "b": 16}, "showlegend": False,
    }
    base.update(extra)
    return base


def red(res):
    """Red de actividades en los nodos (AON), ordenada por niveles de precedencia."""
    nivel = {}
    for f in res.filas:
        preds = [p.strip() for p in f["pred"].split(",") if p.strip() and p.strip() != "—"]
        nivel[f["id"]] = max((nivel[p] + 1 for p in preds), default=0)
    columnas = {}
    for k, n in nivel.items():
        columnas.setdefault(n, []).append(k)
    pos = {k: (n, (len(ks) - 1) / 2 - i) for n, ks in columnas.items() for i, k in enumerate(ks)}
    critica = {f["id"]: f["critica"] for f in res.filas}

    flechas = []
    for f in res.filas:
        for p in [p.strip() for p in f["pred"].split(",") if p.strip() and p.strip() != "—"]:
            ambos = critica[p] and f["critica"]
            flechas.append({
                "x": pos[f["id"]][0], "y": pos[f["id"]][1], "ax": pos[p][0], "ay": pos[p][1],
                "xref": "x", "yref": "y", "axref": "x", "ayref": "y", "showarrow": True, "arrowhead": 3,
                "arrowsize": 1.2, "arrowwidth": 2.6 if ambos else 1.4, "standoff": 22, "startstandoff": 22,
                "arrowcolor": ROJO if ambos else GRIS,
            })
    nodos = {
        "type": "scatter", "mode": "markers+text",
        "x": [pos[f["id"]][0] for f in res.filas], "y": [pos[f["id"]][1] for f in res.filas],
        "text": [f"<b>{f['id']}</b>" for f in res.filas], "textfont": {"size": 15, "color": TINTA},
        "marker": {"size": 44, "color": ["var(--rojo-fondo)" if f["critica"] else "var(--gris-fondo)" for f in res.filas],
                   "line": {"width": 2, "color": [ROJO if f["critica"] else GRIS for f in res.filas]}},
        "customdata": [[f["nombre"], round(f["te"], 2), round(f["holgura"], 2)] for f in res.filas],
        "hovertemplate": "<b>%{customdata[0]}</b><br>te = %{customdata[1]} h<br>Holgura = %{customdata[2]} h<extra></extra>",
    }
    return {"data": [nodos], "layout": _layout(height=380, annotations=flechas,
                                               xaxis={"visible": False}, yaxis={"visible": False})}


def gantt(res):
    filas = list(reversed(res.filas))
    etiquetas = [f"{f['id']} · {f['nombre']}" for f in filas]
    barras = {
        "type": "bar", "orientation": "h", "y": etiquetas, "x": [round(f["te"], 2) for f in filas],
        "base": [round(f["ES"], 2) for f in filas], "name": "Duración esperada",
        "marker": {"color": [ROJO if f["critica"] else GRIS for f in filas]},
        "hovertemplate": "Inicio %{base} h · duración %{x} h<extra></extra>",
    }
    holgura = {
        "type": "bar", "orientation": "h", "y": etiquetas, "x": [round(f["holgura"], 2) for f in filas],
        "base": [round(f["EF"], 2) for f in filas], "name": "Holgura",
        "marker": {"color": "var(--gris-fondo)", "line": {"color": GRIS, "width": 1},
                   "pattern": {"shape": "/", "fgcolor": GRIS}},
        "hovertemplate": "Holgura %{x} h<extra></extra>",
    }
    fin = {"type": "line", "x0": res.duracion, "x1": res.duracion, "y0": 0, "y1": 1, "yref": "paper",
           "line": {"color": TINTA, "dash": "dash", "width": 1.2}}
    return {"data": [barras, holgura], "layout": _layout(
        height=470, barmode="overlay", showlegend=True, legend={"orientation": "h", "y": -0.16},
        xaxis={"title": "Horas desde el inicio del pedido", "gridcolor": REJILLA, "zeroline": False},
        yaxis={"automargin": True}, shapes=[fin],
        annotations=[{"x": res.duracion, "y": 1.03, "yref": "paper", "showarrow": False,
                      "text": f"Fin esperado {res.duracion:.2f} h", "font": {"color": TINTA}}])}


def _texto_p(p):
    if p < 0.0005:
        return "≈ 0 %"
    if p > 0.9995:
        return "≈ 100 %"
    return f"{p:.1%}"


def _curva(media, sd, marcado, recomendado, confianza, unidad, titulo_x):
    """Curva de probabilidad acumulada con la zona recomendable y el plazo evaluado."""
    sd = max(sd, 1e-9)
    nd = NormalDist(media, sd)
    x_min = max(0.0, min(marcado - 0.08 * media, media - 4 * sd))
    x_max = max(marcado + 0.05 * media, media + 4 * sd, recomendado + 0.06 * media)
    xs = [x_min + (x_max - x_min) * i / 240 for i in range(241)]
    p = nd.cdf(marcado)
    linea = {"type": "scatter", "mode": "lines", "x": [round(x, 3) for x in xs], "y": [round(nd.cdf(x), 5) for x in xs],
             "line": {"color": ROJO, "width": 3, "shape": "spline"}, "fill": "tozeroy", "fillcolor": "var(--rojo-fondo)",
             "hovertemplate": "%{x:.1f} " + unidad + " → %{y:.1%}<extra></extra>"}
    punto = {"type": "scatter", "mode": "markers", "x": [marcado], "y": [round(p, 5)],
             "marker": {"size": 14, "color": ROJO, "line": {"color": "#FFFFFF", "width": 3}},
             "hovertemplate": "Plazo evaluado: %{x} " + unidad + " → %{y:.1%}<extra></extra>"}
    formas = [
        {"type": "rect", "x0": recomendado, "x1": x_max, "y0": 0, "y1": 1, "yref": "paper",
         "fillcolor": "var(--ok-fondo)", "opacity": 0.9, "line": {"width": 0}, "layer": "below"},
        {"type": "line", "x0": x_min, "x1": x_max, "y0": confianza, "y1": confianza,
         "line": {"color": SUAVE, "dash": "dot", "width": 1.4}},
        {"type": "line", "x0": marcado, "x1": marcado, "y0": 0, "y1": p, "line": {"color": ROJO, "dash": "dash", "width": 1.6}},
    ]
    derecha = marcado < (x_min + x_max) / 2
    notas = [
        {"x": x_max, "y": 0.04, "yref": "y", "xanchor": "right", "showarrow": False,
         "text": "Zona recomendable ", "font": {"color": "var(--ok-texto)", "size": 12}},
        {"x": x_min, "y": confianza, "xanchor": "left", "yanchor": "bottom", "showarrow": False,
         "text": f" Meta {confianza:.0%}", "font": {"color": SUAVE, "size": 11}},
        {"x": marcado, "y": p, "ax": 40 if derecha else -40, "ay": 38 if p > 0.75 else -34, "showarrow": True, "arrowcolor": TINTA,
         "arrowhead": 0, "arrowwidth": 1, "bgcolor": FONDO, "bordercolor": ROJO, "borderwidth": 1.2, "borderpad": 5,
         "text": f"<b>{marcado:g} {unidad}: {_texto_p(p)}</b>", "font": {"color": TINTA, "size": 12}},
    ]
    eje = {"gridcolor": REJILLA, "zeroline": False, "automargin": True, "linecolor": "var(--borde)", "showline": True}
    return {"data": [linea, punto], "layout": _layout(
        height=360, shapes=formas, annotations=notas, hovermode="closest",
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        xaxis={**eje, "title": {"text": titulo_x, "standoff": 10}, "range": [x_min, x_max]},
        yaxis={**eje, "title": {"text": "Probabilidad de cumplir", "standoff": 10}, "tickformat": ".0%",
               "range": [-0.03, 1.05], "dtick": 0.2})}


def curva(res, plazo, confianza):
    recomendado = res.duracion + NormalDist().inv_cdf(confianza) * max(res.desviacion, 1e-9)
    return _curva(res.duracion, res.desviacion, round(plazo, 2), recomendado, confianza, "h", "Plazo de entrega (horas)")


def curva_jornadas(res, cfg, disponibles, jornadas_rec):
    j = cfg["jornada"]
    return _curva(res.duracion / j, res.desviacion / j, disponibles, jornadas_rec, cfg["confianza"],
                  "jornadas", "Jornadas de trabajo hasta la entrega")
