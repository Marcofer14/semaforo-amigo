"""Evalúa la recuperación del RAG: ¿la fuente esperada aparece entre los k primeros?
Requiere el índice construido.  Uso:  python -m scripts.evaluar_rag"""
import json
import time

import pandas as pd

from src import rag
from src.config import DATOS, METRICAS

if __name__ == "__main__":
    preguntas = pd.read_csv(DATOS / "preguntas_rag.csv", sep=";")
    aciertos, tiempos = 0, []
    for fila in preguntas.itertuples():
        t0 = time.perf_counter()
        fuentes = [f["fuente"].lower() for f in rag.buscar(fila.pregunta, k=3)]
        tiempos.append(time.perf_counter() - t0)
        ok = any(fila.fuente_esperada in f for f in fuentes)
        aciertos += ok
        print(f"{'✅' if ok else '❌'} {fila.pregunta} -> {fuentes}")
    if not any(tiempos) or not rag.buscar("prueba"):
        print("No hay índice: corré antes  python -m scripts.construir_indice")
    else:
        resultado = {"preguntas": len(preguntas), "hit_at_3": round(aciertos / len(preguntas), 2),
                     "latencia_media_busqueda_s": round(sum(tiempos) / len(tiempos), 3)}
        (METRICAS / "rag.json").write_text(json.dumps(resultado, indent=2), encoding="utf-8")
        print(resultado)
