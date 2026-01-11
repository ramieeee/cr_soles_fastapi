from __future__ import annotations

import json

import httpx

from app.core.config import settings
from app.core.prompts import get_vlm_ocr_system_prompt
from app.langgraph.multimodal_extraction.state import DocumentState


class OllamaClient:
    def __init__(self):
        self.chat_url = f"{settings.ollama_base_url}/api/chat"
        self.generate_url = f"{settings.ollama_base_url}/api/generate"

    async def chat(
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
        return response.json()
