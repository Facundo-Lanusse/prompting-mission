"""Registro de los 4 slots de modelos de la interfaz de chat.

Cada slot ejercita una capacidad distinta de la API:

    1. openai/gpt-5.6-luna         -> reasoning effort configurable
    2. anthropic/claude-haiku-4.5  -> prompt caching explicito (cache_control)
    3. google/gemini-3.7-flash     -> salidas estructuradas (JSON Schema)
    4. deepseek/deepseek-v4-flash-0731 -> escalon barato + reasoning

IDs verificados contra el catalogo de OpenRouter al 2026-09-18. Si alguno
deja de existir, reemplazarlo aca por el equivalente vigente del mismo
proveedor y anotarlo en reports/informe-de-consumo.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class ModelSlot:
    slot: int
    model_id: str
    provider: str
    capacidad: str
    reasoning_configurable: bool = False
    explicit_caching: bool = False
    structured_output: bool = False

    def build_request(
        self,
        messages: list[dict[str, Any]],
        *,
        reasoning_effort: Optional[str] = None,
        static_context: Optional[str] = None,
    ) -> dict[str, Any]:
        """Arma el body del request a /chat/completions para este slot.

        `messages` ya viene en formato OpenAI-like: [{"role": ..., "content": ...}, ...].
        `static_context` es el bloque de contexto/instrucciones estatico que va
        primero (para forzar cache hits); solo se usa en slots con caching
        (explicito en el 2, automatico por prefijo en el 4).
        """
        body: dict[str, Any] = {
            "model": self.model_id,
            "messages": self._build_messages(messages, static_context=static_context),
        }

        if self.reasoning_configurable and reasoning_effort:
            body["reasoning"] = {"effort": reasoning_effort}
        elif self.model_id.startswith("deepseek/") and reasoning_effort:
            # Slot 4: reasoning activado, sin nivel configurable.
            body["reasoning"] = {"enabled": True}

        if self.structured_output:
            body["response_format"] = _DEFAULT_JSON_SCHEMA

        return body

    def _build_messages(
        self, messages: list[dict[str, Any]], *, static_context: Optional[str]
    ) -> list[dict[str, Any]]:
        if not static_context:
            return messages

        if self.explicit_caching:
            # Anthropic: el bloque estatico va como content block con
            # cache_control ephemeral, para que OpenRouter lo pase al
            # proveedor y se registre el cache hit en turnos siguientes.
            system_msg = {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": static_context,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            }
            return [system_msg, *messages]

        # DeepSeek (y en general): caching automatico por prefijo repetido.
        # Alcanza con que el bloque estatico sea identico y vaya primero.
        system_msg = {"role": "system", "content": static_context}
        return [system_msg, *messages]


_DEFAULT_JSON_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "respuesta_estructurada",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "respuesta": {"type": "string"},
                "confianza": {
                    "type": "string",
                    "enum": ["baja", "media", "alta"],
                },
            },
            "required": ["respuesta", "confianza"],
            "additionalProperties": False,
        },
    },
}


SLOTS: dict[int, ModelSlot] = {
    1: ModelSlot(
        slot=1,
        model_id="openai/gpt-5.6-luna",
        provider="OpenAI",
        capacidad="Effort configurable (reasoning_effort)",
        reasoning_configurable=True,
    ),
    2: ModelSlot(
        slot=2,
        model_id="anthropic/claude-haiku-4.5",
        provider="Anthropic",
        capacidad="Prompt caching explicito (cache_control)",
        explicit_caching=True,
    ),
    3: ModelSlot(
        slot=3,
        model_id="google/gemini-3.7-flash",
        provider="Google",
        capacidad="Salidas estructuradas (JSON Schema)",
        structured_output=True,
    ),
    4: ModelSlot(
        slot=4,
        model_id="deepseek/deepseek-v4-flash-0731",
        provider="DeepSeek",
        capacidad="Escalon barato + reasoning",
    ),
}


def get_slot(slot_number: int) -> ModelSlot:
    try:
        return SLOTS[slot_number]
    except KeyError as exc:
        raise ValueError(f"Slot invalido: {slot_number}. Opciones: {sorted(SLOTS)}") from exc
