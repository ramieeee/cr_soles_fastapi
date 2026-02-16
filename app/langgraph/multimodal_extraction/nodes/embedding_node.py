from __future__ import annotations

from typing import Any

import httpx
from app.langgraph.multimodal_extraction.state import DocumentState
from app.clients.embedding_client import EmbeddingClient

from app.core.logger import set_log


async def embed_data(state: DocumentState) -> DocumentState:
    set_log("Embed node")
    bi = state.get("bibliographic_info") or {}
    set_log(f"Bibliographic information for embedding: {bi}")

    title = bi.get("title", "")
    abstract = bi.get("abstract", "")

    text_to_embed = f"{title}\n\n{abstract}".strip()
    set_log(f"Text to embed: {text_to_embed[:500]}")
    if not text_to_embed:
        raise ValueError("No text available for embedding.")

    # Same rationale as OCR node: EmbeddingClient.embed() uses its own timeout.
    embedding_client = EmbeddingClient(port="")

    async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
        resp = await embedding_client.embed(
            client,
            input=text_to_embed,
        )
        set_log("EmbeddingClient.embed called")

    return {
        "embedding": resp.get("data", [{}])[0].get("embedding", []),
    }
