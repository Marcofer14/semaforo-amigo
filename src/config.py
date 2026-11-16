"""Rutas y parámetros del proyecto en un solo lugar."""
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

DATOS = RAIZ / "data"
DOCS = RAIZ / "docs"
MODELOS = RAIZ / "modelos"
INDICE = RAIZ / "indice_chroma"
METRICAS = RAIZ / "metricas"

DATASET = DATOS / "dataset.csv"
RECURSOS = DATOS / "recursos.json"
MODELO_NLP = MODELOS / "clasificadores.joblib"

# Groq cambia seguido los modelos disponibles: revisar https://console.groq.com/docs/models
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
PAIS = os.getenv("PAIS", "argentina").lower()

TURNOS_MEMORIA = 6      # mensajes recientes que recuerda el agente
MAX_PASOS_AGENTE = 4    # vueltas máximas de herramientas por respuesta
