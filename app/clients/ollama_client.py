from __future__ import annotations

import httpx

from app.core.config import settings


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        port: int | None = None,
        model_name: str | None = None,
    ):
        base_url = base_url or settings.ollama_base_url
        ollama_port = port or settings.ollama_port
        self.chat_url = f"{base_url}:{ollama_port}/api/chat"
        self.generate_url = f"{base_url}:{ollama_port}/api/generate"
        self.model_name = model_name or settings.ollama_model

    async def chat_with_fallback(
        self,
        client: httpx.AsyncClient,
        system_prompt: str = "",
        user_prompt: str = "",
        image_b64: str = "",
    ) -> dict:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": user_prompt,
                    "images": [image_b64],
                },
            ],
            "stream": False,
        }
        response = await client.post(self.chat_url, json=payload)
        if response.status_code == 404:
            generate_payload = {
                "model": self.model_name,
                "options": {"reasoning": False},
                "prompt": f"{system_prompt} {user_prompt}".strip(),
                "images": [image_b64],
                "stream": False,
            }
            response = await client.post(self.generate_url, json=generate_payload)

        response.raise_for_status()
        return response.json()

    async def generate_text(
        self,
        client: httpx.AsyncClient,
        prompt: str,
    ) -> dict:
        payload = {
            "model": self.model_name,
            "options": {"reasoning": False},
            "prompt": prompt,
            "stream": False,
        }
        response = await client.post(self.generate_url, json=payload)
        response.raise_for_status()
        return response.json()
