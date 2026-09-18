"""Tests propios de la interfaz de chat (Ejercicio 1). Mockean la llamada
HTTP: no pegan a la red real ni gastan API key.

Uso: python3 -m unittest tests/test_chat_cli.py -v  (desde la raiz del repo)
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from conversation_logger import ConversationLogger  # noqa: E402
from models import get_slot  # noqa: E402
from openrouter_client import Usage, extract_reply_text, parse_usage  # noqa: E402


class TestModelSlots(unittest.TestCase):
    def test_slot1_agrega_reasoning_effort(self):
        slot = get_slot(1)
        body = slot.build_request([{"role": "user", "content": "hola"}], reasoning_effort="high")
        self.assertEqual(body["reasoning"], {"effort": "high"})
        self.assertEqual(body["model"], "openai/gpt-5.6-luna")

    def test_slot2_usa_cache_control_explicito(self):
        slot = get_slot(2)
        body = slot.build_request(
            [{"role": "user", "content": "hola"}], static_context="contexto grande"
        )
        system = body["messages"][0]
        self.assertEqual(system["role"], "system")
        self.assertEqual(system["content"][0]["cache_control"], {"type": "ephemeral"})
        self.assertEqual(system["content"][0]["text"], "contexto grande")

    def test_slot3_pide_json_schema(self):
        slot = get_slot(3)
        body = slot.build_request([{"role": "user", "content": "hola"}])
        self.assertEqual(body["response_format"]["type"], "json_schema")

    def test_slot4_prefijo_estatico_identico_sin_cache_control(self):
        slot = get_slot(4)
        body = slot.build_request(
            [{"role": "user", "content": "hola"}],
            reasoning_effort="high",
            static_context="prefijo fijo",
        )
        system = body["messages"][0]
        self.assertEqual(system, {"role": "system", "content": "prefijo fijo"})
        self.assertEqual(body["reasoning"], {"enabled": True})

    def test_slot_invalido_lanza_error(self):
        with self.assertRaises(ValueError):
            get_slot(99)


class TestUsageParsing(unittest.TestCase):
    def _response(self, **usage_overrides):
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "prompt_tokens_details": {"cached_tokens": 0},
            "completion_tokens_details": {"reasoning_tokens": 0},
            "cost": 0.001,
        }
        usage.update(usage_overrides)
        return {
            "choices": [{"message": {"role": "assistant", "content": "respuesta"}}],
            "usage": usage,
        }

    def test_parse_usage_campos_basicos(self):
        usage = parse_usage(self._response())
        self.assertEqual(usage.prompt_tokens, 100)
        self.assertEqual(usage.completion_tokens, 50)
        self.assertEqual(usage.total_tokens, 150)
        self.assertFalse(usage.reasoning_sin_tokens_declarados)

    def test_parse_usage_detecta_cache_hit(self):
        resp = self._response(prompt_tokens_details={"cached_tokens": 80})
        usage = parse_usage(resp)
        self.assertEqual(usage.cached_tokens, 80)

    def test_parse_usage_detecta_razonamiento_sin_tokens_declarados(self):
        resp = self._response()
        resp["choices"][0]["message"]["reasoning"] = "pensando paso a paso..."
        usage = parse_usage(resp)
        self.assertTrue(usage.reasoning_sin_tokens_declarados)

    def test_parse_usage_no_marca_hallazgo_si_declara_tokens(self):
        resp = self._response(completion_tokens_details={"reasoning_tokens": 20})
        resp["choices"][0]["message"]["reasoning"] = "pensando..."
        usage = parse_usage(resp)
        self.assertFalse(usage.reasoning_sin_tokens_declarados)
        self.assertEqual(usage.reasoning_tokens, 20)

    def test_extract_reply_text_content_string(self):
        resp = self._response()
        self.assertEqual(extract_reply_text(resp), "respuesta")

    def test_extract_reply_text_content_lista_de_bloques(self):
        resp = self._response()
        resp["choices"][0]["message"]["content"] = [
            {"type": "text", "text": "hola "},
            {"type": "text", "text": "mundo"},
        ]
        self.assertEqual(extract_reply_text(resp), "hola mundo")


class TestConversationLogger(unittest.TestCase):
    def test_log_turn_escribe_rol_mensaje_y_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = ConversationLogger(Path(tmp), slot=4, model_id="deepseek/deepseek-v4-flash-0731")
            logger.log_turn("user", "Generá vida.py")
            logger.log_turn(
                "assistant", "```python\nprint('hola')\n```",
                usage=Usage(prompt_tokens=10, completion_tokens=5, cost=0.0001),
            )
            path = logger.close()

            texto = path.read_text(encoding="utf-8")
            self.assertIn("## user", texto)
            self.assertIn("Generá vida.py", texto)
            self.assertIn("## assistant", texto)
            self.assertIn("in=10", texto)
            self.assertIn("out=5", texto)

    def test_nombre_de_archivo_incluye_slot_y_modelo(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = ConversationLogger(Path(tmp), slot=2, model_id="anthropic/claude-haiku-4.5")
            self.assertIn("slot2", logger.path.name)
            self.assertIn("anthropic-claude-haiku-4.5", logger.path.name)


class TestConversationSend(unittest.TestCase):
    def test_send_registra_turnos_y_devuelve_usage(self):
        from chat_cli import Conversation

        fake_client = MagicMock()
        fake_client.chat_completion.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "hola humano"}}],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 10,
                "prompt_tokens_details": {"cached_tokens": 0},
                "completion_tokens_details": {"reasoning_tokens": 0},
                "cost": 0.0005,
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            import chat_cli

            original_logs_dir = chat_cli.LOGS_DIR
            chat_cli.LOGS_DIR = Path(tmp)
            try:
                conv = Conversation(fake_client, get_slot(1), reasoning_effort="low")
                reply, usage = conv.send("hola modelo")
                self.assertEqual(reply, "hola humano")
                self.assertEqual(usage.prompt_tokens, 20)
                self.assertEqual(len(conv.messages), 2)
                self.assertEqual(conv.messages[0], {"role": "user", "content": "hola modelo"})
                conv.close()
            finally:
                chat_cli.LOGS_DIR = original_logs_dir


if __name__ == "__main__":
    unittest.main(verbosity=2)
