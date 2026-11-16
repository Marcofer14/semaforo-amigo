"""NLP clásico: tema, intención, sentimiento y gravedad (semáforo) de un mensaje.

Cuatro clasificadores TF-IDF + regresión logística entrenados con data/dataset.csv
(frases ficticias). La gravedad final es el máximo entre el clasificador y unas reglas
simples, para no subestimar una situación. La gravedad describe la SITUACIÓN,
no a la persona: no es un diagnóstico ni una medida de riesgo.
"""
import re
from functools import lru_cache

import joblib

from .config import MODELO_NLP
from .guardrail import normalizar

ETIQUETAS = ["tema", "intencion", "sentimiento", "gravedad"]
ORDEN = {"verde": 0, "amarillo": 1, "rojo": 2}

REGLAS_ROJO = r"\b(me |le |les )?(peg\w+|golpe\w+|pate\w+|amenaz\w+|encerr\w+|lastim\w+)|a la fuerza|tengo miedo|me da miedo"
REGLAS_AMARILLO = r"todos los dias|siempre|nunca me dejan|burl\w+|cargan|apodo|me molestan|se rien de"


@lru_cache
def _modelos() -> dict:
    if not MODELO_NLP.exists():
        raise FileNotFoundError("Falta entrenar el NLP: corré  python -m scripts.entrenar_nlp")
    return joblib.load(MODELO_NLP)


def gravedad_por_reglas(texto: str) -> str:
    limpio = normalizar(texto)
    if re.search(REGLAS_ROJO, limpio):
        return "rojo"
    if re.search(REGLAS_AMARILLO, limpio):
        return "amarillo"
    return "verde"


def analizar(texto: str) -> dict:
    modelos = _modelos()
    salida = {}
    for etiqueta in ETIQUETAS:
        modelo = modelos[etiqueta]
        probas = modelo.predict_proba([texto])[0]
        i = probas.argmax()
        salida[etiqueta] = str(modelo.classes_[i])
        salida[f"confianza_{etiqueta}"] = round(float(probas[i]), 2)
    reglas = gravedad_por_reglas(texto)
    salida["gravedad_modelo"] = salida["gravedad"]
    salida["gravedad_reglas"] = reglas
    salida["gravedad"] = max(salida["gravedad"], reglas, key=ORDEN.get)
    return salida
