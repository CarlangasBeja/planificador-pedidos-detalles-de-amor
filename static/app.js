// Tema claro/oscuro y dibujo de los gráficos de Plotly con los colores del tema.
(function () {
  "use strict";
  const raiz = document.documentElement;
  const botones = document.querySelectorAll("#tema");

  function rotular() {
    const oscuro = raiz.dataset.theme === "oscuro";
    botones.forEach((b) => {
      const destino = b.querySelector(".texto") || b;
      destino.textContent = oscuro ? "Modo claro" : "Modo oscuro";
    });
  }

  // Menú lateral: en computadora se oculta o muestra; en teléfono se despliega encima
  const movil = () => window.matchMedia("(max-width: 900px)").matches;
  const btnMenu = document.getElementById("btn-menu");
  if (btnMenu) {
    btnMenu.addEventListener("click", () => {
      if (movil()) { raiz.classList.toggle("menu-abierto"); return; }
      raiz.classList.toggle("menu-cerrado");
      try { localStorage.setItem("dda_menu", raiz.classList.contains("menu-cerrado") ? "cerrado" : "abierto"); } catch (e) {}
      setTimeout(() => { const g = document.getElementById("grafico"); if (g && window.Plotly && g.data) window.Plotly.Plots.resize(g); }, 260);
    });
    document.querySelectorAll("[data-cerrar-menu]").forEach((v) => v.addEventListener("click", () => raiz.classList.remove("menu-abierto")));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") raiz.classList.remove("menu-abierto"); });
  }

  // Reemplaza "var(--x)" por el valor real del tema actual
  function resolverColores(valor, estilos) {
    if (typeof valor === "string" && valor.startsWith("var(--")) {
      return estilos.getPropertyValue(valor.slice(4, -1)).trim() || valor;
    }
    if (Array.isArray(valor)) return valor.map((v) => resolverColores(v, estilos));
    if (valor && typeof valor === "object") {
      const copia = {};
      Object.keys(valor).forEach((k) => { copia[k] = resolverColores(valor[k], estilos); });
      return copia;
    }
    return valor;
  }

  function dibujar() {
    const fuente = document.getElementById("figura");
    const destino = document.getElementById("grafico");
    if (!fuente || !destino || !window.Plotly) return;
    const fig = resolverColores(JSON.parse(fuente.textContent), getComputedStyle(raiz));
    window.Plotly.react(destino, fig.data, fig.layout, { responsive: true, displaylogo: false,
      modeBarButtonsToRemove: ["lasso2d", "select2d"] });
  }

  botones.forEach((b) => b.addEventListener("click", () => {
    raiz.dataset.theme = raiz.dataset.theme === "oscuro" ? "claro" : "oscuro";
    try { localStorage.setItem("dda_tema", raiz.dataset.theme); } catch (e) { /* sin almacenamiento */ }
    rotular();
    dibujar();
  }));

  // Avisos rotativos de la barra superior
  const avisos = ["Campaña navideña 2026 · Peluche de Snoopy navideño",
    "Calcule la fecha segura de entrega antes de aceptar un pedido",
    "Hecho a mano en Ambato – Ecuador · Un pequeño regalo para el corazón"];
  const anuncio = document.getElementById("anuncio");
  let actual = 0, temporizador;
  function mostrarAviso(paso) {
    if (!anuncio) return;
    actual = (actual + paso + avisos.length) % avisos.length;
    anuncio.style.opacity = 0;
    setTimeout(() => { anuncio.textContent = avisos[actual]; anuncio.style.opacity = 1; }, 180);
  }
  function reiniciar() { clearInterval(temporizador); temporizador = setInterval(() => mostrarAviso(1), 6000); }
  document.querySelectorAll("[data-anuncio]").forEach((b) => b.addEventListener("click", () => {
    mostrarAviso(Number(b.dataset.anuncio)); reiniciar();
  }));
  reiniciar();

  // Mostrar u ocultar la contraseña
  document.querySelectorAll("[data-ver-clave]").forEach((b) => b.addEventListener("click", () => {
    const campo = document.getElementById(b.dataset.verClave);
    if (campo) campo.type = campo.type === "password" ? "text" : "password";
  }));

  // Recalcular automáticamente al cambiar un dato
  document.querySelectorAll("form[data-auto]").forEach((f) => {
    const jornada = Number(f.dataset.jornada || 8);
    f.querySelectorAll('input[type="radio"][name="unidad"]').forEach((r) => r.addEventListener("change", () => {
      const v = f.querySelector('input[name="valor"]');
      if (v && v.value) {
        const n = Number(v.value);
        v.value = r.value === "horas" ? +(n * jornada).toFixed(2) : +(n / jornada).toFixed(2);
      }
      f.submit();
    }));
    f.querySelectorAll('input[type="number"], input[type="date"], select').forEach((c) =>
      c.addEventListener("change", () => { if (c.value) f.submit(); }));
  });

  // Confirmación antes de eliminar un pedido
  document.querySelectorAll('button[value="eliminar"]').forEach((b) => b.addEventListener("click", (e) => {
    if (!window.confirm("¿Eliminar este pedido?")) e.preventDefault();
  }));

  rotular();
  if (document.readyState === "complete") dibujar();
  else window.addEventListener("load", dibujar);
})();
