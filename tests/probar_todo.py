"""Pruebas sin API key: guardrail, NLP, recursos, RAG (embeddings falsos) y agente (LLM falso).
Uso:  python -m tests.probar_todo"""
import asyncio
import json
import tempfile

from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from src import guardrail, nlp, rag
from src.agente import responder
from src.herramientas import analizar_situacion, orientar_recursos

# Guardrail: lo que debe cortar y lo que no.
RIESGO = ["Un compañero me dijo que no quiere seguir viviendo", "mi tío me toca y no me gusta", "En mi casa me pegan",
          "un señor me dijo que guarde un secreto y me da miedo", "alguien que no conozco me pide fotos", "un chico trajo un cuchillo"]
NORMAL = ["Me peleé con mi amigo por un juego", "Qué es el bullying", "Mi seño está triste", "Hola"]
assert all(guardrail.revisar(t) for t in RIESGO), [t for t in RIESGO if not guardrail.revisar(t)]
assert not any(guardrail.revisar(t) for t in NORMAL), [t for t in NORMAL if guardrail.revisar(t)]
assert "102" in guardrail.respuesta_segura("riesgo_de_vida", "argentina")
assert "adulto de confianza" in guardrail.respuesta_segura("riesgo_de_vida", "uruguay")
print("guardrail OK")

a = nlp.analizar("Un nene más grande me pega en el recreo")
assert a["gravedad"] == "rojo", a
assert json.loads(analizar_situacion.invoke({"mensaje": "Se burlan de mí todos los días"}))["gravedad"] != "verde"
print("nlp OK", a)

assert "0800-222-1197" in orientar_recursos.invoke({"tema": "bullying"})
print("recursos OK")

# RAG con embeddings falsos (no descarga el modelo): prueba lectura, troceado, índice y cita.
with tempfile.TemporaryDirectory() as tmp:
    from pathlib import Path
    rag.DOCS, rag.INDICE = Path(tmp) / "docs", Path(tmp) / "idx"
    rag.DOCS.mkdir()
    (rag.DOCS / "prueba.md").write_text("La convivencia escolar se construye con acuerdos entre todos. " * 30, encoding="utf-8")
    falso = DeterministicFakeEmbedding(size=64)
    assert rag.construir_indice(falso) > 0
    from langchain_chroma import Chroma
    base = Chroma(rag.COLECCION, falso, persist_directory=str(rag.INDICE))
    r = rag.buscar("convivencia", k=2, base=base)
    assert r and rag.cita(r[0]) == "prueba.md", r
print("rag OK")


class LLMFalso(GenericFakeChatModel):
    def bind_tools(self, tools, **kw):
        return self


guion = iter([
    AIMessage("", tool_calls=[{"name": "orientar_recursos", "args": {"tema": "bullying"}, "id": "1"}]),
    AIMessage("Entiendo que te sientas mal.\n**Qué podés hacer:**\n1. Contale a tu seño."),
])
texto, usadas = asyncio.run(responder("Se burlan de mí", {"tema": "bullying", "intencion": "contar", "sentimiento": "negativo", "gravedad": "amarillo"}, [], llm=LLMFalso(messages=guion)))
assert usadas[0]["nombre"] == "orientar_recursos" and "seño" in texto
print("agente OK")
