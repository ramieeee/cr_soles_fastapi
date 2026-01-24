from __future__ import annotations
from typing import Any, Optional
import httpx
from app.core.config import settings
from app.core.logger import set_log


class EmbeddingClient:
    def __init__(
        self,
        base_url: str | None = None,
        port: int | None = None,
        model_name: str | None = None,
        api_key: str | None = None,
        timeout_s: float = 60.0,
    ):
        self.base_url = (base_url or settings.embedding_base_url).rstrip("/")
        self.port = port
        self.model = model_name or settings.embedding_model
        self.api_key = api_key or getattr(settings, "embedding_api_key", "EMPTY")

        self.chat_url = (
            f"{self.base_url}:{self.port}/v1/embeddings"
            if self.port != ""
            else f"{self.base_url}/v1/embeddings"
        )
        self.timeout = httpx.Timeout(timeout_s)

        set_log(
            f"EmbeddingClient initialized with base_url={self.base_url}, port={self.port}, model={self.model}"
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def embed(
        self,
        client: httpx.AsyncClient,
        *,
        input: str,
        max_tokens: Optional[int] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Single embed entrypoint.
        """
        set_log("EmbeddingClient.embed called")

        set_log(f"Input text for embedding: {input[:100]}")

        payload: dict[str, Any] = {
            "model": self.model,
            "input": input,
        }

        response = await client.post(
            self.chat_url,
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        set_log(f"Response from EmbeddingClient.embed: {response.text[:100]}")
        response.raise_for_status()
        return response.json()
