# Planificador de pedidos · Detalles de Amor

Aplicación web en **Python (Flask)** para planificar los pedidos de la fábrica de peluches
Detalles de Amor con el método **PERT-CPM**. Proyecto de Investigación Operativa · Grupo 5.

## Usuarios
| Usuario | Contraseña | Acceso |
|---|---|---|
| `admin` (Alexandra Bucheli) | `Admin2026` | Todo: resumen, datos editables, red, cronograma, probabilidad, pedidos, casos de prueba y cuentas y accesos |
| `usuario` | `Usuario2026` | Interfaz sencilla: nuevo pedido, analizar plazo (curva de probabilidad), mis pedidos y guía de producción |

Los usuarios están definidos en `app.py` (sin base de datos). En Vercel se pueden cambiar las
contraseñas con las variables de entorno `ADMIN_PASSWORD` y `USER_PASSWORD`.

## Menú y cuenta
- El menú lateral se oculta o muestra con el botón ☰; en el teléfono se despliega sobre la pantalla.
- Solo la administradora, en **Cuentas y accesos**, puede cambiar el nombre, usuario y contraseña de las dos
  cuentas. Los cambios se guardan solo en ese navegador (cookie firmada, sin base de datos) y se pueden restablecer.
- El inicio de sesión vence a las 8 horas.

## Diseño
- Colores de la marca (rojo y blanco), tipografías Nunito y Fredoka incluidas en `static/fuentes/`.
- Logotipo oficial (oso con corazón) en `static/img/logo_completo.png` y `static/img/logo_oso.png`.
- Imágenes de la tienda para el inicio de sesión y las portadas: `static/img/banner_peluches.jpg` y `static/img/ramo_peluche.jpg`.
- Barra de avisos rotativos, botón de modo claro/oscuro y mostrar/ocultar contraseña.

## Ejecutar en la computadora
```bash
pip install -r requirements.txt
python app.py
```
Abrir http://localhost:5000

## Publicar en Vercel
1. Suba esta carpeta a un repositorio de GitHub.
2. En https://vercel.com elija **Add New → Project**, importe el repositorio y pulse **Deploy**.
   No hace falta cambiar ninguna opción: el archivo `vercel.json` ya indica cómo ejecutar la app.
3. Recomendado: en **Settings → Environment Variables** agregue `SECRET_KEY` con un texto largo
   cualquiera y vuelva a desplegar. Esa clave firma la sesión del login.

También puede usar la terminal: `npm i -g vercel` y luego `vercel --prod` dentro de la carpeta.

## Cómo se guardan los datos
No hay base de datos. La sesión, la configuración, los datos editados y los últimos 15 pedidos
se guardan en una cookie firmada del navegador. Por eso los pedidos se ven en el mismo navegador
donde se registraron, tanto desde la cuenta de administrador como desde la de usuario.

## Archivos
- `app.py` — rutas, login y lógica de pedidos.
- `pert_core.py` — cálculos PERT-CPM (`python pert_core.py` imprime los casos de prueba).
- `graficos.py` — red, diagrama de Gantt y curva de probabilidad.
- `templates/` — páginas HTML. `static/` — estilos, JavaScript y Plotly.
- `vercel.json` — configuración para Vercel.
