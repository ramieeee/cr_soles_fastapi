from __future__ import annotations

import json

import httpx

from app.core.prompts import get_vlm_ocr_system_prompt
from app.langgraph.multimodal_extraction.state import DocumentState
from app.clients.ollama_client import OllamaClient


def _extract_ollama_text(payload: dict) -> str:
    if "message" in payload and isinstance(payload["message"], dict):
        content = str(payload["message"].get("content", "")).strip()
    else:
        content = str(payload.get("response", "")).strip()

    if not content:
        return ""

    # Some models wrap JSON in a string; prefer the inner "text" field if present.
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict) and isinstance(parsed.get("text"), str):
            return parsed["text"].strip()
    except json.JSONDecodeError:
        pass

    return content


async def run_ocr(state: DocumentState) -> DocumentState:
    page_images_b64 = state.get("page_images_b64", [])
    if not page_images_b64:
        return {"ocr_pages": [], "ocr_text": ""}

    system_prompt = get_vlm_ocr_system_prompt()
    user_prompt = state.get("prompt") or "Extract the content of this page."

    page_images_b64 = page_images_b64[:10]
    page_results: list[dict] = []

    ollama_client = OllamaClient()
    async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
        for page_index, image_b64 in enumerate(page_images_b64, start=1):
            response_payload = await ollama_client.chat_with_fallback(
                client,
                system_prompt=system_prompt,
                user_prompt=f"Page {page_index}: {user_prompt}",
                image_b64=image_b64,
            )
            result = {
                "page": page_index,
                "ollama": response_payload,
                "text": _extract_ollama_text(response_payload),
            }
            page_results.append(result)

    ocr_text = "\n\n".join(
        [
            page_result.get("text", "")
            for page_result in page_results
            if page_result.get("text")
        ]
    )

    return {"ocr_pages": page_results, "ocr_text": ocr_text}
