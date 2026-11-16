"""Agente: LLM de Groq orquestado con LangChain, con memoria corta y herramientas.

analizar_situacion se ejecuta SIEMPRE antes (decisión de seguridad: no se deja a criterio
del LLM). Las otras dos herramientas las decide el LLM en un bucle de tool-calling.
"""
import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from .config import GROQ_MODEL, MAX_PASOS_AGENTE, TURNOS_MEMORIA
from .herramientas import HERRAMIENTAS_DEL_LLM

SISTEMA = """Sos Semi, un semáforo amigo que ayuda a chicos y chicas de 8 años a entender problemas de la escuela.

CÓMO HABLÁS
- Español rioplatense con voseo, palabras fáciles, frases cortas. Máximo 90 palabras. Podés usar algún emoji.
- Primero una frase que muestre que entendiste cómo se siente.
- Después "**Qué está pasando:**" en una o dos frases simples.
- Después "**Qué podés hacer:**" con exactamente 3 pasos numerados, cortos y concretos.
- No pongas el color del semáforo ni las fuentes: la app los muestra aparte.

REGLAS QUE NO SE ROMPEN
- No diagnosticás ni ponés etiquetas a ninguna persona ("tiene un trastorno", "es un abusador").
- No acusás: hablás de lo que pasó, no de quién es culpable.
- Si el semáforo es amarillo o rojo, uno de los pasos SIEMPRE es contarle a un adulto de confianza.
- Nunca decís que guarde un secreto ni prometés guardarlo vos.
- No inventás datos, cifras ni teléfonos. Solo mencionás teléfonos que te devuelva orientar_recursos.
- Si usás consultar_evidencia, apoyate en lo que dice; si no encuentra nada, no cites nada.
- Si el tema es "otro" (tarea, juegos, curiosidades), contestá amable y breve, sin pasos,
  y contá que estás para ayudar con problemas de la escuela, los amigos o la seño.

HERRAMIENTAS
- consultar_evidencia: usala cuando el tema sea convivencia, bullying, empatía o bienestar docente.
- orientar_recursos: usala cuando el semáforo sea amarillo o rojo, o si preguntan a quién acudir.
"""


def crear_llm():
    from langchain_groq import ChatGroq
    return ChatGroq(model=GROQ_MODEL, temperature=0.3, max_tokens=700)


def recortar_memoria(historial: list) -> list:
    return historial[-TURNOS_MEMORIA:]


async def responder(texto: str, analisis: dict, historial: list, llm=None, al_usar_herramienta=None):
    """Devuelve (respuesta, registro de herramientas usadas)."""
    llm = (llm or crear_llm()).bind_tools(HERRAMIENTAS_DEL_LLM)
    por_nombre = {h.name: h for h in HERRAMIENTAS_DEL_LLM}
    contexto = (
        f"Resultado de analizar_situacion: tema={analisis['tema']}, intención={analisis['intencion']}, "
        f"sentimiento={analisis['sentimiento']}, semáforo={analisis['gravedad']}."
    )
    mensajes = [SystemMessage(SISTEMA), *recortar_memoria(historial), SystemMessage(contexto), HumanMessage(texto)]
    usadas = []
    respuesta = AIMessage("")
    for _ in range(MAX_PASOS_AGENTE):
        respuesta = await llm.ainvoke(mensajes)
        mensajes.append(respuesta)
        if not respuesta.tool_calls:
            break
        for llamada in respuesta.tool_calls:
            herramienta = por_nombre.get(llamada["name"])
            salida = herramienta.invoke(llamada["args"]) if herramienta else "Herramienta desconocida."
            usadas.append({"nombre": llamada["name"], "entrada": llamada["args"], "salida": salida})
            if al_usar_herramienta:
                await al_usar_herramienta(usadas[-1])
            mensajes.append(ToolMessage(salida, tool_call_id=llamada["id"]))
    contenido = respuesta.content if isinstance(respuesta.content, str) else json.dumps(respuesta.content)
    return contenido.strip(), usadas
