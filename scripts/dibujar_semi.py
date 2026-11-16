"""Genera los dibujos animados de Semi (personaje original) en public/.  Uso: python -m scripts.dibujar_semi"""
from src.config import RAIZ

LUCES = {"rojo": ("#ff5a5f", "#7a3038", 52), "amarillo": ("#ffd23f", "#7a6a2a", 100), "verde": ("#3ddc84", "#2a6a48", 148)}
BOCAS = {
    "verde": '<path d="M-9 5 Q0 14 9 5" fill="none" stroke="#2b2135" stroke-width="3" stroke-linecap="round"/>',
    "amarillo": '<path d="M-7 8 H7" fill="none" stroke="#2b2135" stroke-width="3" stroke-linecap="round"/>',
    "rojo": '<path d="M-8 10 Q0 3 8 10" fill="none" stroke="#2b2135" stroke-width="3" stroke-linecap="round"/>',
    "hola": '<path d="M-9 4 Q0 15 9 4 Z" fill="#2b2135"/>',
}
ESTILO = """
@keyframes saludo{0%,100%{transform:rotate(0)}50%{transform:rotate(-28deg)}}
@keyframes brillo{0%,100%{opacity:.35}50%{opacity:.85}}
@keyframes salto{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
@keyframes parpadeo{0%,92%,100%{transform:scaleY(1)}96%{transform:scaleY(.1)}}
.cuerpo{animation:salto 2.4s ease-in-out infinite}
.brazo{animation:saludo 1.1s ease-in-out infinite;transform-origin:150px 100px}
.halo{animation:brillo 1.6s ease-in-out infinite}
.ojos{animation:parpadeo 4s infinite;transform-box:fill-box;transform-origin:center}
@media(prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def semi(estado: str, tam: int = 170) -> str:
    activas = list(LUCES) if estado == "hola" else [estado]
    cara_y = LUCES["amarillo"][2] if estado == "hola" else LUCES[estado][2]
    luces = ""
    for nombre, (viva, apagada, y) in LUCES.items():
        if nombre in activas:
            luces += f'<circle class="halo" cx="100" cy="{y}" r="27" fill="{viva}"/>'
        luces += f'<circle cx="100" cy="{y}" r="20" fill="{viva if nombre in activas else apagada}" stroke="#2b2135" stroke-width="3"/>'
    brazo_der = ('<g class="brazo"><path d="M150 100 L178 74" stroke="#5b3a9b" stroke-width="9" stroke-linecap="round"/><circle cx="180" cy="72" r="9" fill="#ffd9b8" stroke="#2b2135" stroke-width="2.5"/></g>'
                 if estado in ("hola", "verde") else
                 '<path d="M150 104 L176 122" stroke="#5b3a9b" stroke-width="9" stroke-linecap="round"/><circle cx="178" cy="124" r="9" fill="#ffd9b8" stroke="#2b2135" stroke-width="2.5"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 230" width="{tam}" height="{int(tam*1.15)}" role="img" aria-label="Semi, el semáforo amigo ({estado})">
<style>{ESTILO}</style>
<ellipse cx="100" cy="220" rx="52" ry="7" fill="#2b2135" opacity=".15"/>
<g class="cuerpo">
<path d="M82 176 V204 M118 176 V204" stroke="#5b3a9b" stroke-width="10" stroke-linecap="round"/>
<ellipse cx="78" cy="208" rx="13" ry="7" fill="#ff8a5c" stroke="#2b2135" stroke-width="2.5"/><ellipse cx="122" cy="208" rx="13" ry="7" fill="#ff8a5c" stroke="#2b2135" stroke-width="2.5"/>
<path d="M50 104 L24 122" stroke="#5b3a9b" stroke-width="9" stroke-linecap="round"/><circle cx="22" cy="124" r="9" fill="#ffd9b8" stroke="#2b2135" stroke-width="2.5"/>
{brazo_der}
<rect x="52" y="18" width="96" height="164" rx="34" fill="#7c5cff" stroke="#2b2135" stroke-width="4"/>
<path d="M64 40 Q64 28 78 26" stroke="#fff" stroke-opacity=".5" stroke-width="5" fill="none" stroke-linecap="round"/>
{luces}
<g transform="translate(100 {cara_y})"><g class="ojos"><circle cx="-8" cy="-4" r="3.6" fill="#2b2135"/><circle cx="8" cy="-4" r="3.6" fill="#2b2135"/></g>{BOCAS[estado]}</g>
</g></svg>'''


def main():
    publico = RAIZ / "public"
    (publico / "avatars").mkdir(parents=True, exist_ok=True)
    for estado in ["hola", "verde", "amarillo", "rojo"]:
        (publico / f"semi_{estado}.svg").write_text(semi(estado), encoding="utf-8")
    for nombre in ["logo_light.svg", "logo_dark.svg", "favicon.svg", "avatars/semi.svg"]:
        (publico / nombre).write_text(semi("hola", 200), encoding="utf-8")


if __name__ == "__main__":
    main()
