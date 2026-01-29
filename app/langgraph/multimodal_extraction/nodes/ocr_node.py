from __future__ import annotations

import asyncio
import json
import httpx
from typing import Any

from app.core.prompts import get_vlm_ocr_system_prompt
from app.langgraph.multimodal_extraction.state import DocumentState
from app.clients.vllm_client import VllmClient
from app.core.logger import set_log
from app.enums.multimodal_extraction.enums import VllmTaskType


async def run_ocr(state: DocumentState) -> DocumentState:
    set_log("Run_ocr node")
    page_images_b64 = state.get("page_images_b64", [])
    if not page_images_b64:
        return {"ocr_pages": [], "ocr_text": ""}

    system_prompt = get_vlm_ocr_system_prompt()
    user_prompt = state.get("prompt") or "Extract the content of this page."

    # page_images_b64 = page_images_b64[:3]
    page_results: list[dict] = []

    # NOTE: httpx.AsyncClient(timeout=300) alone is NOT enough here because
    # VllmClient.chat() passes its own timeout to client.post().
    vllm_client = VllmClient(
        port="", timeout_s=300.0
    )  # port is empty when run on runpod
    semaphore = asyncio.Semaphore(10)

    def _extract_json_obj(text: str) -> dict[str, Any] | None:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        snippet = cleaned[start : end + 1]
        try:
            obj = json.loads(snippet)
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None

    async def _process_page(page_index: int, image_b64: str) -> dict:
        async with semaphore:
            try:
                resp = await vllm_client.chat(
                    client,
                    system_prompt=system_prompt,
                    user_prompt=f"Page {page_index}: {user_prompt}",
                    image_b64=image_b64,
                    task_type=VllmTaskType.OCR,
                )

                raw = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
                raw_text = raw if isinstance(raw, str) else json.dumps(raw)

                parsed = _extract_json_obj(raw_text)
                if parsed is None:
                    # 모델이 JSON 외 텍스트를 섞거나, 깨진 JSON을 줄 때가 흔해서
                    # 원문 일부를 남겨 원인 파악 가능하게 한다.
                    return {
                        "page": page_index,
                        "error": "Invalid JSON from model",
                        "error_type": "json_decode",
                        "raw_preview": str(raw_text)[:500],
                    }

                parsed["page"] = page_index
                return parsed
            except httpx.TimeoutException as e:
                return {
                    "page": page_index,
                    "error": str(e),
                    "error_type": "timeout",
                }
            except httpx.HTTPStatusError as e:
                body_preview = ""
                try:
                    body_preview = (e.response.text or "")[:500]
                except Exception:
                    body_preview = ""
                return {
                    "page": page_index,
                    "error": str(e),
                    "error_type": "http_status",
                    "status_code": getattr(e.response, "status_code", None),
                    "body_preview": body_preview,
                }
            except Exception as e:
                return {
                    "page": page_index,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }

    async with httpx.AsyncClient(timeout=300.0, trust_env=False) as client:
        tasks = [
            _process_page(page_index=i, image_b64=img)
            for i, img in enumerate(page_images_b64, start=1)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

    page_results: list[dict] = []
    for i, r in enumerate(results, start=1):
        if isinstance(r, Exception):
            set_log(f"OCR failed for page {i}: {type(r).__name__}: {r}")
            # 실패한 페이지도 결과 리스트에 남겨서 후처리/재시도 가능하게
            page_results.append(
                {"page": i, "error": str(r), "error_type": type(r).__name__}
            )
        else:
            page_results.append(r)

    set_log(f"Completed OCR for page document ({len(page_images_b64)} pages)")

    return {"ocr_pages": page_results}
