from __future__ import annotations

import httpx
from app.clients.embedding_client import EmbeddingClient
from typing import Mapping, Any, TypedDict


from app.core.logger import set_log


class EmbeddingData(TypedDict, total=False):
    bibliographic_info: dict
    embedding: list[float]


def _bi_to_text(bi: Mapping[str, Any]) -> str:
    title = (bi.get("title") or "")
    abstract = (bi.get("abstract") or "")
    return f"{title}\n\n{abstract}".strip()


async def embed_bibliographic_info(bi: Mapping[str, Any]) -> EmbeddingData:
    text_to_embed = _bi_to_text(bi)

    if not text_to_embed:
        raise ValueError("No text available for embedding.")

    # Same rationale as OCR node: EmbeddingClient.embed() uses its own timeout.
    embedding_client = EmbeddingClient(port="")

    async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
        resp = await embedding_client.embed(
            client,
            input=text_to_embed,
        )

    return {
        "embedding": resp.get("data", [{}])[0].get("embedding", []),
    }


def embed_bibliographic_info_sync(bi: Mapping[str, Any]) -> EmbeddingData:
    """Sync variant for sync service/repository call sites."""
    text_to_embed = _bi_to_text(bi)
    if not text_to_embed:
        raise ValueError("No text available for embedding.")

    embedding_client = EmbeddingClient(port="")
    with httpx.Client(timeout=300.0, trust_env=False) as client:
        resp = embedding_client.embed_sync(
            client,
            input=text_to_embed,
        )

    return {
        "embedding": resp.get("data", [{}])[0].get("embedding", []),
    }
