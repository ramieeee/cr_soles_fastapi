from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.prompts import (
    get_metadata_determine_completion_prompt,
    get_metadata_extraction_prompt,
)
from app.langgraph.multimodal_extraction.state import DocumentState
from app.clients.embedding_client import EmbeddingClient

from app.core.logger import set_log
from app.core.config import settings


async def embed_data(state: DocumentState) -> DocumentState:
    set_log("Embed node")
    metadata = state.get("metadata") or {}
    set_log(f"Metadata for embedding: {metadata}")

    title = metadata.get("title", "")
    abstract = metadata.get("abstract", "")

    text_to_embed = f"{title}\n\n{abstract}".strip()
    set_log(f"Text to embed: {text_to_embed[:500]}")
    if not text_to_embed:
        raise ValueError("No text available for embedding.")

    port = settings.embedding_port if hasattr(settings, "embedding_port") else 8008

    # Same rationale as OCR node: EmbeddingClient.embed() uses its own timeout.
    embedding_client = EmbeddingClient(port=port)

    async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
        resp = await embedding_client.embed(
            client,
            input=text_to_embed,
        )
        set_log("EmbeddingClient.embed called")

    return {
        "embeddings": resp.get("data", [{}])[0].get("embedding", []),
    }
