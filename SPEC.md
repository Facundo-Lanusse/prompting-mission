# SPEC — interfaz de chat multi-modelo sobre OpenRouter

## Objetivo

Una interfaz de chat mínima (CLI) que sirva cuatro modelos de cuatro
proveedores vía OpenRouter, muestre el usage completo después de cada
respuesta y deje un log `.md` auditable por conversación, usable tanto de
forma interactiva como scripteada.

## Decisiones de diseño

| Decisión | Razón |
|---|---|
| CLI, no web | La auditoría se hace sobre texto plano; una UI agrega superficie sin agregar evidencia. |
| Sin SDK de proveedor | OpenRouter expone un endpoint compatible con el formato de OpenAI; `requests` alcanza y deja el body explícito y verificable. |
| Toda la lógica "qué parámetro va con qué modelo" en `ModelSlot` | Un único lugar donde vive la diferencia entre proveedores; ni la CLI ni el runner la repiten. |
| El runner scripteado reusa `Conversation` | El log de una corrida automatizada es idéntico al de una sesión tipeada a mano: una sola ruta de código produce toda la evidencia. |
| Log escrito en cada turno, no al cerrar | Si el proceso se corta a la mitad, la evidencia de lo ya ocurrido sobrevive. |
| Cambiar de modelo siempre abre conversación nueva | Evita historial cruzado entre modelos, que haría ambigua la contabilidad de tokens por modelo. |

## Componentes

### `src/models.py`

Registro de los 4 slots (`ModelSlot`, dataclass inmutable), cada uno con su
`model_id` y su capacidad:

| Slot | Modelo | Capacidad | Cómo se implementa |
|---|---|---|---|
| 1 | `openai/gpt-5.6-luna` | reasoning effort configurable | `reasoning: {"effort": <nivel>}`, nivel elegido en la CLI |
| 2 | `anthropic/claude-haiku-4.5` | prompt caching explícito | system message como content block con `cache_control: {"type": "ephemeral"}` |
| 3 | `google/gemini-3.7-flash` | salidas estructuradas | `response_format: {"type": "json_schema", ...}`, `strict: true` |
| 4 | `deepseek/deepseek-v4-flash-0731` | escalón barato + reasoning | `reasoning: {"enabled": true}`; caching automático por prefijo estático repetido |

`ModelSlot.build_request(messages, reasoning_effort, static_context)` arma el
body del request según esas reglas y es la única función con lógica
específica por proveedor.

### `src/openrouter_client.py`

- `OpenRouterClient.chat_completion(body)`: `POST` a
  `https://openrouter.ai/api/v1/chat/completions`; cualquier respuesta que no
  sea 200 levanta `OpenRouterError` con el cuerpo del error.
- `parse_usage(response) -> Usage`: extrae `prompt_tokens`,
  `completion_tokens`, `prompt_tokens_details.cached_tokens`,
  `completion_tokens_details.reasoning_tokens`, `cost` y `cache_discount`.
  No hace falta ningún parámetro extra en el request: OpenRouter incluye el
  usage en cada respuesta.
- Detección de **razonamiento no declarado**: si el mensaje trae un bloque
  `reasoning`/`reasoning_content` pero `reasoning_tokens` es 0, el `Usage`
  queda marcado. Es un chequeo automático, no una inspección manual.
- `extract_reply_text(response)`: normaliza el contenido de la respuesta,
  que puede venir como string o como lista de bloques.

### `src/conversation_logger.py`

Un archivo `.md` por conversación, nombrado con slot, modelo, etiqueta y
timestamp UTC. Contiene un encabezado `## rol — timestamp` por turno, la
línea de usage debajo de cada respuesta del asistente y, si hubo contexto
estático, una constancia de su tamaño en caracteres (sin repetirlo en cada
turno). Se vuelca a disco en cada turno.

### `src/chat_cli.py`

- `Conversation`: agrupa modelo, historial y logger. `send(texto)` manda el
  historial completo —la API es stateless— con el `static_context`
  antepuesto si corresponde, y devuelve `(respuesta, usage)`.
- Loop interactivo: elegir slot → si aplica, elegir effort o cargar un
  contexto estático desde un archivo → chatear. `/modelo` cierra la
  conversación (flush del log) y abre una nueva; `/salir` termina.

### `src/prompt_vida.py` y `src/run_ejercicio2.py`

El prompt de generación de `vida.py` vive separado del código de la CLI para
que la parte estática (rol, contrato, restricciones, ejemplos) sea
literalmente el mismo texto en todas las corridas, condición necesaria para
el caching por prefijo. `pedido_final()` concentra la única parte variable.

`run_ejercicio2.py` manda el prompt a través de `Conversation`, extrae el
bloque de código de la respuesta (recorta los fences de Markdown, sin tocar
la lógica), lo escribe en `vida.py` y ejecuta los tests de aceptación como
subproceso, reportando el resultado en la misma corrida.

## Fuera de alcance

- Sin persistencia de conversaciones entre ejecuciones del proceso: cada
  arranque empieza de cero y los logs en disco son la persistencia.
- Sin streaming: respuestas completas, una por request.
- Sin UI web ni framework.
- Sin reintentos automáticos ante error de red: el error se reporta y el
  turno se puede repetir a mano, para que ningún request quede fuera del log.
