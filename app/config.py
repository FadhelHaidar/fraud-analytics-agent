# config.py
"""
Clean, import-friendly factories for embeddings, LLM, vector store, and Vanna.
- No side effects at import time.
- All initializers are small, composable functions.
- get_vanna() is cached so you can import and reuse it safely.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional, Dict
from urllib.parse import urlparse

from langchain.chat_models import init_chat_model
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

# vanna
from vanna.mistral import Mistral as VannaMistral
from vanna.qdrant import Qdrant_VectorStore as VannaQdrant_VectorStore

from app.settings import settings


# ===== Defaults (override via function args if needed) =====
DEFAULT_EMBED_MODEL = "Qwen/Qwen3-Embedding-0.6B"
DEFAULT_LLM_MODEL = "groq:meta-llama/llama-4-maverick-17b-128e-instruct"
DEFAULT_CODER_MODEL = "codestral-latest"
DEFAULT_QDRANT_COLLECTION = "my_documents"


# ===== Embeddings / LLM / Qdrant =====
def get_embeddings(model_name: str = DEFAULT_EMBED_MODEL) -> HuggingFaceEmbeddings:
    """Return a HuggingFace embeddings model."""
    return HuggingFaceEmbeddings(model_name=model_name)


def get_llm(
    model: str = DEFAULT_LLM_MODEL,
    temperature: float = 0.2,
    api_key: Optional[str] = None,
):
    """Return a chat model (LangChain interface)."""
    return init_chat_model(
        model=model,
        api_key=api_key or settings.groq_api_key,
        temperature=temperature,
    )


def get_qdrant_client(url: Optional[str] = None) -> QdrantClient:
    """Return a Qdrant client; prefers provided URL, falls back to settings."""
    return QdrantClient(url=url or settings.qdrant_url)


def get_vector_store(
    collection_name: str = DEFAULT_QDRANT_COLLECTION,
    embeddings: Optional[HuggingFaceEmbeddings] = None,
    qdrant_url: Optional[str] = None,
) -> QdrantVectorStore:
    """Return a Qdrant VectorStore for an existing collection."""
    return QdrantVectorStore.from_existing_collection(
        embedding=embeddings or get_embeddings(),
        collection_name=collection_name,
        url=qdrant_url or settings.qdrant_url,
    )


# ===== Vanna (Qdrant + Mistral) =====
class MyVanna(VannaQdrant_VectorStore, VannaMistral):
    """
    Vanna that uses Qdrant as the vector store and Mistral as the coder model.
    Construct with a config dict compatible with VannaQdrant_VectorStore and VannaMistral.
    """

    def __init__(self, config: Optional[Dict] = None):
        VannaQdrant_VectorStore.__init__(self, config=config)
        VannaMistral.__init__(
            self,
            config={
                "api_key": settings.mistral_api_key,
                "model": DEFAULT_CODER_MODEL,
                **({} if config is None else config),
            },
        )


def _pg_conn_kwargs_from_url(pg_url: str) -> Dict[str, Optional[str]]:
    """Parse a postgres URL into keyword args for connect_to_postgres."""
    parsed = urlparse(pg_url)
    return {
        "host": parsed.hostname,
        "dbname": parsed.path[1:] if parsed.path else None,
        "user": parsed.username,
        "password": parsed.password,
        "port": parsed.port,
    }


@lru_cache(maxsize=1)
def get_vanna(
    qdrant_url: Optional[str] = None,
    connect_postgres: bool = True,
    postgres_url: Optional[str] = None,
) -> MyVanna:
    """
    Return a cached MyVanna instance.

    Args:
        qdrant_url: Override Qdrant URL. Defaults to settings.qdrant_url.
        connect_postgres: If True, connects Vanna to Postgres once.
        postgres_url: Override Postgres URL. Defaults to settings.postgres_url.

    Notes:
        - Uses a cached singleton by default so repeated imports are cheap.
        - Safe to call in web handlers or background tasks—won’t reconnect repeatedly.
    """
    client = get_qdrant_client(url=qdrant_url)
    vn = MyVanna(config={"client": client})

    if connect_postgres:
        pg_url = postgres_url or settings.postgres_url
        if not pg_url:
            raise ValueError("Postgres URL is not provided or missing in settings.")
        conn_kwargs = _pg_conn_kwargs_from_url(pg_url)
        vn.connect_to_postgres(**conn_kwargs)

    return vn


# ===== Handy import surface =====
__all__ = [
    "DEFAULT_EMBED_MODEL",
    "DEFAULT_LLM_MODEL",
    "DEFAULT_CODER_MODEL",
    "DEFAULT_QDRANT_COLLECTION",
    "get_embeddings",
    "get_llm",
    "get_qdrant_client",
    "get_vector_store",
    "MyVanna",
    "get_vanna",
]
