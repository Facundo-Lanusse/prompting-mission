"""Cliente minimo para el endpoint de chat completions de OpenRouter.

OpenRouter expone un endpoint compatible con el formato de OpenAI:
POST https://openrouter.ai/api/v1/chat/completions

El usage (tokens de entrada/salida/razonamiento/cacheados y costo) viene
incluido en cada respuesta sin pedir nada extra (mission.md, Ejercicio 1).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(RuntimeError):
    pass


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cached_tokens: int = 0
    cost: float = 0.0
    cache_discount: Optional[float] = None
    reasoning_sin_tokens_declarados: bool = False

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def as_markdown_line(self) -> str:
        partes = [
            f"in={self.prompt_tokens}",
            f"out={self.completion_tokens}",
            f"reasoning={self.reasoning_tokens}",
            f"cached={self.cached_tokens}",
            f"cost=${self.cost:.6f}",
        ]
        if self.cache_discount is not None:
            partes.append(f"cache_discount=${self.cache_discount:.6f}")
        if self.reasoning_sin_tokens_declarados:
            partes.append("⚠ razono sin declarar reasoning_tokens")
        return " · ".join(partes)


class OpenRouterClient:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 120):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise OpenRouterError(
                "Falta OPENROUTER_API_KEY. Copia .env.example a .env y pega tu key."
            )
        self.timeout = timeout

    def chat_completion(self, body: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(
            OPENROUTER_URL, headers=headers, json=body, timeout=self.timeout
        )
        if resp.status_code != 200:
            raise OpenRouterError(f"OpenRouter {resp.status_code}: {resp.text}")
        return resp.json()


def extract_reply_text(response: dict[str, Any]) -> str:
    choice = response["choices"][0]
    message = choice.get("message", {})
    content = message.get("content", "")
    if isinstance(content, list):
        # Algunos proveedores devuelven content como lista de bloques.
        return "".join(block.get("text", "") for block in content if isinstance(block, dict))
    return content or ""


def _tuvo_razonamiento(response: dict[str, Any]) -> bool:
    choice = response.get("choices", [{}])[0]
    message = choice.get("message", {})
    return bool(message.get("reasoning") or message.get("reasoning_content"))


def parse_usage(response: dict[str, Any]) -> Usage:
    usage = response.get("usage", {}) or {}
    prompt_details = usage.get("prompt_tokens_details", {}) or {}
    completion_details = usage.get("completion_tokens_details", {}) or {}

    reasoning_tokens = completion_details.get("reasoning_tokens", 0) or 0
    reasono = _tuvo_razonamiento(response)

    return Usage(
        prompt_tokens=usage.get("prompt_tokens", 0) or 0,
        completion_tokens=usage.get("completion_tokens", 0) or 0,
        reasoning_tokens=reasoning_tokens,
        cached_tokens=prompt_details.get("cached_tokens", 0) or 0,
        cost=usage.get("cost", 0.0) or 0.0,
        cache_discount=usage.get("cache_discount"),
        reasoning_sin_tokens_declarados=reasono and reasoning_tokens == 0,
    )
