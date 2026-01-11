from __future__ import annotations

import httpx

from app.core.config import settings


class OllamaClient:
    def __init__(self):
        self.chat_url = f"{settings.ollama_base_url}/api/chat"
        self.generate_url = f"{settings.ollama_base_url}/api/generate"

    async def chat_with_fallback(
        self,
        client: httpx.AsyncClient,
        system_prompt: str = "",
        user_prompt: str = "",
        image_b64: str = "",
    ) -> dict:
        payload = {
            "model": settings.ollama_model,
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
                "model": settings.ollama_model,
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
            "model": settings.ollama_model,
            "options": {"reasoning": False},
            "prompt": prompt,
            "stream": False,
        }
        response = await client.post(self.generate_url, json=payload)
        response.raise_for_status()
        return response.json()
