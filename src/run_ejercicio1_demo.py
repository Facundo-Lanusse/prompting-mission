"""Genera los logs de prueba de la etapa 1: un log por modelo, mas la
evidencia del efecto del reasoning effort (slot 1) y del cache hit
explicito (slot 2). Scripteado para que sea reproducible, pero usa
exactamente el mismo camino de codigo (`Conversation`) que usaria alguien
tipeando en `chat_cli.py` a mano.

Uso: python3 src/run_ejercicio1_demo.py [--contexto <ruta> ...]
"""
from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

from chat_cli import Conversation, REPO_ROOT
from models import get_slot
from openrouter_client import OpenRouterClient

# Documentos usados como contexto estatico en la demo de caching del slot 2.
# Cualquier archivo de texto sirve; lo unico que importa para el cache hit es
# que sea el mismo texto en los dos turnos y lo bastante largo (>= ~1024
# tokens, ~4000 caracteres) para que el proveedor lo cachee.
CONTEXTO_POR_DEFECTO = sorted(
    (REPO_ROOT.parent / "talksmith-ing" / "missions" / "prompting").glob("*.md")
)


def contexto_estatico(rutas: list[Path]) -> str:
    # nonce unico por corrida: garantiza que el primer turno sea un cache
    # miss real (prefijo nunca visto), y no un hit heredado de una corrida
    # anterior con el mismo texto todavia dentro del TTL de cache de Anthropic.
    nonce = uuid.uuid4().hex
    partes = [
        f"Documento de referencia. Id de corrida: {nonce}. Vas a responder "
        "preguntas puntuales sobre este documento, citando partes concretas "
        "cuando corresponda."
    ]
    for ruta in rutas:
        partes.append(f"=== {ruta.name} ===\n" + ruta.read_text(encoding="utf-8"))
    return "\n\n".join(partes)


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


def demo_slot2_cache(client: OpenRouterClient, rutas: list[Path]) -> None:
    slot2 = get_slot(2)
    static_ctx = contexto_estatico(rutas)
    print("\n--- Slot 2, caching explicito (2 turnos, mismo contexto estatico) ---")
    print(f"    contexto: {len(static_ctx)} caracteres de {len(rutas)} archivo(s)")
    conv = Conversation(
        client, slot2, log_subdir="ejercicio1", etiqueta="cache-demo",
        static_context=static_ctx,
    )
    _, usage1 = conv.send(
        "En una linea: ¿cuál es el objetivo principal del documento de referencia?"
    )
    print(f"[usage turno 1 - escritura de cache esperada] {usage1.as_markdown_line()}")
    _, usage2 = conv.send(
        "En una linea: ¿qué requisito del documento te parece el mas dificil de cumplir?"
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contexto",
        type=Path,
        nargs="+",
        default=CONTEXTO_POR_DEFECTO,
        help="Archivo(s) de texto a usar como contexto estatico en la demo de "
             "caching del slot 2 (cuanto mas largo, mas probable el cache hit).",
    )
    args = parser.parse_args()

    faltantes = [r for r in args.contexto if not r.is_file()]
    if not args.contexto or faltantes:
        print(
            "Error: hace falta al menos un archivo de contexto estatico para la "
            "demo de caching. Pasalo con --contexto <ruta> [<ruta> ...].",
            file=sys.stderr,
        )
        sys.exit(1)

    load_dotenv(REPO_ROOT / ".env")
    client = OpenRouterClient()
    demo_slot1_effort(client)
    demo_slot2_cache(client, list(args.contexto))
    demo_slot3_structured(client)
    demo_slot4_simple(client)


if __name__ == "__main__":
    main()
