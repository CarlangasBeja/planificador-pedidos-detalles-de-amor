"""Planificador de pedidos · Detalles de Amor
Aplicación web (Streamlit) para planificar pedidos con PERT-CPM.
Ejecutar con:  streamlit run app.py
"""
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from statistics import NormalDist

from pert_core import ACTIVIDADES_BASE, CASOS, caso, resolver, validar

from marca import TEMAS, css, logo

# ---------- tema claro / oscuro ----------
MODO = "oscuro" if st.session_state.get("modo_oscuro", False) else "claro"
C = TEMAS[MODO]
if st._config.get_option("theme.backgroundColor") != C["streamlit"]["backgroundColor"]:
    for opcion, valor in C["streamlit"].items():
        st._config.set_option(f"theme.{opcion}", valor)
    st.rerun()

CRITICA, NO_CRITICA, TINTA, SUAVE = C["rojo"], C["nocrit"], C["tinta"], C["suave"]

st.set_page_config(page_title="Planificador de pedidos · Detalles de Amor", page_icon="❤️",
                   layout="wide", initial_sidebar_state="auto")
st.markdown(css(C), unsafe_allow_html=True)


def kpis(items):
    html = "".join(f'<div class="kpi"><div class="etq">{e}</div><div class="val">{v}</div>'
                   f'<div class="sub">{s}</div></div>' for e, v, s in items)
    st.markdown(f'<div class="kpis">{html}</div>', unsafe_allow_html=True)


def fmt(x, d=2):
    return f"{x:,.{d}f}".replace(",", " ")


# ---------- barra lateral ----------
with st.sidebar:
    st.markdown(f'<div class="logo-lateral">{logo(C, 170, con_texto=True)}'
                '<div class="sub">Peluches hechos a mano</div></div>', unsafe_allow_html=True)
    st.markdown("### Configuración")
    clave = st.selectbox("Escenario", list(CASOS), format_func=CASOS.get)
    jornada = st.number_input("Horas por jornada", 4.0, 12.0, 8.0, 0.5)
    confianza = st.select_slider("Nivel de confianza", [0.80, 0.85, 0.90, 0.95, 0.99], value=0.95,
                                 format_func=lambda x: f"{x:.0%}")
    st.caption("Tiempos en horas para un pedido de dos docenas. Datos levantados con la propietaria.")

if "datos" not in st.session_state or st.session_state.get("clave") != clave:
    st.session_state.datos = caso(clave)
    st.session_state.clave = clave
if "pedidos" not in st.session_state:
    st.session_state.pedidos = []

cab1, cab2 = st.columns([5, 1.3], vertical_alignment="center")
with cab1:
    st.markdown(f'<div class="marca">{logo(C, 64)}<div><div class="nombre">Detalles de Amor</div>'
                '<h1>Planificador de pedidos</h1>'
                '<p>Peluche de Snoopy navideño · Método PERT-CPM</p></div></div>', unsafe_allow_html=True)
with cab2:
    st.toggle("Modo oscuro", value=MODO == "oscuro", key="tgl_oscuro",
              help="Cambia la apariencia entre claro y oscuro",
              on_change=lambda: st.session_state.update(modo_oscuro=st.session_state.tgl_oscuro))
st.markdown('<div class="franja"></div>', unsafe_allow_html=True)

errores = validar(st.session_state.datos)
if errores:
    st.error("Revise los datos de entrada:\n\n" + "\n".join(f"- {e}" for e in errores))
    st.stop()

res = resolver(st.session_state.datos)
plazo_conf = res.plazo_para(confianza)
tabla = pd.DataFrame(res.filas)

tabs = st.tabs(["Resumen", "Datos", "Red", "Cronograma", "Probabilidad", "Pedidos", "Casos de prueba"])

# ---------- Resumen ----------
with tabs[0]:
    kpis([
        ("Duración esperada", f"{fmt(res.duracion)} h", f"{fmt(res.duracion / jornada, 1)} jornadas"),
        ("Desviación estándar", f"{fmt(res.desviacion)} h", f"Varianza {fmt(res.varianza, 3)}"),
        (f"Plazo al {confianza:.0%}", f"{fmt(plazo_conf)} h", f"{math.ceil(plazo_conf / jornada - 1e-9)} jornadas a ofrecer"),
        ("Actividades críticas", str(int(tabla.critica.sum())), f"de {len(tabla)} actividades"),
    ])
    st.markdown("**Ruta crítica**")
    for r in res.rutas_criticas:
        st.markdown(f'<div class="ruta">{" → ".join(r)}</div>', unsafe_allow_html=True)
    if len(res.rutas_criticas) > 1:
        st.info("Existen varias rutas críticas. Para la probabilidad se usa la de mayor varianza.")
    st.markdown("**Tiempos y holguras por actividad**")
    vista = tabla[["id", "nombre", "te", "var", "ES", "EF", "LS", "LF", "holgura", "critica"]].rename(columns={
        "id": "Act.", "nombre": "Actividad", "te": "te (h)", "var": "σ²", "holgura": "Holgura (h)", "critica": "Crítica"})
    vista["Crítica"] = vista["Crítica"].map({True: "Sí", False: "No"})
    st.dataframe(
        vista.style.format({c: "{:.2f}" for c in ["te (h)", "ES", "EF", "LS", "LF", "Holgura (h)"]} | {"σ²": "{:.3f}"})
        .apply(lambda f: [f"background-color: {C['rojo_fondo']}; color: {C['rojo_texto']}" if f["Crítica"] == "Sí" else "" for _ in f], axis=1),
        hide_index=True, use_container_width=True)

# ---------- Datos ----------
with tabs[1]:
    st.markdown("Edite los tiempos o las precedencias y la planificación se recalcula al instante.")
    editable = pd.DataFrame([{**a, "pred": ", ".join(a["pred"])} for a in st.session_state.datos])
    editado = st.data_editor(
        editable, hide_index=True, use_container_width=True, num_rows="dynamic", key=f"editor_{clave}",
        column_config={
            "id": st.column_config.TextColumn("Act.", width="small"),
            "nombre": st.column_config.TextColumn("Actividad", width="large"),
            "pred": st.column_config.TextColumn("Predecesoras", help="Códigos separados por coma"),
            "a": st.column_config.NumberColumn("Optimista (h)", min_value=0.0, step=0.5),
            "m": st.column_config.NumberColumn("Más probable (h)", min_value=0.0, step=0.5),
            "b": st.column_config.NumberColumn("Pesimista (h)", min_value=0.0, step=0.5),
        })
    c1, c2 = st.columns([1, 1])
    if c1.button("Aplicar cambios", type="primary", use_container_width=True):
        nuevos = []
        for _, f in editado.dropna(subset=["id"]).iterrows():
            nuevos.append({"id": str(f["id"]).strip().upper(), "nombre": str(f["nombre"] or ""),
                           "pred": [p.strip().upper() for p in str(f["pred"] or "").replace("—", "").split(",") if p.strip()],
                           "a": float(f["a"] or 0), "m": float(f["m"] or 0), "b": float(f["b"] or 0)})
        st.session_state.datos = nuevos
        st.rerun()
    if c2.button("Restaurar datos del escenario", use_container_width=True):
        st.session_state.datos = caso(clave)
        st.rerun()

# ---------- Red ----------
with tabs[2]:
    nivel = {}
    for f in res.filas:  # filas en orden topológico
        preds = [p.strip() for p in f["pred"].split(",") if p.strip() and p.strip() != "—"]
        nivel[f["id"]] = max((nivel[p] + 1 for p in preds), default=0)
    columnas = {}
    for k, n in nivel.items():
        columnas.setdefault(n, []).append(k)
    pos = {}
    for n, ks in columnas.items():
        for i, k in enumerate(ks):
            pos[k] = (n, (len(ks) - 1) / 2 - i)
    fig = go.Figure()
    for f in res.filas:
        for p in [p.strip() for p in f["pred"].split(",") if p.strip() and p.strip() != "—"]:
            ambos = f["critica"] and tabla.set_index("id").loc[p, "critica"]
            fig.add_annotation(x=pos[f["id"]][0], y=pos[f["id"]][1], ax=pos[p][0], ay=pos[p][1],
                               xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=3,
                               arrowsize=1.2, arrowwidth=2.4 if ambos else 1.3, standoff=22, startstandoff=22,
                               arrowcolor=CRITICA if ambos else C["flecha"])
    fig.add_trace(go.Scatter(
        x=[pos[f["id"]][0] for f in res.filas], y=[pos[f["id"]][1] for f in res.filas], mode="markers+text",
        marker=dict(size=44, color=[C["rojo_fondo"] if f["critica"] else C["nocrit_fondo"] for f in res.filas],
                    line=dict(width=2, color=[CRITICA if f["critica"] else NO_CRITICA for f in res.filas])),
        text=[f"<b>{f['id']}</b>" for f in res.filas], textfont=dict(size=15, color=TINTA),
        customdata=[[f["nombre"], f["te"], f["holgura"]] for f in res.filas],
        hovertemplate="<b>%{text}</b> %{customdata[0]}<br>te = %{customdata[1]:.2f} h<br>Holgura = %{customdata[2]:.2f} h<extra></extra>"))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
                      xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor=None),
                      plot_bgcolor=C["fondo"], paper_bgcolor=C["fondo"], font=dict(color=TINTA))
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
    st.caption("Red de actividades en los nodos (AON). Rojo: ruta crítica. Pase el cursor sobre una actividad para ver sus tiempos.")

# ---------- Cronograma ----------
with tabs[3]:
    orden = list(reversed(res.filas))
    g = go.Figure()
    g.add_trace(go.Bar(y=[f"{f['id']} · {f['nombre']}" for f in orden], x=[f["te"] for f in orden],
                       base=[f["ES"] for f in orden], orientation="h", name="Duración esperada",
                       marker_color=[CRITICA if f["critica"] else NO_CRITICA for f in orden],
                       hovertemplate="Inicio %{base:.2f} h · duración %{x:.2f} h<extra></extra>"))
    g.add_trace(go.Bar(y=[f"{f['id']} · {f['nombre']}" for f in orden], x=[f["holgura"] for f in orden],
                       base=[f["EF"] for f in orden], orientation="h", name="Holgura",
                       marker=dict(color=C["nocrit_fondo"], line=dict(color=NO_CRITICA, width=1),
                                   pattern_shape="/", pattern_fgcolor=NO_CRITICA),
                       hovertemplate="Holgura %{x:.2f} h<extra></extra>"))
    g.add_vline(x=res.duracion, line_dash="dash", line_color=TINTA,
                annotation_text=f"Fin esperado {fmt(res.duracion)} h", annotation_position="top left")
    g.update_layout(barmode="overlay", height=460, margin=dict(l=10, r=10, t=30, b=10),
                    xaxis_title="Horas desde el inicio del pedido", legend=dict(orientation="h", y=-0.15),
                    plot_bgcolor=C["fondo"], paper_bgcolor=C["fondo"], font=dict(color=TINTA))
    g.update_xaxes(gridcolor=C["rejilla"])
    st.plotly_chart(g, use_container_width=True, config={"displaylogo": False})
    st.caption("Rojo: actividad crítica. Gris: actividad con holgura. La zona rayada es el margen disponible.")

# ---------- Probabilidad ----------
with tabs[4]:
    c1, c2 = st.columns([1, 2])
    with c1:
        unidad = st.radio("Expresar el plazo en", ["Jornadas", "Horas"], horizontal=True)
        if unidad == "Jornadas":
            dias = st.number_input("Plazo solicitado (jornadas)", 0.5, 30.0, 2.0, 0.5)
            plazo = dias * jornada
        else:
            plazo = st.number_input("Plazo solicitado (horas)", 1.0, 240.0, 16.0, 1.0)
        z, p = res.probabilidad(plazo)
        kpis([("Probabilidad de cumplir", f"{p:.1%}", f"Z = {fmt(z)} · plazo {fmt(plazo)} h")])
        if p >= confianza:
            st.markdown('<div class="alerta-ok">El plazo puede aceptarse con el nivel de confianza elegido.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alerta-mal">Plazo riesgoso. Se recomienda ofrecer al menos '
                        f'{fmt(plazo_conf)} h ({math.ceil(plazo_conf / jornada - 1e-9)} jornadas).</div>',
                        unsafe_allow_html=True)
    with c2:
        xs = [res.duracion + res.desviacion * (i / 20 - 4) for i in range(161)]
        ys = [NormalDist(res.duracion, res.desviacion).cdf(x) for x in xs]
        cur = go.Figure(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=CRITICA, width=2.5),
                                   hovertemplate="%{x:.1f} h → %{y:.1%}<extra></extra>"))
        cur.add_vline(x=plazo, line_color=TINTA, line_dash="dash",
                      annotation_text=f"Plazo {fmt(plazo)} h", annotation_position="bottom right")
        cur.add_hline(y=confianza, line_color=SUAVE, line_dash="dot",
                      annotation_text=f"{confianza:.0%}", annotation_position="top left")
        cur.update_layout(height=340, margin=dict(l=10, r=10, t=20, b=10), yaxis_tickformat=".0%",
                          xaxis_title="Plazo (horas)", yaxis_title="Probabilidad de cumplir",
                          plot_bgcolor=C["fondo"], paper_bgcolor=C["fondo"], font=dict(color=TINTA))
        cur.update_xaxes(gridcolor=C["rejilla"]); cur.update_yaxes(gridcolor=C["rejilla"])
        st.plotly_chart(cur, use_container_width=True, config={"displaylogo": False})

# ---------- Pedidos ----------
with tabs[5]:
    st.markdown("Registre un pedido para saber, antes de aceptarlo, si el plazo es alcanzable y si la tela alcanza.")
    with st.form("pedido", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        cliente = c1.text_input("Cliente")
        docenas = c2.number_input("Cantidad (docenas)", 0.5, 2.0, 2.0, 0.5,
                                  help="Los tiempos están calibrados para pedidos de hasta dos docenas.")
        dias = c3.number_input("Plazo solicitado (jornadas)", 0.5, 30.0, 2.0, 0.5)
        c4, c5 = st.columns(2)
        tela = c4.number_input("Tela disponible (m)", 0.0, 500.0, 6.0, 0.5)
        consumo = c5.number_input("Consumo de tela por docena (m)", 0.1, 50.0, 3.5, 0.1)
        enviado = st.form_submit_button("Evaluar pedido", type="primary", use_container_width=True)
    if enviado:
        if not cliente.strip():
            st.warning("Ingrese el nombre del cliente.")
        else:
            _, p = res.probabilidad(dias * jornada)
            falta = max(docenas * consumo - tela, 0)
            st.session_state.pedidos.append({
                "Cliente": cliente.strip(), "Docenas": docenas, "Plazo pedido (jornadas)": dias,
                "Prob. de cumplir": f"{p:.1%}", "Plazo recomendado (jornadas)": math.ceil(plazo_conf / jornada - 1e-9),
                "Tela": "Suficiente" if falta == 0 else f"Faltan {fmt(falta, 1)} m",
                "Decisión": "Aceptar" if p >= confianza and falta == 0 else "Negociar plazo / comprar tela"})
    if st.session_state.pedidos:
        st.dataframe(pd.DataFrame(st.session_state.pedidos), hide_index=True, use_container_width=True)
    else:
        st.caption("Aún no hay pedidos registrados en esta sesión.")

# ---------- Casos de prueba ----------
with tabs[6]:
    plazo_ref = st.slider("Plazo de referencia para comparar (horas)", 8, 72, 48, 1)
    filas = []
    for k, nombre in CASOS.items():
        r = resolver(caso(k))
        z, p = r.probabilidad(plazo_ref)
        filas.append({"Escenario": nombre, "T (h)": r.duracion, "σ (h)": r.desviacion,
                      f"P(≤ {plazo_ref} h)": p, f"Plazo al {confianza:.0%} (h)": r.plazo_para(confianza),
                      "Rutas críticas": len(r.rutas_criticas)})
    st.dataframe(pd.DataFrame(filas).style.format({"T (h)": "{:.2f}", "σ (h)": "{:.2f}",
                 f"P(≤ {plazo_ref} h)": "{:.1%}", f"Plazo al {confianza:.0%} (h)": "{:.2f}"}),
                 hide_index=True, use_container_width=True)
    st.caption("Los resultados coinciden con la solución manual del informe; las diferencias en el último "
               "decimal se deben al redondeo de Z en las tablas de la distribución normal.")

st.markdown("<div class='pie'>Detalles de Amor · Planificador de pedidos con PERT-CPM · Proyecto de "
            "Investigación Operativa, Universidad Técnica de Ambato</div>", unsafe_allow_html=True)
