# SPEC — interfaz de chat sobre OpenRouter

## Objetivo

Interfaz de chat mínima (CLI) que sirve 4 modelos vía OpenRouter, muestra el
usage completo después de cada respuesta, y guarda un log `.md` auditable
por conversación. No se evalúa la estética (lo dice `mission.md`
explícitamente).

## Componentes

### `src/models.py`
Registro de los 4 slots (`ModelSlot`), cada uno con su `model_id` y su
capacidad especial:

| Slot | Modelo | Capacidad | Cómo se implementa |
|---|---|---|---|
| 1 | `openai/gpt-5.6-luna` | reasoning effort configurable | body `reasoning: {"effort": <nivel>}`, nivel elegido por el usuario en la CLI |
| 2 | `anthropic/claude-haiku-4.5` | prompt caching explícito | system message como content block con `cache_control: {"type": "ephemeral"}` |
| 3 | `google/gemini-3.7-flash` | salidas estructuradas | `response_format: {"type": "json_schema", ...}` |
| 4 | `deepseek/deepseek-v4-flash-0731` | tier barato + reasoning | `reasoning: {"enabled": true}`; caching automático por prefijo estático repetido |

`ModelSlot.build_request()` arma el body del request según estas reglas;
es la única función con lógica de "qué parámetro va con qué modelo", para
no repetirla en la CLI ni en el runner del Ejercicio 2.

### `src/openrouter_client.py`
- `OpenRouterClient.chat_completion(body)`: `POST` a
  `https://openrouter.ai/api/v1/chat/completions`, error si no es 200.
- `parse_usage(response) -> Usage`: extrae `prompt_tokens`,
  `completion_tokens`, `prompt_tokens_details.cached_tokens`,
  `completion_tokens_details.reasoning_tokens`, `cost`, `cache_discount`.
  También detecta el caso "el modelo razonó (trae `reasoning`/
  `reasoning_content` en el mensaje) pero no declaró `reasoning_tokens`" —
  el hallazgo que pide documentar el Ejercicio 3.
- No requiere ningún parámetro extra para pedir el usage: OpenRouter lo
  incluye siempre (confirmado en `mission.md`).

### `src/conversation_logger.py`
Un archivo `.md` por conversación (nombre con slot, modelo y timestamp
UTC), con un `## rol — timestamp` por turno y la línea de usage debajo de
cada respuesta del asistente. Se reescribe a disco en cada turno (no solo
al cerrar), para no perder evidencia si el proceso se corta a mitad.

### `src/chat_cli.py`
- `Conversation`: agrupa modelo + historial + logger. `send(texto)` manda
  el turno completo (con el `static_context` si corresponde) y devuelve
  `(respuesta, usage)`.
- Loop interactivo: elegir slot → (si aplica) elegir effort / cargar
  contexto estático → chatear. `/modelo` cierra la conversación actual
  (flush del log) y abre una nueva. `/salir` termina.
- **Cambiar de modelo siempre inicia una conversación nueva** (nuevo
  `Conversation`, nuevo log): no hay opción de mantener historial cruzado
  entre modelos.

### `src/prompt_vida.py` + `src/run_ejercicio2.py`
El prompt de generación de `vida.py` vive separado del código de la CLI
para que la parte estática (rol, contrato, restricciones, ejemplos) sea
literalmente el mismo texto en todos los intentos — requisito de caching
del Ejercicio 2. `run_ejercicio2.py` reusa `Conversation` (el mismo camino
que usaría un humano tipeando en `chat_cli.py`) para que el log quede
generado por el mismo código que audita la cátedra.

## Fuera de alcance

- No hay persistencia de conversaciones entre corridas del proceso (cada
  ejecución de `chat_cli.py` empieza de cero); los logs en disco son la
  persistencia.
- No hay manejo de streaming — respuestas completas, una por request.
- No hay UI web ni framework: es intencionalmente una CLI (decisión
  tomada porque la consigna no exige estética y la CLI es más simple de
  auditar en logs de texto plano).
