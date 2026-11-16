"""Guardrail: corre ANTES del agente y no depende del análisis de sentimiento.

Si detecta una señal de riesgo, corta el flujo normal: el LLM no responde y se
devuelve un mensaje fijo que deriva a un adulto de confianza y a recursos verificados.
Es un filtro por patrones: prioriza no dejar pasar casos (prefiere falsos positivos).
"""
import re
import unicodedata

from .recursos import bloque_adulto, recursos_por_tema


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


PATRONES = {
    "riesgo_de_vida": [
        r"no quier\w+ (seguir )?vivi", r"quier\w+ morir", r"morirme", r"matarme", r"matarse",
        r"suicid", r"hacer(me|se) dano", r"lastimar(me|se) a (mi|si) mism",
        r"desaparecer para siempre", r"no quier\w+ estar mas (aca|vivo|viva)",
    ],
    "adulto_que_lastima": [
        r"(papa|mama|padrastro|madrastra|tio|tia|abuelo|abuela|adulto|persona grande|senor|senora|profe|vecino)\b.{0,25}\bme (pega|lastima|golpea|toca|toco)",
        r"me (pega|pegan|lastiman|golpean) en (mi )?casa", r"en (mi )?casa .{0,15}me (pega|pegan)",
        r"me toca\w* .{0,25}(no me gusta|partes|cuerpo)", r"cosas que no me gustan",
        r"secreto.{0,40}(miedo|asusta|no (le )?(cuente|diga))", r"(miedo|asusta).{0,40}secreto",
    ],
    "contacto_peligroso": [
        r"fotos? (sin ropa|desnud)", r"me pid\w+ fotos", r"(desconocid|no conozco).{0,40}(escribe|habla|pide|regal)",
        r"encontrarnos sin que", r"no le diga a (nadie|mis papas)",
    ],
    "violencia_grave": [
        r"\b(cuchillo|navaja|arma|pistola|revolver)\b", r"me (va|van) a matar", r"\bsangre\b",
        r"me (ahorc|asfixi)", r"me desmay", r"al hospital",
    ],
}


def revisar(texto: str) -> str | None:
    """Devuelve la categoría de riesgo detectada, o None si no hay señales."""
    limpio = normalizar(texto)
    for categoria, patrones in PATRONES.items():
        if any(re.search(p, limpio) for p in patrones):
            return categoria
    return None


def respuesta_segura(categoria: str, pais: str) -> str:
    """Mensaje fijo: corto, sin preguntas, sin diagnóstico. Las líneas dependen de la categoría."""
    lineas_ayuda = recursos_por_tema(pais, categoria)
    texto = [
        "## 🔴 Esto es muy importante",
        "Gracias por contármelo. Fuiste muy valiente. **No es tu culpa.**",
        "",
        "**Hacé esto ahora:**",
        "1. Buscá a un **adulto de confianza** (mamá, papá, un abuelo, tu seño) y contale lo mismo que me contaste a mí.",
    ]
    for n, r in enumerate(lineas_ayuda[:2], start=2):   # como mucho dos teléfonos para el chico
        texto.append(f"{n}. {r['para_chicos']}")
    texto += [
        "",
        "Yo soy un robot y no puedo ir a ayudarte, pero una persona grande sí puede. "
        "No tenés que guardar este secreto.",
    ]
    if lineas_ayuda:
        texto += ["", "---", "👨‍👩‍👧 **Para el adulto que acompaña**", bloque_adulto(lineas_ayuda)]
    return "\n".join(texto)
