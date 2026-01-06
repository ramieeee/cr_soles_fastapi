from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.prompts import get_vlm_ocr_system_prompt
from app.langgraph.state import DocumentState


def _extract_ollama_text(payload: dict) -> str:
    if "message" in payload and isinstance(payload["message"], dict):
        return str(payload["message"].get("content", "")).strip()
    return str(payload.get("response", "")).strip()


async def run_ocr(state: DocumentState) -> DocumentState:
    page_images_b64 = state.get("page_images_b64", [])
    page_images_b64 = page_images_b64[:1]  # TODO remove this after testing
    if not page_images_b64:
        return {"ocr_pages": [], "ocr_text": ""}

    system_prompt = get_vlm_ocr_system_prompt()
    user_prompt = state.get("prompt") or "Extract the content of this page."

    page_images_b64 = page_images_b64[:10]
    page_results: list[dict] = []

    print("Starting OCR process with Ollama...")
    async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
        chat_url = f"{settings.ollama_base_url}/api/chat"
        generate_url = f"{settings.ollama_base_url}/api/generate"
        for page_index, image_b64 in enumerate(page_images_b64, start=1):
            payload = {
                "model": settings.ollama_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"/no_think Page {page_index}: {user_prompt}",
                        "images": [image_b64],
                    },
                ],
                "stream": False,
            }

            response = await client.post(chat_url, json=payload)
            if response.status_code == 404:
                generate_payload = {
                    "model": settings.ollama_model,
                    "prompt": f"{system_prompt} Page {page_index}: {user_prompt}",
                    "images": [image_b64],
                    "stream": False,
                }
                response = await client.post(generate_url, json=generate_payload)

            response.raise_for_status()
            response_payload = response.json()
            result = {
                "page": page_index,
                "ollama": response_payload,
                "text": _extract_ollama_text(response_payload),
            }
            print(f"OCR Page {page_index} Result: {result['text'][:100]}...")
            page_results.append(result)

    ocr_text = "\n\n".join(
        [
            page_result.get("text", "")
            for page_result in page_results
            if page_result.get("text")
        ]
    )

    return {"ocr_pages": page_results, "ocr_text": ocr_text}
