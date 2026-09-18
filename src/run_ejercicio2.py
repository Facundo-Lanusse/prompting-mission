"""Ejercicio 2, scripteado y auditable: genera vida.py via el slot 4.

Reglas de mission.md que este script respeta:
  - Correcto en 1 prompt, a lo sumo 2 (el 2do solo para pulir).
  - Si se pasa de 2, la corrida queda "quemada": conversacion nueva, prompt
    reescrito desde cero (nunca se parchea el codigo a mano).
  - El contexto estatico (CONTEXTO_ESTATICO) es identico en todos los
    intentos, para que el caching de DeepSeek funcione entre corridas.
  - Reasoning activado en el slot 4.

Uso: python3 src/run_ejercicio2.py [--max-intentos N]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

from chat_cli import Conversation, REPO_ROOT
from models import get_slot
from openrouter_client import OpenRouterClient, OpenRouterError
from prompt_vida import CONTEXTO_ESTATICO, pedido_final

VIDA_PY = REPO_ROOT / "vida.py"
TEST_VIDA = REPO_ROOT / "tests" / "test_vida.py"
CANDIDATO = REPO_ROOT / "logs" / "ejercicio2" / "_candidato_vida.py"

FENCE_RE = re.compile(r"^```[a-zA-Z]*\n|\n```$", re.MULTILINE)


def limpiar_codigo(texto: str) -> str:
    texto = texto.strip()
    texto = FENCE_RE.sub("", texto)
    return texto.strip() + "\n"


def correr_tests(script_path: Path) -> tuple[bool, str]:
    r = subprocess.run(
        [sys.executable, str(TEST_VIDA), str(script_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    salida = r.stdout + r.stderr
    ok = r.returncode == 0
    return ok, salida


def resumen_fallas(salida: str) -> str:
    lineas = [
        l for l in salida.splitlines()
        if l.startswith("FAIL:") or l.startswith("ERROR:") or "AssertionError" in l
    ]
    return "\n".join(lineas[:30]) or salida[-2000:]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-intentos", type=int, default=4)
    args = parser.parse_args()

    load_dotenv(REPO_ROOT / ".env")
    client = OpenRouterClient()
    slot = get_slot(4)

    for intento in range(1, args.max_intentos + 1):
        print(f"\n=== Intento {intento} (conversacion nueva) ===")
        conv = Conversation(
            client,
            slot,
            log_subdir="ejercicio2",
            etiqueta=f"intento{intento}",
            reasoning_effort="high",
            static_context=CONTEXTO_ESTATICO,
        )

        prompt1 = pedido_final(intento)
        reply, usage = conv.send(prompt1)
        print(f"[prompt 1] {usage.as_markdown_line()}")

        codigo = limpiar_codigo(reply)
        CANDIDATO.write_text(codigo, encoding="utf-8")
        ok, salida = correr_tests(CANDIDATO)

        n_prompts = 1
        if not ok:
            print("Fallaron tests, mando 1 prompt de pulido (segundo y ultimo permitido)...")
            fallas = resumen_fallas(salida)
            prompt2 = (
                "Los tests automatizados fallaron contra este código. Corregí el "
                "archivo completo (no un parche, el archivo entero) respetando "
                "exactamente la especificación del contrato de arriba. Fallas:\n\n"
                f"{fallas}\n\n"
                "Respondé solo con el contenido completo y corregido de `vida.py`, "
                "sin explicaciones ni markdown."
            )
            reply2, usage2 = conv.send(prompt2)
            print(f"[prompt 2 - pulido] {usage2.as_markdown_line()}")
            codigo = limpiar_codigo(reply2)
            CANDIDATO.write_text(codigo, encoding="utf-8")
            ok, salida = correr_tests(CANDIDATO)
            n_prompts = 2

        conv.close()

        if ok:
            VIDA_PY.write_text(codigo, encoding="utf-8")
            print(f"\n✅ Intento {intento} GANADOR con {n_prompts} prompt(s). "
                  f"vida.py escrito en {VIDA_PY}. Log: {conv.logger.path}")
            return

        print(f"\n🔥 Intento {intento} QUEMADO ({n_prompts} prompts, tests en rojo). "
              f"Log conservado: {conv.logger.path}")

    print("\n❌ Se agotaron los intentos sin pasar los 9 tests. Revisar logs en logs/ejercicio2/.")
    sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except OpenRouterError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
