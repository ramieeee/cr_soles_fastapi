from __future__ import annotations

import json
import re

import httpx

from app.core.prompts import get_vlm_ocr_system_prompt
from app.langgraph.multimodal_extraction.state import DocumentState
from app.clients.vllm_client import VllmClient


async def run_ocr(state: DocumentState) -> DocumentState:
    print("Starting OCR for document pages...")
    page_images_b64 = state.get("page_images_b64", [])
    if not page_images_b64:
        return {"ocr_pages": [], "ocr_text": ""}

    system_prompt = get_vlm_ocr_system_prompt()
    user_prompt = state.get("prompt") or "Extract the content of this page."

    page_images_b64 = page_images_b64[:3]
    page_results: list[dict] = []

    vllm_client = VllmClient(port="")  # port is empty when run on runpod
    async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
        for page_index, image_b64 in enumerate(page_images_b64, start=1):
            response = await vllm_client.chat(
                client,
                system_prompt=system_prompt,
                user_prompt=f"Page {page_index}: {user_prompt}",
                image_b64=image_b64,
            )
            content = json.loads(response.get("response", "{}"))
            page_results.append(content)
        print(f"Completed OCR for page document ({page_index} pages)")

    return {"ocr_pages": page_results}
