from __future__ import annotations

from app.langgraph.multimodal_extraction.state import DocumentState
from app.clients.embedding_client import EmbeddingClient

from app.core.logger import set_log
from app.utils.embedding import embed_bibliographic_info


async def embed_data(state: DocumentState) -> DocumentState:
    set_log("Embed node")
    bi = state.get("bibliographic_info") or {}

    embedded_data = await embed_bibliographic_info(bi)
    set_log(f"Embedded data length: {len(embedded_data.get('embedding', []))}")

    return {
        "embedding": embedded_data.get("embedding", []),
    }
