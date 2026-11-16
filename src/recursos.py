"""Líneas de ayuda verificadas. Nunca se inventan: si no hay para el país, se dice."""
import json
from functools import lru_cache

from .config import RECURSOS


@lru_cache
def _cargar() -> dict:
    return json.loads(RECURSOS.read_text(encoding="utf-8"))


def recursos_generales() -> list[dict]:
    return _cargar()["generales"]


def recursos_de_pais(pais: str) -> list[dict]:
    return _cargar()["paises"].get(pais.lower().strip(), [])


def recursos_por_tema(pais: str, tema: str) -> list[dict]:
    """Líneas del país que sirven para un tema (bullying, riesgo_de_vida, peligro...)."""
    return [r for r in recursos_de_pais(pais) if tema in r.get("temas", [])]


def tarjeta_telefonos(pais: str) -> str:
    """Lista completa en lenguaje para chicos (botón '¿A quién puedo llamar?')."""
    lineas = recursos_de_pais(pais)
    if not lineas:
        return ("Todavía no tengo teléfonos verificados para tu país. "
                "Lo más importante: contale a un **adulto de confianza**.")
    partes = ["## 📞 Teléfonos que ayudan", "Lo primero siempre es contarle a un **adulto de confianza**. Estos teléfonos también ayudan:", ""]
    partes += [f"- {r['emoji']} **{r['nombre']}**  \n  {r['para_chicos']}" for r in lineas]
    return "\n".join(partes)


def bloque_adulto(lineas: list[dict]) -> str:
    """Detalle con fuente, para el adulto que acompaña."""
    return "\n".join(f"- **{r['nombre']}**: {r['detalle']} [Fuente]({r['fuente']})" for r in lineas)
