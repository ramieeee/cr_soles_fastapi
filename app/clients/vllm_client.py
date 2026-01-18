from __future__ import annotations

from typing import Any, Optional

import httpx

from app.core.config import settings


class VllmClient:
    def __init__(
        self,
        base_url: str | None = None,
        port: int | None = None,
        model_name: str | None = None,
        api_key: str | None = None,
        timeout_s: float = 120.0,
    ):
        self.base_url = (base_url or settings.vllm_base_url).rstrip("/")
        self.port = port or settings.vllm_port
        self.model = model_name or settings.vllm_model
        self.api_key = api_key or getattr(settings, "vllm_api_key", "EMPTY")

        self.chat_url = f"{self.base_url}:{self.port}/v1/chat/completions"
        self.timeout = httpx.Timeout(timeout_s)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_user_message(
        self,
        user_prompt: str,
        image_b64: Optional[str],
        image_mime: str = "image/png",
    ) -> dict[str, Any]:
        """
        Build OpenAI-compatible user message.
        Image handling is purely structural.
        """
        if not image_b64:
            return {
                "role": "user",
                "content": user_prompt,
            }

        return {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{image_mime};base64,{image_b64}"},
                },
            ],
        }

    async def chat(
        self,
        client: httpx.AsyncClient,
        *,
        system_prompt: str,
        user_prompt: str,
        image_b64: Optional[str] = None,
        image_mime: str = "image/png",
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Single chat entrypoint.

        Caller decides:
        - system_prompt content
        - whether image_b64 is passed
        """
        messages = [
            {"role": "system", "content": system_prompt},
            self._build_user_message(
                user_prompt=user_prompt,
                image_b64=image_b64,
                image_mime=image_mime,
            ),
        ]

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if extra:
            payload.update(extra)

        response = await client.post(
            self.chat_url,
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
