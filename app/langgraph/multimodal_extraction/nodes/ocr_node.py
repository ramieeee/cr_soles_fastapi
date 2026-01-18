from __future__ import annotations

import asyncio
import json
import httpx

from app.core.prompts import get_vlm_ocr_system_prompt
from app.langgraph.multimodal_extraction.state import DocumentState
from app.clients.vllm_client import VllmClient
from app.core.logger import set_log


async def run_ocr(state: DocumentState) -> DocumentState:
    set_log("run_ocr node")
    page_images_b64 = state.get("page_images_b64", [])
    if not page_images_b64:
        return {"ocr_pages": [], "ocr_text": ""}

    system_prompt = get_vlm_ocr_system_prompt()
    user_prompt = state.get("prompt") or "Extract the content of this page."

    page_images_b64 = page_images_b64[:3]
    page_results: list[dict] = []

    vllm_client = VllmClient(port="")  # port is empty when run on runpod
    semaphore = asyncio.Semaphore(3)

    async def _process_page(page_index: int, image_b64: str) -> dict:
        async with semaphore:
            resp = await vllm_client.chat(
                client,
                system_prompt=system_prompt,
                user_prompt=f"Page {page_index}: {user_prompt}",
                image_b64=image_b64,
            )

            raw = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            json_loaded = json.loads(raw) if isinstance(raw, str) else (raw or {})
            json_loaded["page"] = page_index
            return json_loaded

    async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
        tasks = [
            _process_page(page_index=i, image_b64=img)
            for i, img in enumerate(page_images_b64, start=1)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

    page_results: list[dict] = []
    for i, r in enumerate(results, start=1):
        if isinstance(r, Exception):
            # 실패한 페이지도 결과 리스트에 남겨서 후처리/재시도 가능하게
            page_results.append({"page": i, "error": str(r)})
        else:
            page_results.append(r)

    print(f"Completed OCR for page document ({len(page_images_b64)} pages)")

    return {"ocr_pages": page_results}
