"""Las 3 herramientas del agente (consigna): analizar_situacion, consultar_evidencia, orientar_recursos."""
import json

from langchain_core.tools import tool

from . import nlp, rag
from .config import PAIS
from .recursos import recursos_de_pais, recursos_generales, recursos_por_tema


@tool
def analizar_situacion(mensaje: str) -> str:
    """Analiza el mensaje del chico: tema, intención, sentimiento y color del semáforo (gravedad de la situación)."""
    return json.dumps(nlp.analizar(mensaje), ensure_ascii=False)


@tool
def consultar_evidencia(pregunta: str) -> str:
    """Busca en los documentos oficiales (OMS, OIT, guías escolares argentinas) qué se recomienda hacer.
    Usala cuando necesites respaldo para un consejo. Devuelve fragmentos con su fuente y página."""
    fragmentos = rag.buscar(pregunta, k=3)
    if not fragmentos:
        return "No hay documentos indexados. No cites fuentes ni inventes datos."
    return "\n\n".join(f"[{rag.cita(f)}]\n{f['texto']}" for f in fragmentos)


@tool
def orientar_recursos(tema: str) -> str:
    """Devuelve a quién puede acudir el chico. tema: 'bullying', 'peligro' o 'general'.
    Son los ÚNICOS teléfonos que podés mencionar. Si no hay para el país, no inventes ninguno."""
    lineas = recursos_por_tema(PAIS, tema) or recursos_por_tema(PAIS, "general")
    datos = {
        "siempre": [r["para_chicos"] for r in recursos_generales()],
        "telefonos": [{"nombre": r["nombre"], "para_chicos": r["para_chicos"]} for r in lineas],
    }
    if not recursos_de_pais(PAIS):
        datos["aviso"] = f"No hay teléfonos verificados para '{PAIS}'. Recomendá solo hablar con un adulto de confianza."
    return json.dumps(datos, ensure_ascii=False)


HERRAMIENTAS_DEL_LLM = [consultar_evidencia, orientar_recursos]
