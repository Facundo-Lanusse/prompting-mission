"""Logger de conversaciones a Markdown.

Cada conversacion (= una sesion con un modelo, hasta que se cambia de modelo
o se cierra) queda en su propio archivo .md, con rol, mensaje y usage por
respuesta. Es la evidencia de auditoria de la entrega: una corrida sin log
no se puede verificar.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from openrouter_client import Usage


class ConversationLogger:
    def __init__(self, directory: Path, slot: int, model_id: str, etiqueta: str = ""):
        directory.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        sufijo = f"_{etiqueta}" if etiqueta else ""
        nombre = f"slot{slot}_{model_id.replace('/', '-')}{sufijo}_{ts}.md"
        self.path = directory / nombre
        self._lineas: list[str] = [
            f"# Conversacion — slot {slot} — `{model_id}`",
            "",
            f"Inicio (UTC): {datetime.now(timezone.utc).isoformat()}",
            "",
        ]
        self._flush()

    def log_static_context(self, texto: str) -> None:
        """Deja constancia del contexto estatico (system prompt) que se
        antepuso a cada request, sin repetirlo en cada turno."""
        self._lineas.append(f"## contexto estático (system, {len(texto)} caracteres)")
        self._lineas.append("")
        self._lineas.append("<details><summary>ver contenido</summary>")
        self._lineas.append("")
        self._lineas.append("```")
        self._lineas.append(texto)
        self._lineas.append("```")
        self._lineas.append("")
        self._lineas.append("</details>")
        self._lineas.append("")
        self._flush()

    def log_turn(self, role: str, content: str, usage: Optional[Usage] = None) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        self._lineas.append(f"## {role} — {ts}")
        self._lineas.append("")
        self._lineas.append(content)
        self._lineas.append("")
        if usage is not None:
            self._lineas.append(f"**usage:** {usage.as_markdown_line()}")
            self._lineas.append("")
        self._flush()

    def close(self) -> Path:
        self._lineas.append(f"Fin (UTC): {datetime.now(timezone.utc).isoformat()}")
        self._flush()
        return self.path

    def _flush(self) -> None:
        self.path.write_text("\n".join(self._lineas), encoding="utf-8")
