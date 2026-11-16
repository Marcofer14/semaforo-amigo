"""RAG: indexa los documentos de docs/ en Chroma y recupera fragmentos con su fuente."""
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import DOCS, EMBEDDINGS, INDICE

COLECCION = "semaforo"


class EmbeddingsLocales(Embeddings):
    """Embeddings multilingües que corren en la compu (fastembed, sin GPU ni API)."""

    def __init__(self, modelo: str = EMBEDDINGS):
        from fastembed import TextEmbedding
        self._modelo = TextEmbedding(modelo)

    def embed_documents(self, textos):
        return [v.tolist() for v in self._modelo.embed(list(textos))]

    def embed_query(self, texto):
        return self.embed_documents([texto])[0]


def leer_documentos() -> list[Document]:
    """Lee PDF, .txt y .md de docs/. Cada página de PDF conserva su número para poder citarla."""
    from pypdf import PdfReader
    documentos = []
    for ruta in sorted(DOCS.iterdir()):
        if ruta.name.upper().startswith("LEEME"):
            continue
        if ruta.suffix.lower() == ".pdf":
            for n, pagina in enumerate(PdfReader(ruta).pages, start=1):
                texto = (pagina.extract_text() or "").strip()
                if texto:
                    documentos.append(Document(texto, metadata={"fuente": ruta.name, "pagina": n}))
        elif ruta.suffix.lower() in {".txt", ".md"}:
            documentos.append(Document(ruta.read_text(encoding="utf-8"), metadata={"fuente": ruta.name, "pagina": 0}))
    return documentos


def construir_indice(embeddings: Embeddings | None = None) -> int:
    documentos = leer_documentos()
    if not documentos:
        return 0
    trozos = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150).split_documents(documentos)
    base = Chroma(COLECCION, embeddings or EmbeddingsLocales(), persist_directory=str(INDICE))
    base.reset_collection()
    base.add_documents(trozos)
    return len(trozos)


@lru_cache
def _base() -> Chroma | None:
    if not INDICE.exists():
        return None
    return Chroma(COLECCION, EmbeddingsLocales(), persist_directory=str(INDICE))


def buscar(consulta: str, k: int = 3, base: Chroma | None = None) -> list[dict]:
    """Devuelve hasta k fragmentos: texto, fuente, página y distancia (menor = más parecido)."""
    base = base or _base()
    if base is None:
        return []
    return [
        {"texto": d.page_content, "fuente": d.metadata["fuente"], "pagina": d.metadata["pagina"], "distancia": round(float(s), 3)}
        for d, s in base.similarity_search_with_score(consulta, k=k)
    ]


def cita(fragmento: dict) -> str:
    pagina = f", pág. {fragmento['pagina']}" if fragmento["pagina"] else ""
    return f"{fragmento['fuente']}{pagina}"
