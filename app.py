"""Planificador de pedidos · Detalles de Amor
Aplicación web en Flask (Python) con login de administrador y usuario.

Local:   pip install -r requirements.txt  y luego  python app.py  → http://localhost:5000
Vercel:  se publica con el archivo vercel.json incluido.
"""
import math
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, flash, make_response, redirect, render_template, request, session, url_for
from itsdangerous import BadSignature, URLSafeSerializer
from werkzeug.security import check_password_hash, generate_password_hash

import graficos
from pert_core import CASOS, caso, resolver, validar

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "detalles-de-amor-grupo5-cambiar-en-produccion")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  PERMANENT_SESSION_LIFETIME=timedelta(days=30))
HORAS_SESION = 8  # el login vence a las 8 horas; los pedidos se conservan

# ---------- Usuarios definidos en el código (sin base de datos) ----------
USUARIOS = {
    "admin": {"clave": os.environ.get("ADMIN_PASSWORD", "Admin2026"), "rol": "admin",
              "nombre": "Alexandra Bucheli"},
    "usuario": {"clave": os.environ.get("USER_PASSWORD", "Usuario2026"), "rol": "usuario",
                "nombre": "Atención al cliente"},
}

ZONA = timezone(timedelta(hours=-5))  # Ecuador continental
CONFIG_INICIAL = {"escenario": "base", "jornada": 8.0, "confianza": 0.95, "consumo": 3.5}
NIVELES = [0.80, 0.85, 0.90, 0.95, 0.99]
MAX_PEDIDOS = 15


# ---------- Utilidades ----------
def sesion_vigente():
    inicio = session.get("inicio")
    if session.get("rol") and inicio and datetime.now(ZONA).timestamp() - inicio < HORAS_SESION * 3600:
        return True
    for k in ("usuario", "rol", "nombre", "inicio"):
        session.pop(k, None)
    return False


# ---------- Cuentas: cambios guardados solo en este navegador (cookie firmada) ----------
COOKIE_CUENTAS = "dda_cuentas"


def _firmador():
    return URLSafeSerializer(app.secret_key, salt="cuentas-locales")


def leer_cuentas():
    try:
        return _firmador().loads(request.cookies.get(COOKIE_CUENTAS, "")) or {}
    except BadSignature:
        return {}


def cuenta(rol):
    """Usuario y nombre vigentes del rol, con los cambios locales aplicados."""
    base = next(k for k, v in USUARIOS.items() if v["rol"] == rol)
    propio = leer_cuentas().get(rol, {})
    return {"usuario": propio.get("u", base), "nombre": propio.get("n", USUARIOS[base]["nombre"]),
            "clave_hash": propio.get("h"), "clave": USUARIOS[base]["clave"], "rol": rol}


def verificar(usuario, clave):
    for rol in ("admin", "usuario"):
        c = cuenta(rol)
        if usuario == c["usuario"]:
            valida = check_password_hash(c["clave_hash"], clave) if c["clave_hash"] else clave == c["clave"]
            return c if valida else None
    return None


def requiere(rol):
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            sesion_vigente()
            if rol != "cualquiera" and session.get("rol") != rol or not session.get("rol"):
                if session.get("rol"):
                    return redirect(url_for("inicio"))
                flash("Inicie sesión para continuar.", "aviso")
                return redirect(url_for("login"))
            return vista(*args, **kwargs)
        return envoltura
    return decorador


def config():
    return {**CONFIG_INICIAL, **session.get("config", {})}


def datos_actuales():
    cfg = config()
    if session.get("datos") and session.get("datos_esc") == cfg["escenario"]:
        return session["datos"]
    return caso(cfg["escenario"])


def calcular():
    datos = datos_actuales()
    errores = validar(datos)
    return datos, errores, (None if errores else resolver(datos))


def hoy():
    return datetime.now(ZONA).date()


def es_laborable(d):
    return d.weekday() != 6  # se trabaja de lunes a sábado


def jornadas_hasta(fecha):
    """Jornadas laborables desde hoy (incluido) hasta la fecha de entrega (excluida)."""
    d, n = hoy(), 0
    while d < fecha:
        n += es_laborable(d)
        d += timedelta(days=1)
    return n


def fecha_tras(jornadas):
    """Fecha de entrega luego de trabajar el número de jornadas indicado desde hoy."""
    d, n = hoy(), 0
    while n < jornadas:
        n += es_laborable(d)
        d += timedelta(days=1)
    while not es_laborable(d):
        d += timedelta(days=1)
    return d


def num(texto, defecto=None):
    try:
        return float(str(texto).replace(",", "."))
    except (TypeError, ValueError):
        return defecto


def evaluar(res, cfg, form):
    """Valida el formulario de pedido y devuelve (datos, errores)."""
    errores = []
    cliente = (form.get("cliente") or "").strip()[:40]
    docenas = num(form.get("docenas"), 0)
    tela = num(form.get("tela"))
    try:
        fecha = datetime.strptime(form.get("fecha", ""), "%Y-%m-%d").date()
    except ValueError:
        fecha = None
    if not cliente:
        errores.append("Ingrese el nombre del cliente.")
    if not 0.5 <= docenas <= 2:
        errores.append("La cantidad debe estar entre media y dos docenas.")
    if fecha is None or fecha <= hoy():
        errores.append("La fecha de entrega debe ser posterior a hoy.")
    if tela is None or tela < 0:
        errores.append("Ingrese los metros de tela disponibles.")
    if errores:
        return None, errores

    disponibles = jornadas_hasta(fecha)
    _, prob = res.probabilidad(disponibles * cfg["jornada"])
    plazo_rec = res.plazo_para(cfg["confianza"])
    jornadas_rec = math.ceil(plazo_rec / cfg["jornada"] - 1e-9)
    falta = max(docenas * cfg["consumo"] - tela, 0.0)
    acepta = prob >= cfg["confianza"] and falta == 0
    return {
        "cliente": cliente, "docenas": docenas, "fecha": fecha, "tela": tela, "disponibles": disponibles,
        "prob": prob, "jornadas_rec": jornadas_rec, "fecha_rec": fecha_tras(jornadas_rec),
        "falta": falta, "acepta": acepta,
    }, []


def guardar_pedido(ev, fecha):
    pedidos = session.get("pedidos", [])
    pedidos.insert(0, {"c": ev["cliente"], "d": ev["docenas"], "f": fecha.isoformat(),
                       "p": round(ev["prob"], 4) if fecha == ev["fecha"] else None,
                       "t": round(ev["falta"], 1), "e": "Pendiente", "r": hoy().isoformat()})
    session["pedidos"] = pedidos[:MAX_PEDIDOS]


MENUS = {
    "admin": [("resumen", "Resumen", "resumen"), ("datos", "Datos", "datos"), ("red", "Red", "red"),
              ("cronograma", "Cronograma", "cronograma"), ("probabilidad", "Probabilidad", "curva"),
              ("pedidos", "Pedidos", "pedidos"), ("casos", "Casos de prueba", "casos"), ("cuenta", "Cuentas y accesos", "cuenta")],
    "usuario": [("nuevo", "Nuevo pedido", "nuevo"), ("analizar", "Analizar plazo", "curva"),
                ("pedidos", "Mis pedidos", "lista"), ("guia", "Guía de producción", "guia")],
}


def url_menu(rol, clave):
    if clave == "cuenta":
        return url_for("mi_cuenta")
    if rol == "admin":
        return url_for("admin", seccion=clave)
    return url_for({"nuevo": "usuario_nuevo", "analizar": "usuario_analizar", "pedidos": "usuario_pedidos",
                    "guia": "usuario_guia"}[clave])


@app.context_processor
def contexto():
    return {"CASOS": CASOS, "NIVELES": NIVELES, "sesion": session, "hoy": hoy(), "MENUS": MENUS, "url_menu": url_menu,
            "manana": (hoy() + timedelta(days=1)).isoformat()}


@app.template_filter("f2")
def f2(x, d=2):
    return f"{x:,.{d}f}".replace(",", " ")


@app.template_filter("pct")
def pct(p):
    if p < 0.0005:
        return "≈ 0 %"
    if p > 0.9995:
        return "≈ 100 %"
    return f"{p * 100:.1f} %"


@app.template_filter("fecha")
def fecha_larga(d):
    if isinstance(d, str):
        d = datetime.strptime(d, "%Y-%m-%d").date()
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
             "octubre", "noviembre", "diciembre"]
    return f"{dias[d.weekday()]} {d.day} de {meses[d.month - 1]}"


# ---------- Sesión ----------
@app.route("/")
def inicio():
    sesion_vigente()
    if session.get("rol") == "admin":
        return redirect(url_for("admin", seccion="resumen"))
    if session.get("rol") == "usuario":
        return redirect(url_for("usuario_nuevo"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nombre = (request.form.get("usuario") or "").strip().lower()
        c = verificar(nombre, request.form.get("clave", ""))
        if c:
            session.permanent = True
            session.update(usuario=c["usuario"], rol=c["rol"], nombre=c["nombre"],
                           inicio=datetime.now(ZONA).timestamp())
            return redirect(url_for("inicio"))
        flash("Usuario o contraseña incorrectos.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    for k in ("usuario", "rol", "nombre", "inicio"):
        session.pop(k, None)  # los pedidos se conservan en este navegador
    flash("Sesión cerrada correctamente.", "ok")
    return redirect(url_for("login"))


# ---------- Administrador ----------
SECCIONES_ADMIN = ["resumen", "datos", "red", "cronograma", "probabilidad", "pedidos", "casos"]


@app.route("/admin/<seccion>", methods=["GET", "POST"])
@requiere("admin")
def admin(seccion):
    if seccion not in SECCIONES_ADMIN:
        return redirect(url_for("admin", seccion="resumen"))
    cfg = config()
    datos, errores, res = calcular()
    ctx = {"seccion": seccion, "cfg": cfg, "datos": datos, "errores": errores, "res": res}

    if seccion == "datos" and request.method == "POST":
        return guardar_datos()
    if res is None:
        return render_template("admin.html", **{**ctx, "seccion": "datos" if seccion != "datos" else seccion})

    ctx["plazo_conf"] = res.plazo_para(cfg["confianza"])
    ctx["jornadas_conf"] = math.ceil(ctx["plazo_conf"] / cfg["jornada"] - 1e-9)

    if seccion == "red":
        ctx["figura"] = graficos.red(res)
    elif seccion == "cronograma":
        ctx["figura"] = graficos.gantt(res)
    elif seccion == "probabilidad":
        unidad = request.args.get("unidad", "jornadas")
        if unidad not in ("jornadas", "horas"):
            unidad = "jornadas"
        valor = num(request.args.get("valor"), 6.0 if unidad == "jornadas" else 48.0)
        valor = min(max(valor, 0.5), 400.0)
        plazo = valor * cfg["jornada"] if unidad == "jornadas" else valor
        z, p = res.probabilidad(plazo)
        media = res.duracion / cfg["jornada"]
        opciones = list(range(max(1, math.floor(media) - 1), ctx["jornadas_conf"] + 2))
        ctx.update(unidad=unidad, valor=valor, plazo=plazo, z=z, p=p, media=media, opciones=opciones,
                   figura=graficos.curva(res, plazo, cfg["confianza"]))
    elif seccion == "pedidos":
        if request.method == "POST":
            return accion_pedido("admin")
        ctx["pedidos"] = session.get("pedidos", [])
    elif seccion == "casos":
        ref = min(max(num(request.args.get("ref"), 48), 8), 120)
        filas = []
        for clave, titulo in CASOS.items():
            r = resolver(caso(clave))
            filas.append({"titulo": titulo, "T": r.duracion, "sd": r.desviacion,
                          "p": r.probabilidad(ref)[1], "plazo": r.plazo_para(cfg["confianza"]),
                          "rutas": len(r.rutas_criticas)})
        ctx.update(ref=ref, casos=filas)
    return render_template("admin.html", **ctx)


def guardar_datos():
    accion = request.form.get("accion", "aplicar")
    cfg = config()
    if accion == "restaurar":
        session.pop("datos", None)
        flash("Se restauraron los datos del escenario.", "ok")
        return redirect(url_for("admin", seccion="datos"))
    filas = []
    total = int(num(request.form.get("filas"), 0) or 0)
    for i in range(min(total, 40)):
        if request.form.get(f"eliminar_{i}"):
            continue
        codigo = (request.form.get(f"id_{i}") or "").strip().upper()[:4]
        if not codigo:
            continue
        preds = [p.strip().upper() for p in (request.form.get(f"pred_{i}") or "").replace("—", "").split(",") if p.strip()]
        filas.append({"id": codigo, "nombre": (request.form.get(f"nombre_{i}") or "").strip()[:60],
                      "pred": preds, "a": num(request.form.get(f"a_{i}"), -1),
                      "m": num(request.form.get(f"m_{i}"), -1), "b": num(request.form.get(f"b_{i}"), -1)})
    if accion == "agregar":
        filas.append({"id": "", "nombre": "", "pred": [], "a": 0.0, "m": 0.0, "b": 0.0})
        return render_template("admin.html", seccion="datos", cfg=cfg, datos=filas, errores=[], res=None,
                               editando=True)
    errores = validar(filas)
    if errores:
        return render_template("admin.html", seccion="datos", cfg=cfg, datos=filas, errores=errores, res=None,
                               editando=True)
    session["datos"], session["datos_esc"] = filas, cfg["escenario"]
    flash("Cambios aplicados. La planificación se recalculó.", "ok")
    return redirect(url_for("admin", seccion="datos"))


@app.route("/config", methods=["POST"])
@requiere("admin")
def cambiar_config():
    cfg = config()
    escenario = request.form.get("escenario", cfg["escenario"])
    if escenario in CASOS and escenario != cfg["escenario"]:
        cfg["escenario"] = escenario
        session.pop("datos", None)
    cfg["jornada"] = min(max(num(request.form.get("jornada"), cfg["jornada"]), 4), 12)
    conf = num(request.form.get("confianza"), cfg["confianza"])
    cfg["confianza"] = conf if conf in NIVELES else cfg["confianza"]
    cfg["consumo"] = min(max(num(request.form.get("consumo"), cfg["consumo"]), 0.1), 50)
    session["config"] = cfg
    destino = request.form.get("volver", "resumen")
    qs = request.form.get("qs", "")
    qs = qs if all(ch.isalnum() or ch in "=&._-%" for ch in qs) else ""
    url = url_for("admin", seccion=destino if destino in SECCIONES_ADMIN else "resumen")
    flash("Configuración aplicada.", "ok")
    return redirect(url + ("?" + qs if qs else ""))


# ---------- Pedidos (compartido) ----------
def accion_pedido(rol):
    cfg = config()
    _, errores_modelo, res = calcular()
    vista = "admin" if rol == "admin" else "usuario"
    destino = url_for("admin", seccion="pedidos") if rol == "admin" else url_for("usuario_nuevo")
    accion = request.form.get("accion", "evaluar")

    if accion in ("entregado", "eliminar"):
        i = int(num(request.form.get("indice"), -1))
        pedidos = session.get("pedidos", [])
        if 0 <= i < len(pedidos):
            if accion == "eliminar":
                pedidos.pop(i)
                flash("Pedido eliminado.", "ok")
            else:
                pedidos[i]["e"] = "Entregado"
                flash("Pedido marcado como entregado.", "ok")
            session["pedidos"] = pedidos
        return redirect(url_for("admin", seccion="pedidos") if rol == "admin" else url_for("usuario_pedidos"))

    if res is None:
        flash("Los datos del modelo tienen errores; el administrador debe corregirlos.", "error")
        return redirect(destino)
    ev, errores = evaluar(res, cfg, request.form)
    if errores:
        for e in errores:
            flash(e, "error")
        ctx = {"cfg": cfg, "form": request.form, "res": res}
        if vista == "admin":
            return render_template("admin.html", seccion="pedidos", datos=None, errores=[],
                                   pedidos=session.get("pedidos", []), **ctx)
        return render_template("usuario.html", seccion="nuevo", **ctx)

    if accion == "guardar_solicitada":
        guardar_pedido(ev, ev["fecha"])
        flash(f"Pedido de {ev['cliente']} guardado para el {fecha_larga(ev['fecha'])}.", "ok")
        return redirect(url_for("admin", seccion="pedidos") if rol == "admin" else url_for("usuario_pedidos"))
    if accion == "guardar_recomendada":
        guardar_pedido(ev, ev["fecha_rec"])
        flash(f"Pedido de {ev['cliente']} guardado para el {fecha_larga(ev['fecha_rec'])}.", "ok")
        return redirect(url_for("admin", seccion="pedidos") if rol == "admin" else url_for("usuario_pedidos"))

    ctx = {"cfg": cfg, "form": request.form, "ev": ev, "res": res,
           "figura": graficos.curva_jornadas(res, cfg, ev["disponibles"], ev["jornadas_rec"])}
    if vista == "admin":
        return render_template("admin.html", seccion="pedidos", datos=None, errores=[],
                               pedidos=session.get("pedidos", []), **ctx)
    return render_template("usuario.html", seccion="nuevo", **ctx)


# ---------- Usuario ----------
@app.route("/usuario/nuevo", methods=["GET", "POST"])
@requiere("usuario")
def usuario_nuevo():
    if request.method == "POST":
        return accion_pedido("usuario")
    _, _, res = calcular()
    return render_template("usuario.html", seccion="nuevo", cfg=config(), form={}, res=res)


@app.route("/usuario/pedidos", methods=["GET", "POST"])
@requiere("usuario")
def usuario_pedidos():
    if request.method == "POST":
        return accion_pedido("usuario")
    return render_template("usuario.html", seccion="pedidos", cfg=config(), pedidos=session.get("pedidos", []))


@app.route("/usuario/guia")
@requiere("usuario")
def usuario_guia():
    _, _, res = calcular()
    return render_template("usuario.html", seccion="guia", cfg=config(), res=res)


def veredicto(p, confianza):
    if p >= confianza:
        return "Recomendable", "ok"
    if p >= 0.5:
        return "Riesgoso", "riesgo"
    return "No recomendable", "mal"


@app.template_global()
def veredicto_global(p, confianza):
    return veredicto(p, confianza)


@app.route("/usuario/analizar")
@requiere("usuario")
def usuario_analizar():
    cfg = config()
    _, _, res = calcular()
    if res is None:
        flash("El administrador debe revisar los datos del modelo.", "error")
        return render_template("usuario.html", seccion="analizar", cfg=cfg, res=None)
    plazo_rec = res.plazo_para(cfg["confianza"])
    jornadas_rec = math.ceil(plazo_rec / cfg["jornada"] - 1e-9)
    try:
        fecha = datetime.strptime(request.args.get("fecha", ""), "%Y-%m-%d").date()
    except ValueError:
        fecha = hoy() + timedelta(days=7)
    if fecha <= hoy():
        flash("Elija una fecha posterior a hoy.", "error")
        fecha = hoy() + timedelta(days=1)
    disponibles = jornadas_hasta(fecha)
    p = res.probabilidad(disponibles * cfg["jornada"])[1]
    tabla, n = [], max(1, jornadas_rec - 4)
    for j in range(n, n + 9):
        pj = res.probabilidad(j * cfg["jornada"])[1]
        tabla.append({"fecha": fecha_tras(j), "jornadas": j, "p": pj, "veredicto": veredicto(pj, cfg["confianza"])})
    return render_template("usuario.html", seccion="analizar", cfg=cfg, res=res, fecha=fecha,
                           disponibles=disponibles, p=p, veredicto=veredicto(p, cfg["confianza"]),
                           jornadas_rec=jornadas_rec, fecha_rec=fecha_tras(jornadas_rec), tabla=tabla,
                           figura=graficos.curva_jornadas(res, cfg, disponibles, jornadas_rec))


def guardar_cookie_cuentas(cuentas, destino):
    resp = make_response(redirect(destino))
    resp.set_cookie(COOKIE_CUENTAS, _firmador().dumps(cuentas), max_age=365 * 86400, httponly=True, samesite="Lax")
    return resp


@app.route("/cuenta", methods=["GET", "POST"])
@requiere("admin")
def mi_cuenta():
    """Solo la administradora cambia nombres, usuarios y contraseñas de ambas cuentas."""
    if request.method == "POST":
        objetivo = request.form.get("cuenta")
        if objetivo not in ("admin", "usuario"):
            return redirect(url_for("mi_cuenta"))
        cuentas = leer_cuentas()
        admin_actual = cuenta("admin")
        clave_admin = request.form.get("clave_admin", "")
        valida = (check_password_hash(admin_actual["clave_hash"], clave_admin) if admin_actual["clave_hash"]
                  else clave_admin == admin_actual["clave"])
        if request.form.get("accion") == "restablecer":
            if not valida:
                flash("Para restablecer, escriba la contraseña actual de la administradora.", "error")
                return render_template("cuenta.html", seccion="cuenta", cuentas_vista=vista_cuentas(),
                                       form=request.form, abierta=objetivo)
            cuentas.pop(objetivo, None)
            if objetivo == "admin":
                base = next(k for k, v in USUARIOS.items() if v["rol"] == "admin")
                session.update(usuario=base, nombre=USUARIOS[base]["nombre"])
            flash("Se restablecieron los datos originales de la cuenta.", "ok")
            return guardar_cookie_cuentas(cuentas, url_for("mi_cuenta"))

        nombre = (request.form.get("nombre") or "").strip()[:40]
        usuario = (request.form.get("usuario") or "").strip().lower()[:20]
        nueva, repetida = request.form.get("clave_nueva", ""), request.form.get("clave_repetida", "")
        errores = []
        if not valida:
            errores.append("La contraseña actual de la administradora no es correcta.")
        if len(nombre) < 3:
            errores.append("El nombre debe tener al menos 3 caracteres.")
        if len(usuario) < 3 or not all(ch.isalnum() or ch in "._-" for ch in usuario):
            errores.append("El usuario debe tener al menos 3 caracteres: letras, números, punto, guion o guion bajo.")
        if usuario == cuenta("usuario" if objetivo == "admin" else "admin")["usuario"]:
            errores.append("Ese nombre de usuario ya lo usa la otra cuenta.")
        if nueva and len(nueva) < 6:
            errores.append("La nueva contraseña debe tener al menos 6 caracteres.")
        if nueva != repetida:
            errores.append("La nueva contraseña y su confirmación no coinciden.")
        if errores:
            for e in errores:
                flash(e, "error")
            return render_template("cuenta.html", seccion="cuenta", cuentas_vista=vista_cuentas(),
                                   form=request.form, abierta=objetivo)
        propio = cuentas.get(objetivo, {})
        propio.update(u=usuario, n=nombre)
        if nueva:
            propio["h"] = generate_password_hash(nueva)
        cuentas[objetivo] = propio
        if objetivo == "admin":
            session.update(usuario=usuario, nombre=nombre)
        etiqueta = "de la administradora" if objetivo == "admin" else "del usuario de atención al cliente"
        flash(f"Se actualizaron los datos {etiqueta}.", "ok")
        return guardar_cookie_cuentas(cuentas, url_for("mi_cuenta"))
    return render_template("cuenta.html", seccion="cuenta", cuentas_vista=vista_cuentas(), form={}, abierta=None)


def vista_cuentas():
    return [{**cuenta("admin"), "titulo": "Administradora"},
            {**cuenta("usuario"), "titulo": "Atención al cliente"}]


@app.errorhandler(404)
def no_encontrado(_):
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", 5000)))
