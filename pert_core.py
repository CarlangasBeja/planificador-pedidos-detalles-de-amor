"""Motor de cálculo PERT-CPM para la planificación de pedidos de Detalles de Amor.

Calcula tiempos esperados, varianzas, tiempos de inicio y terminación,
holguras, ruta crítica y probabilidades de cumplimiento de un plazo.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from graphlib import CycleError, TopologicalSorter
from statistics import NormalDist

EPS = 1e-9

# Datos levantados en la entrevista: horas para un pedido de dos docenas.
ACTIVIDADES_BASE = [
    {"id": "A", "nombre": "Diseño y moldes en cartón", "pred": [], "a": 2, "m": 4, "b": 5},
    {"id": "B", "nombre": "Compra de materiales", "pred": ["A"], "a": 2, "m": 3, "b": 4},
    {"id": "C", "nombre": "Rayado de moldes sobre la tela", "pred": ["B"], "a": 2, "m": 3, "b": 4},
    {"id": "D", "nombre": "Corte de piezas", "pred": ["C"], "a": 3, "m": 5, "b": 5},
    {"id": "E", "nombre": "Bordado y sublimado de accesorios", "pred": ["D"], "a": 6, "m": 13, "b": 14},
    {"id": "F", "nombre": "Costura del cuerpo", "pred": ["D"], "a": 5, "m": 11, "b": 14},
    {"id": "G", "nombre": "Relleno", "pred": ["F"], "a": 5, "m": 10, "b": 16},
    {"id": "H", "nombre": "Cierre y limpieza de costuras", "pred": ["G"], "a": 2, "m": 3, "b": 5},
    {"id": "I", "nombre": "Acabados: ojos, detalles y accesorios", "pred": ["E", "H"], "a": 3, "m": 4, "b": 5},
    {"id": "J", "nombre": "Control de calidad", "pred": ["I"], "a": 1, "m": 2, "b": 4},
    {"id": "K", "nombre": "Publicidad (fotos y redes)", "pred": ["J"], "a": 1, "m": 1, "b": 2},
    {"id": "L", "nombre": "Enfundado y entrega", "pred": ["J"], "a": 4, "m": 5, "b": 10},
]


@dataclass
class ResultadoPERT:
    filas: list[dict]          # una fila por actividad con todos sus tiempos
    duracion: float            # T: duración esperada del proyecto
    varianza: float            # varianza de la ruta crítica
    desviacion: float          # desviación estándar de la ruta crítica
    ruta_critica: list[str]    # ruta crítica usada para la probabilidad
    rutas_criticas: list[list[str]]

    def probabilidad(self, plazo: float) -> tuple[float, float]:
        """Devuelve (Z, P) de terminar en un plazo dado (horas)."""
        if self.desviacion < EPS:
            return (math.inf if plazo >= self.duracion else -math.inf), float(plazo >= self.duracion)
        z = (plazo - self.duracion) / self.desviacion
        return z, NormalDist().cdf(z)

    def plazo_para(self, confianza: float) -> float:
        """Plazo (horas) que se cumple con la probabilidad indicada (0-1)."""
        return self.duracion + NormalDist().inv_cdf(confianza) * self.desviacion


def validar(actividades: list[dict]) -> list[str]:
    """Revisa los datos de entrada y devuelve una lista de errores."""
    errores = []
    ids = [a["id"] for a in actividades]
    if len(ids) != len(set(ids)):
        errores.append("Hay actividades con el mismo código.")
    for act in actividades:
        a, m, b = act["a"], act["m"], act["b"]
        if min(a, m, b) < 0:
            errores.append(f"{act['id']}: los tiempos no pueden ser negativos.")
        if not a <= m <= b:
            errores.append(f"{act['id']}: debe cumplirse optimista ≤ más probable ≤ pesimista.")
        for p in act["pred"]:
            if p not in ids:
                errores.append(f"{act['id']}: la predecesora {p} no existe.")
    if not errores:
        try:
            list(TopologicalSorter({a["id"]: a["pred"] for a in actividades}).static_order())
        except CycleError:
            errores.append("Las precedencias forman un ciclo.")
    return errores


def resolver(actividades: list[dict]) -> ResultadoPERT:
    """Aplica PERT-CPM: pasos hacia adelante y hacia atrás, holguras y ruta crítica."""
    acts = {a["id"]: a for a in actividades}
    orden = list(TopologicalSorter({k: v["pred"] for k, v in acts.items()}).static_order())
    sucesoras = {k: [s for s in acts if k in acts[s]["pred"]] for k in acts}

    te = {k: (v["a"] + 4 * v["m"] + v["b"]) / 6 for k, v in acts.items()}
    var = {k: ((v["b"] - v["a"]) / 6) ** 2 for k, v in acts.items()}

    es, ef = {}, {}
    for k in orden:  # paso hacia adelante
        es[k] = max((ef[p] for p in acts[k]["pred"]), default=0.0)
        ef[k] = es[k] + te[k]
    duracion = max(ef.values())

    ls, lf = {}, {}
    for k in reversed(orden):  # paso hacia atrás
        lf[k] = min((ls[s] for s in sucesoras[k]), default=duracion)
        ls[k] = lf[k] - te[k]
        if abs(ls[k]) < 1e-9:
            ls[k] = 0.0

    filas = []
    for k in orden:
        holgura = ls[k] - es[k]
        libre = min((es[s] for s in sucesoras[k]), default=duracion) - ef[k]
        filas.append({
            "id": k, "nombre": acts[k]["nombre"], "pred": ", ".join(acts[k]["pred"]) or "—",
            "a": acts[k]["a"], "m": acts[k]["m"], "b": acts[k]["b"],
            "te": te[k], "var": var[k], "ES": es[k], "EF": ef[k], "LS": ls[k], "LF": lf[k],
            "holgura": max(holgura, 0.0), "holgura_libre": max(libre, 0.0),
            "critica": abs(holgura) < 1e-6,
        })

    # Todas las rutas formadas solo por actividades críticas
    criticas = {f["id"] for f in filas if f["critica"]}
    inicios = [k for k in criticas if not acts[k]["pred"]]
    rutas: list[list[str]] = []

    def explorar(nodo, camino):
        sig = [s for s in sucesoras[nodo] if s in criticas and abs(es[s] - ef[nodo]) < 1e-6]
        if not sig:
            if abs(ef[nodo] - duracion) < 1e-6:
                rutas.append(camino)
            return
        for s in sig:
            explorar(s, camino + [s])

    for k in sorted(inicios):
        explorar(k, [k])

    # Si hay varias rutas críticas se usa la de mayor varianza (criterio conservador)
    ruta = max(rutas, key=lambda r: sum(var[x] for x in r))
    varianza = sum(var[x] for x in ruta)
    return ResultadoPERT(filas, duracion, varianza, math.sqrt(varianza), ruta, rutas)


def caso(nombre: str) -> list[dict]:
    """Datos de los casos de prueba del informe."""
    datos = [dict(a, pred=list(a["pred"])) for a in ACTIVIDADES_BASE]
    if nombre == "recurrente":  # moldes ya hechos y sin publicidad
        datos = [a for a in datos if a["id"] not in ("A", "K")]
        for a in datos:
            a["pred"] = [p for p in a["pred"] if p not in ("A", "K")]
    elif nombre == "tela":  # la compra puede tardar dos jornadas si falta tela
        for a in datos:
            if a["id"] == "B":
                a["b"] = 16
    elif nombre == "limite":  # E se retrasa exactamente su holgura
        holgura_e = next(f["holgura"] for f in resolver(ACTIVIDADES_BASE).filas if f["id"] == "E")
        for a in datos:
            if a["id"] == "E":
                a["a"] += holgura_e
                a["m"] += holgura_e
                a["b"] += holgura_e
    return datos


CASOS = {
    "base": "Caso 1 · Base (lanzamiento de la campaña)",
    "recurrente": "Caso 2 · Pedido recurrente (sin A ni K)",
    "tela": "Caso 3 · Falta de tela (B pesimista = 16 h)",
    "limite": "Caso 4 · Límite (E se retrasa su holgura)",
}


if __name__ == "__main__":
    for clave, titulo in CASOS.items():
        r = resolver(caso(clave))
        z48, p48 = r.probabilidad(48)
        print(f"{titulo}\n  T = {r.duracion:.2f} h | var = {r.varianza:.4f} | sd = {r.desviacion:.4f}"
              f" | plazo 95% = {r.plazo_para(0.95):.2f} h | P(48 h) = {p48:.4f}")
        print("  rutas críticas:", [" → ".join(x) for x in r.rutas_criticas])
        print("  holguras:", {f['id']: round(f['holgura'], 2) for f in r.filas if f['holgura'] > 1e-6})
