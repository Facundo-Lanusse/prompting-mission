"""Interfaz de chat CLI multi-modelo sobre OpenRouter.

Sirve los 4 modelos de `models.py`, muestra el usage despues de cada
respuesta y guarda un log .md por conversacion. Cambiar de modelo cierra
la conversacion actual y arranca una nueva (con su propio log).

Uso interactivo:
    python3 src/chat_cli.py

Comandos dentro del chat:
    /modelo     -> elegir otro slot (cierra la conversacion actual)
    /salir      -> terminar
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from conversation_logger import ConversationLogger
from models import ModelSlot, get_slot
from openrouter_client import (
    OpenRouterClient,
    OpenRouterError,
    Usage,
    extract_reply_text,
    parse_usage,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = REPO_ROOT / "logs"


class Conversation:
    """Una conversacion con un slot fijo, desde que arranca hasta que se cierra."""

    def __init__(
        self,
        client: OpenRouterClient,
        slot: ModelSlot,
        log_subdir: str = "ejercicio1",
        etiqueta: str = "",
        reasoning_effort: Optional[str] = None,
        static_context: Optional[str] = None,
    ):
        self.client = client
        self.slot = slot
        self.reasoning_effort = reasoning_effort
        self.static_context = static_context
        self.messages: list[dict] = []
        self.usages: list[Usage] = []
        self.logger = ConversationLogger(
            LOGS_DIR / log_subdir, slot.slot, slot.model_id, etiqueta=etiqueta
        )
        if static_context:
            self.logger.log_static_context(static_context)

    def send(self, user_text: str) -> tuple[str, Usage]:
        self.logger.log_turn("user", user_text)
        self.messages.append({"role": "user", "content": user_text})

        # El static_context se antepone en CADA request (la API es stateless:
        # reenviamos el historial completo). El cache hit lo da el proveedor
        # al reconocer ese mismo prefijo repetido entre llamadas.
        body = self.slot.build_request(
            self.messages,
            reasoning_effort=self.reasoning_effort,
            static_context=self.static_context,
        )

        response = self.client.chat_completion(body)
        reply = extract_reply_text(response)
        usage = parse_usage(response)

        self.messages.append({"role": "assistant", "content": reply})
        self.logger.log_turn("assistant", reply, usage=usage)
        self.usages.append(usage)
        return reply, usage

    def close(self) -> Path:
        return self.logger.close()


def _elegir_slot() -> ModelSlot:
    print("\nModelos disponibles:")
    for n, slot in ((1, get_slot(1)), (2, get_slot(2)), (3, get_slot(3)), (4, get_slot(4))):
        print(f"  {n}. {slot.model_id} ({slot.provider}) — {slot.capacidad}")
    while True:
        raw = input("Elegi un slot [1-4]: ").strip()
        if raw in {"1", "2", "3", "4"}:
            return get_slot(int(raw))
        print("Opcion invalida.")


def _armar_conversacion(client: OpenRouterClient) -> Conversation:
    slot = _elegir_slot()
    reasoning_effort = None
    if slot.reasoning_configurable:
        reasoning_effort = input(
            "Nivel de reasoning effort [low/medium/high] (enter = medium): "
        ).strip() or "medium"

    static_context = None
    if slot.explicit_caching or slot.model_id.startswith("deepseek/"):
        usar = input(
            "¿Cargar un contexto estatico grande para caching? [y/N]: "
        ).strip().lower()
        if usar == "y":
            ruta = input("Ruta al archivo de contexto estatico: ").strip()
            static_context = Path(ruta).read_text(encoding="utf-8")

    return Conversation(client, slot, reasoning_effort=reasoning_effort, static_context=static_context)


def main() -> None:
    load_dotenv(REPO_ROOT / ".env")
    try:
        client = OpenRouterClient()
    except OpenRouterError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    conversation = _armar_conversacion(client)
    print(f"\nChateando con slot {conversation.slot.slot} ({conversation.slot.model_id}).")
    print("Comandos: /modelo para cambiar, /salir para terminar.\n")

    while True:
        user_text = input("vos> ").strip()
        if not user_text:
            continue
        if user_text == "/salir":
            conversation.close()
            print("Listo. Log guardado.")
            break
        if user_text == "/modelo":
            conversation.close()
            print("Conversacion cerrada. Log guardado.")
            conversation = _armar_conversacion(client)
            print(f"\nChateando con slot {conversation.slot.slot} ({conversation.slot.model_id}).\n")
            continue

        try:
            reply, usage = conversation.send(user_text)
        except OpenRouterError as exc:
            print(f"[error] {exc}")
            continue

        print(f"\n{conversation.slot.model_id}> {reply}\n")
        print(f"[usage] {usage.as_markdown_line()}\n")


if __name__ == "__main__":
    main()
