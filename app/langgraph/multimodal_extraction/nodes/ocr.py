from __future__ import annotations

import json
import re

import httpx

from app.core.prompts import get_vlm_ocr_system_prompt
from app.langgraph.multimodal_extraction.state import DocumentState
from app.clients.ollama_client import OllamaClient


def _extract_ollama_content(payload: dict) -> str:
    if "message" in payload and isinstance(payload["message"], dict):
        content = str(payload["message"].get("content", "")).strip()
    else:
        content = str(payload.get("response", "")).strip()

    if not content:
        return ""

    return content


def _extract_json_block(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        fence_end = stripped.find("\n")
        if fence_end != -1:
            inner = stripped[fence_end + 1 :]
            fence_close = inner.rfind("```")
            if fence_close != -1:
                return inner[:fence_close].strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        return stripped[start : end + 1]

    return ""


def _parse_ocr_content(content: str) -> dict:
    if not content:
        return {"text": "", "tables": [], "images": []}

    parsed = None
    json_block = _extract_json_block(content)
    if json_block:
        try:
            parsed = json.loads(json_block)
        except json.JSONDecodeError:
            parsed = None

    if isinstance(parsed, dict):
        text = parsed.get("text") or ""
        tables = parsed.get("tables") or []
        images = parsed.get("images") or []
        if not isinstance(text, str):
            text = str(text)
        if not isinstance(tables, list):
            tables = []
        if not isinstance(images, list):
            images = []
        return {"text": text.strip(), "tables": tables, "images": images}

    # Minimal fallback: if the model tried to output JSON but it's truncated/invalid,
    # extract the "text" field so clients don't display raw JSON.
    stripped = content.strip()
    if stripped.startswith("{") and '"text"' in stripped:
        match = re.search(
            r'"text"\s*:\s*"(.*?)"\s*(,\s*"tables"\s*:|\})', stripped, re.DOTALL
        )
        if match:
            return {"text": match.group(1).strip(), "tables": [], "images": []}

    return {"text": stripped, "tables": [], "images": []}


async def run_ocr(state: DocumentState) -> DocumentState:
    page_images_b64 = state.get("page_images_b64", [])
    if not page_images_b64:
        return {"ocr_pages": [], "ocr_text": ""}

    system_prompt = get_vlm_ocr_system_prompt()
    user_prompt = state.get("prompt") or "Extract the content of this page."

    page_images_b64 = page_images_b64[:3]
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
            content = _extract_ollama_content(response_payload)
            result = _parse_ocr_content(content)
            page_results.append(result)
        print(f"Completed OCR for page document ({page_index} pages)")

    return {"ocr_pages": page_results}
