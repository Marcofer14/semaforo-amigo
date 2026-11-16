"""Indexa los documentos de docs/ en Chroma.  Uso:  python -m scripts.construir_indice"""
from src.rag import construir_indice

if __name__ == "__main__":
    n = construir_indice()
    print(f"Índice listo: {n} fragmentos." if n else "No hay documentos en docs/. Mirá docs/LEEME.md.")
