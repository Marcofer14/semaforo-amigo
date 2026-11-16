"""Semáforo Amigo: asistente para chicos de 8 años sobre convivencia en la escuela.

Flujo de cada mensaje:  guardrail -> analizar_situacion (NLP) -> agente (LLM + RAG + recursos) -> tarjeta.
Correr con:  chainlit run app.py -w
"""
import csv
import json
import re
import time
from datetime import datetime

import chainlit as cl
from langchain_core.messages import AIMessage, HumanMessage

from src import guardrail
from src.agente import responder
from src.config import METRICAS, PAIS
from src.herramientas import analizar_situacion
from src.recursos import bloque_adulto, recursos_por_tema, tarjeta_telefonos

SEMAFORO = {
    "verde": ("🟢 Luz verde", "Esto pasa a veces y se puede arreglar hablando."),
    "amarillo": ("🟡 Luz amarilla", "Esto es importante. Hay que contárselo a un adulto de confianza."),
    "rojo": ("🔴 Luz roja", "Esto es serio. Buscá a un adulto de confianza **ahora**."),
}
PIDE_TELEFONOS = re.compile(r"telefono|a quien (puedo |le puedo )?llam|a que numero|lineas? de ayuda")
PREGUNTAS = [
    ("😢 Se burlan de mí", "Se burlan de mí en la escuela todos los días."),
    ("🙅 No me dejan jugar", "No me dejan jugar con ellos en el recreo."),
    ("😠 Me peleé con un amigo", "Me peleé con mi mejor amigo por un juego."),
    ("👀 Molestan a un compañero", "Vi que a un compañero lo molestan y quiero ayudarlo."),
    ("🍎 Mi seño está triste", "Mi seño está triste porque nadie le hace caso."),
    ("📞 ¿A quién puedo llamar?", "¿A qué teléfonos puedo llamar si necesito ayuda?"),
]


@cl.set_starters
async def preguntas_pregrabadas():
    return [cl.Starter(label=etiqueta, message=mensaje) for etiqueta, mensaje in PREGUNTAS]


def registrar(ruta: str, gravedad: str, herramientas: list[str], segundos: float):
    """Guarda latencia y ruta de cada turno. No se guarda el texto del chico."""
    METRICAS.mkdir(exist_ok=True)
    archivo = METRICAS / "latencias.csv"
    nuevo = not archivo.exists()
    with archivo.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["fecha", "ruta", "gravedad", "herramientas", "segundos"])
        w.writerow([datetime.now().isoformat(timespec="seconds"), ruta, gravedad, "|".join(herramientas), round(segundos, 2)])


def fuentes_citadas(usadas: list[dict]) -> list[str]:
    """Extrae las citas [archivo, pág. N] de lo que devolvió consultar_evidencia."""
    citas = []
    for uso in usadas:
        if uso["nombre"] == "consultar_evidencia":
            citas += [c for c in re.findall(r"^\[(.+?)\]$", uso["salida"], flags=re.M) if c not in citas]
    return citas


def armar_tarjeta(analisis: dict, respuesta: str, usadas: list[dict]) -> str:
    gravedad, tema = analisis["gravedad"], analisis["tema"]
    if tema == "otro" and gravedad == "verde":
        return f"![Semi](/public/semi_hola.svg)\n\n{respuesta}"
    titulo, frase = SEMAFORO[gravedad]
    partes = [f"![Semi](/public/semi_{gravedad}.svg)", f"## {titulo}", frase, "", respuesta]

    lineas = []
    if gravedad == "rojo":
        lineas = recursos_por_tema(PAIS, "peligro")
        partes += ["", "**📞 Teléfonos que ayudan:**"] + [f"- {r['para_chicos']}" for r in lineas]
    elif tema == "bullying":
        lineas = recursos_por_tema(PAIS, "bullying")

    citas = fuentes_citadas(usadas)
    if lineas or citas:
        partes += ["", "---", "👨‍👩‍👧 **Para el adulto que acompaña**"]
        if lineas:
            partes.append(bloque_adulto(lineas))
        if citas:
            partes.append("- 📚 **Fuentes consultadas:** " + " · ".join(citas))
    return "\n".join(partes)


@cl.on_message
async def al_recibir(mensaje: cl.Message):
    inicio = time.perf_counter()
    texto = mensaje.content.strip()
    historial = cl.user_session.get("historial") or []

    # 1) Guardrail: si hay señal de riesgo se corta el flujo y NO responde el LLM.
    categoria = guardrail.revisar(texto)
    if categoria:
        salida = guardrail.respuesta_segura(categoria, PAIS)
        await cl.Message(content=f"![Semi](/public/semi_rojo.svg)\n\n{salida}").send()
        cl.user_session.set("historial", historial + [HumanMessage(texto), AIMessage(salida)])
        registrar(f"guardrail:{categoria}", "rojo", [], time.perf_counter() - inicio)
        return

    # 2) Pedido directo de teléfonos: respuesta fija con las líneas verificadas.
    if PIDE_TELEFONOS.search(guardrail.normalizar(texto)):
        await cl.Message(content=f"![Semi](/public/semi_hola.svg)\n\n{tarjeta_telefonos(PAIS)}").send()
        registrar("telefonos", "", [], time.perf_counter() - inicio)
        return

    # 3) NLP: se ejecuta siempre, antes del LLM.
    async with cl.Step(name="analizar_situacion", type="tool") as paso:
        paso.input = texto
        analisis = json.loads(analizar_situacion.invoke({"mensaje": texto}))
        paso.output = analisis

    async def mostrar(uso: dict):
        async with cl.Step(name=uso["nombre"], type="tool") as p:
            p.input = uso["entrada"]
            p.output = uso["salida"][:1500]

    # 4) Agente: el LLM decide si consulta evidencia (RAG) y recursos.
    try:
        respuesta, usadas = await responder(texto, analisis, historial, al_usar_herramienta=mostrar)
    except Exception as error:  # sin internet, sin API key o modelo dado de baja
        print(f"[agente] {type(error).__name__}: {error}")
        respuesta, usadas = ("Ahora no puedo pensar bien la respuesta. 😕 "
                             "Si te pasa algo que te preocupa, contale a un **adulto de confianza**."), []

    await cl.Message(content=armar_tarjeta(analisis, respuesta, usadas)).send()
    cl.user_session.set("historial", historial + [HumanMessage(texto), AIMessage(respuesta)])
    registrar("agente", analisis["gravedad"], ["analizar_situacion"] + [u["nombre"] for u in usadas], time.perf_counter() - inicio)
