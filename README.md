# Planificador de pedidos · Detalles de Amor

Aplicación web para planificar los pedidos del peluche navideño con el método PERT-CPM.

## Cómo ejecutarla
1. Instale Python 3.10 o superior.
2. En esta carpeta, ejecute:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. Se abrirá en el navegador (http://localhost:8501). Funciona también en el celular si se abre desde la misma red.

## Qué incluye
- **Resumen:** duración esperada, desviación, plazo recomendado y ruta crítica.
- **Datos:** tabla editable de actividades, precedencias y tiempos (optimista, más probable, pesimista).
- **Red y Cronograma:** red de actividades y diagrama de Gantt interactivos.
- **Probabilidad:** probabilidad de cumplir el plazo que pide el cliente.
- **Pedidos:** evalúa un pedido antes de aceptarlo, incluida la tela disponible.
- **Casos de prueba:** compara los cuatro escenarios del informe.
- **Modo oscuro:** interruptor en la parte superior derecha.

## Archivos
- `app.py` — interfaz.
- `pert_core.py` — cálculos PERT-CPM (`python pert_core.py` imprime los casos de prueba).
- `marca.py` — colores, tema claro/oscuro y logotipo.
- `.streamlit/config.toml` — tema inicial.
- `capturas/` — vistas en modo claro, oscuro y celular.
# planificador-pedidos-detalles-de-amor
