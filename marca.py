"""Identidad visual de Detalles de Amor: paletas claro/oscuro y logotipo."""

TEMAS = {
    "claro": {
        "streamlit": {"base": "light", "primaryColor": "#C8102E", "backgroundColor": "#FFFFFF",
                      "secondaryBackgroundColor": "#FFF3F5", "textColor": "#2B1B1E"},
        "fondo": "#FFFFFF", "fondo2": "#FFF3F5", "tarjeta": "#FFFFFF", "tinta": "#2B1B1E",
        "suave": "#7A6468", "borde": "#F1D3D8", "rojo": "#C8102E", "rojo_fondo": "#FDECEF",
        "rojo_texto": "#8A0B20", "nocrit": "#9AA0A6", "nocrit_fondo": "#F1F2F4",
        "rejilla": "#F3E7E9", "flecha": "#B9AFB1", "ok_fondo": "#EAF6EF", "ok_borde": "#B7E1C6",
        "ok_texto": "#145A32", "mal_fondo": "#FDECEF", "mal_borde": "#F3B9C3", "mal_texto": "#8A0B20",
        "osito": "#F6EDE3", "osito_borde": "#8C6B58",
    },
    "oscuro": {
        "streamlit": {"base": "dark", "primaryColor": "#FF4D5E", "backgroundColor": "#141012",
                      "secondaryBackgroundColor": "#1F181A", "textColor": "#F5ECEE"},
        "fondo": "#141012", "fondo2": "#1F181A", "tarjeta": "#1C1517", "tinta": "#F5ECEE",
        "suave": "#BFAEB2", "borde": "#3A2C30", "rojo": "#FF4D5E", "rojo_fondo": "#3A1A20",
        "rojo_texto": "#FFC2C9", "nocrit": "#8A8F98", "nocrit_fondo": "#262A30",
        "rejilla": "#2E2427", "flecha": "#6F6467", "ok_fondo": "#12301F", "ok_borde": "#25603D",
        "ok_texto": "#9BE3B6", "mal_fondo": "#3A1A20", "mal_borde": "#7A2C37", "mal_texto": "#FFC2C9",
        "osito": "#EADCCD", "osito_borde": "#B08E78",
    },
}


def logo(c: dict, tam: int = 64, con_texto: bool = False) -> str:
    """Osito de peluche original abrazando un corazón. Con texto, el corazón dice «Detalles de Amor»."""
    texto = (
        '<text x="60" y="93" text-anchor="middle" font-family="Georgia, serif" font-size="9.5" '
        'font-weight="700" fill="#FFFFFF">Detalles</text>'
        '<text x="60" y="104" text-anchor="middle" font-family="Georgia, serif" font-size="9.5" '
        'font-weight="700" fill="#FFFFFF">de Amor</text>'
    ) if con_texto else ""
    o, b = c["osito"], c["osito_borde"]
    return f"""
<svg width="{tam}" height="{tam}" viewBox="0 0 120 120" role="img" aria-label="Logotipo de Detalles de Amor">
  <circle cx="31" cy="27" r="14" fill="{o}" stroke="{b}" stroke-width="2.5"/>
  <circle cx="89" cy="27" r="14" fill="{o}" stroke="{b}" stroke-width="2.5"/>
  <circle cx="31" cy="27" r="7" fill="#F4B6C0"/>
  <circle cx="89" cy="27" r="7" fill="#F4B6C0"/>
  <ellipse cx="60" cy="98" rx="34" ry="21" fill="{o}" stroke="{b}" stroke-width="2.5"/>
  <circle cx="60" cy="46" r="31" fill="{o}" stroke="{b}" stroke-width="2.5"/>
  <ellipse cx="60" cy="57" rx="13" ry="10" fill="#FFFBF6" stroke="{b}" stroke-width="1.5"/>
  <ellipse cx="60" cy="52.5" rx="4.6" ry="3.4" fill="#3B2A22"/>
  <path d="M55 59 Q60 64 65 59" fill="none" stroke="#3B2A22" stroke-width="2" stroke-linecap="round"/>
  <circle cx="48.5" cy="42" r="3.4" fill="#3B2A22"/>
  <circle cx="71.5" cy="42" r="3.4" fill="#3B2A22"/>
  <circle cx="42" cy="52" r="4" fill="#F4B6C0" opacity=".7"/>
  <circle cx="78" cy="52" r="4" fill="#F4B6C0" opacity=".7"/>
  <path d="M60 117 C 27 97 22 74 41 71 C 50 69.5 57 74 60 80 C 63 74 70 69.5 79 71 C 98 74 93 97 60 117 Z"
        fill="#C8102E" stroke="#8A0B20" stroke-width="1.5"/>
  {texto}
  <ellipse cx="29" cy="90" rx="8.5" ry="8" fill="{o}" stroke="{b}" stroke-width="2.2"/>
  <ellipse cx="91" cy="90" rx="8.5" ry="8" fill="{o}" stroke="{b}" stroke-width="2.2"/>
</svg>"""


def css(c: dict) -> str:
    return f"""
<style>
  .block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1200px; }}
  [data-testid="stSidebar"] {{ border-right: 1px solid {c['borde']}; }}
  h1, h2, h3, h4 {{ color: {c['tinta']}; letter-spacing: -0.01em; }}
  .marca {{ display: flex; align-items: center; gap: .9rem; }}
  .marca .nombre {{ font-family: Georgia, 'Times New Roman', serif; color: {c['rojo']};
                   font-size: 1.05rem; font-weight: 700; letter-spacing: .02em; }}
  .marca h1 {{ font-size: 1.7rem; margin: 0; padding: 0; color: {c['tinta']}; }}
  .marca p {{ color: {c['suave']}; margin: .1rem 0 0 0; font-size: .92rem; }}
  .franja {{ height: 4px; border-radius: 4px; margin: .8rem 0 1.1rem 0;
            background: linear-gradient(90deg, {c['rojo']} 0%, {c['rojo']} 35%, {c['borde']} 35%); }}
  .logo-lateral {{ text-align: center; margin: -.5rem 0 .4rem 0; }}
  .logo-lateral .lema {{ font-family: Georgia, serif; color: {c['rojo']}; font-weight: 700; font-size: 1.05rem; }}
  .logo-lateral .sub {{ color: {c['suave']}; font-size: .8rem; }}
  .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: .8rem; margin-bottom: 1rem; }}
  .kpi {{ background: {c['tarjeta']}; border: 1px solid {c['borde']}; border-top: 4px solid {c['rojo']};
          border-radius: 12px; padding: .85rem 1rem; }}
  .kpi .etq {{ color: {c['suave']}; font-size: .78rem; text-transform: uppercase; letter-spacing: .05em; }}
  .kpi .val {{ color: {c['tinta']}; font-size: 1.6rem; font-weight: 650; line-height: 1.25; }}
  .kpi .sub {{ color: {c['suave']}; font-size: .85rem; }}
  .ruta {{ background: {c['rojo_fondo']}; border: 1px solid {c['mal_borde']}; border-radius: 10px;
           padding: .7rem 1rem; color: {c['rojo_texto']}; font-weight: 600; overflow-wrap: anywhere; }}
  .alerta-ok {{ background: {c['ok_fondo']}; border: 1px solid {c['ok_borde']}; color: {c['ok_texto']};
               border-radius: 10px; padding: .7rem 1rem; }}
  .alerta-mal {{ background: {c['mal_fondo']}; border: 1px solid {c['mal_borde']}; color: {c['mal_texto']};
                border-radius: 10px; padding: .7rem 1rem; }}
  .pie {{ color: {c['suave']}; font-size: .8rem; margin-top: 1.6rem; border-top: 1px solid {c['borde']};
          padding-top: .6rem; }}
  button[data-baseweb="tab"] p {{ font-weight: 600; }}
  @media (max-width: 640px) {{
    .marca h1 {{ font-size: 1.3rem; }} .kpi .val {{ font-size: 1.35rem; }}
    .marca svg {{ width: 48px; height: 48px; }}
  }}
</style>"""
