"""Genera los logs de prueba del Ejercicio 1: un log por modelo, mas la
evidencia de 1.5 (efecto del reasoning effort en slot 1) y 1.6 (cache hit
en slot 2). Scripteado para que sea reproducible, pero usa exactamente el
mismo camino de codigo (`Conversation`) que usaria alguien tipeando en
`chat_cli.py` a mano.

Uso: python3 src/run_ejercicio1_demo.py
"""
from __future__ import annotations

import uuid
from pathlib import Path

from dotenv import load_dotenv

from chat_cli import Conversation, REPO_ROOT
from models import get_slot
from openrouter_client import OpenRouterClient

MISSION_DIR = REPO_ROOT.parent / "talksmith-ing" / "missions" / "prompting"


def contexto_mision() -> str:
    mission = (MISSION_DIR / "mission.md").read_text(encoding="utf-8")
    rubric = (MISSION_DIR / "rubric.md").read_text(encoding="utf-8")
    # nonce unico por corrida: garantiza que el primer turno sea un cache
    # miss real (prefijo nunca visto), y no un hit heredado de una corrida
    # anterior con el mismo texto todavia dentro del TTL de cache de Anthropic.
    nonce = uuid.uuid4().hex
    return (
        f"Documento de referencia (consigna de una materia universitaria). "
        f"Id de corrida: {nonce}. Vas a responder preguntas puntuales sobre "
        "este documento, citando partes concretas cuando corresponda.\n\n"
        "=== mission.md ===\n" + mission + "\n\n=== rubric.md ===\n" + rubric
    )


def demo_slot1_effort(client: OpenRouterClient) -> None:
    pregunta = (
        "Sin usar la libreria estandar `itertools`, explicá en un parrafo "
        "corto por qué calcular todas las permutaciones de una lista de 12 "
        "elementos a mano, sin memoizacion, es computacionalmente costoso. "
        "Dá el numero exacto de permutaciones."
    )
    slot1 = get_slot(1)
    for nivel in ("low", "high"):
        print(f"\n--- Slot 1, effort={nivel} ---")
        conv = Conversation(
            client, slot1, log_subdir="ejercicio1", etiqueta=f"effort-{nivel}",
            reasoning_effort=nivel,
        )
        _, usage = conv.send(pregunta)
        print(f"[usage] {usage.as_markdown_line()}")
        conv.close()


def demo_slot2_cache(client: OpenRouterClient) -> None:
    slot2 = get_slot(2)
    static_ctx = contexto_mision()
    print("\n--- Slot 2, caching explicito (2 turnos, mismo contexto estatico) ---")
    conv = Conversation(
        client, slot2, log_subdir="ejercicio1", etiqueta="cache-demo",
        static_context=static_ctx,
    )
    _, usage1 = conv.send(
        "En una linea: ¿cuántos puntos vale en total el Ejercicio 2 segun la rubrica?"
    )
    print(f"[usage turno 1 - escritura de cache esperada] {usage1.as_markdown_line()}")
    _, usage2 = conv.send(
        "En una linea: ¿qué pasa si el vida.py entregado no coincide con el del log ganador?"
    )
    print(f"[usage turno 2 - cache hit esperado] {usage2.as_markdown_line()}")
    conv.close()


def demo_slot3_structured(client: OpenRouterClient) -> None:
    slot3 = get_slot(3)
    print("\n--- Slot 3, salida estructurada (JSON Schema) ---")
    conv = Conversation(client, slot3, log_subdir="ejercicio1", etiqueta="structured")
    reply, usage = conv.send(
        "¿Cuál es la capital de Francia? Respondé usando el schema JSON provisto."
    )
    print(f"[reply] {reply}")
    print(f"[usage] {usage.as_markdown_line()}")
    conv.close()


def demo_slot4_simple(client: OpenRouterClient) -> None:
    slot4 = get_slot(4)
    print("\n--- Slot 4, chat simple (tier barato) ---")
    conv = Conversation(client, slot4, log_subdir="ejercicio1", etiqueta="prueba")
    reply, usage = conv.send(
        "En una linea: ¿por qué conviene mandar tareas simples a un modelo barato "
        "en vez de a uno caro?"
    )
    print(f"[reply] {reply}")
    print(f"[usage] {usage.as_markdown_line()}")
    conv.close()


def main() -> None:
    load_dotenv(REPO_ROOT / ".env")
    client = OpenRouterClient()
    demo_slot1_effort(client)
    demo_slot2_cache(client)
    demo_slot3_structured(client)
    demo_slot4_simple(client)


if __name__ == "__main__":
    main()
