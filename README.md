# Misión de prompting — el prompt mínimo

Repo propio (separado del repo de la materia `talksmith-ing`) para la misión
**"El prompt mínimo"**: una interfaz de chat sobre OpenRouter que sirve 4
modelos, usada para resolver el Juego de la Vida de Conway en la mínima
cantidad de prompts posible, con contabilidad completa de tokens y costo.

La consigna completa está en `talksmith-ing/missions/prompting/mission.md`
(no se copia acá porque es material de la cátedra, se referencia).

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # pegar ahí OPENROUTER_API_KEY
```

## Uso

```bash
cd src
python3 chat_cli.py
```

Elegí un slot (1-4), chateá, `/modelo` para cambiar de modelo (cierra la
conversación actual y abre una nueva con su propio log en `logs/`), `/salir`
para terminar.

Para reproducir el Ejercicio 2 (generación de `vida.py`) de forma
scripteada y auditable: `python3 src/run_ejercicio2.py`.

Para correr los tests de la cátedra contra el `vida.py` entregado:

```bash
python3 tests/test_vida.py vida.py
```

## Trabajo previo obligatorio (antes de escribir código)

### 1. ¿Qué es un router de modelos y qué problema resuelve?

Un **model router** (el `openrouter/auto` de OpenRouter) es un modelo virtual
que, en vez de responder él mismo, **elige a qué modelo real de qué
proveedor mandar cada request**, según qué modelo respondió mejor tareas
parecidas en el mercado de OpenRouter durante los últimos 7 días. El
problema que resuelve: nadie tiene que decidir a mano "esto es una tarea de
código, mando a Claude" / "esto es barato, mando a DeepSeek" — el router
externaliza esa decisión y además da resiliencia (fallback automático a
otro proveedor si el elegido está caído o saturado), sin cambiar una línea
de código del lado del cliente (siempre es el mismo endpoint, cambia solo
el `model: "openrouter/auto"`).

*(Nota metodológica: la ficha pública de `openrouter/auto` no expone en su
HTML estático el mecanismo interno de selección más allá de lo que ya
describe `mission.md`; el fetch directo a la página no devolvió más detalle
que el que ya está citado acá.)*

### 2. Mapa de modelos — el más avanzado de cada proveedor

Datos obtenidos de `GET https://openrouter.ai/api/v1/models` (catálogo real,
consultado 2026-09-18). Criterio de "más avanzado": el modelo no-batch más
caro y más reciente (`created`) del proveedor — proxy razonable cuando no
hay acceso directo al gráfico de benchmarks (que la web renderiza como
canvas/JS, no extraíble por fetch de texto).

| Proveedor | Modelo elegido | Precio in / out (por 1M tok) | Contexto | Benchmark |
|---|---|---|---|---|
| OpenAI | `openai/gpt-5.5-pro` | $30.00 / $180.00 | 1.05M | No accesible vía fetch estático; ficha visual en openrouter.ai/openai/gpt-5.5-pro |
| Anthropic | `anthropic/claude-fable-5.1` | $10.00 / $50.00 | 1.0M | ídem — ficha visual |
| Grok (x-ai) | `x-ai/grok-4.6` | $2.00 / $6.00 | 500K | ídem |
| Gemini (google) | `google/gemini-3.1-pro-preview` | $2.00 / $12.00 | 1.05M | ídem |
| DeepSeek | `deepseek/deepseek-v4-pro-0813` | $0.578 / $1.734 | 1.05M | ídem |
| Qwen | `qwen/qwen3.8-max-0902` | $2.00 / $6.00 | 1.0M | ídem |
| Kimi (moonshotai) | `moonshotai/kimi-k3` | $2.10 / $10.95 | 1.05M | ídem |

**Hallazgo:** la posición en benchmarks que muestra `openrouter.ai/discover`
se renderiza como gráfico interactivo (JS), no como texto/HTML plano, así
que no es extraíble con un fetch de solo-lectura. Para completarlo hay que
abrir la página en un navegador y leerlo a ojo — quedó pendiente de
verificación manual, documentado acá como limitación conocida en vez de
inventar un número.

### 3. Comparación de `supported_parameters` entre proveedores

De los 4 modelos del Ejercicio 1 (mismo `GET /api/v1/models`):

| Modelo | `supported_parameters` relevantes |
|---|---|
| `openai/gpt-5.6-luna` | `reasoning`, `reasoning_effort`, `include_reasoning`, `response_format`, `structured_outputs`, `tools`, `tool_choice`, `seed`, `max_completion_tokens` — **no** tiene `temperature`/`top_p`/`top_k` |
| `anthropic/claude-haiku-4.5` | `reasoning`, `include_reasoning`, `response_format`, `structured_outputs`, `temperature`, `top_p`, `top_k`, `tools` — **no** tiene `reasoning_effort` (Anthropic usa `reasoning.max_tokens`, no niveles) |
| `google/gemini-3.7-flash` | `reasoning`, `reasoning_effort`, `include_reasoning`, `response_format`, `structured_outputs`, `temperature`, `top_p`, `tools` |
| `deepseek/deepseek-v4-flash-0731` | superset: además de lo anterior, `frequency_penalty`, `presence_penalty`, `repetition_penalty`, `logit_bias`, `logprobs`, `top_logprobs`, `min_p`, `top_a`, `parallel_tool_calls` |

**Conclusión:** los 4 aceptan `reasoning` + `response_format`/
`structured_outputs` (por eso el diseño de slots de esta misión funciona en
los 4), pero **solo OpenAI y Gemini exponen `reasoning_effort` como nivel
discreto**; Anthropic controla el presupuesto de pensamiento con
`reasoning.max_tokens` en lugar de un enum. DeepSeek es, de los cuatro, el
que más parámetros de sampling clásico soporta (penalties, logprobs,
top-k/top-a), coherente con ser el modelo "de motor" pensado para uso
programático barato.

### Verificación: los 4 IDs de la misión

Los 4 modelos de `mission.md` (verificados ahí al 2026-09-02) siguen
existiendo en el catálogo al 2026-09-18 — **no hizo falta sustituir
ninguno**.

## Estructura del repo

```
src/
  models.py              # registro de los 4 slots y su config especial
  openrouter_client.py   # cliente HTTP + parseo de usage
  conversation_logger.py # logs .md por conversación
  chat_cli.py            # interfaz de chat interactiva (Ejercicio 1)
  prompt_vida.py         # especificación (prompt) para generar vida.py
  run_ejercicio1_demo.py # genera los logs de prueba de los 4 modelos (Ejercicio 1)
  run_ejercicio2.py       # corre el Ejercicio 2 de forma scripteada/auditable
tests/
  test_vida.py           # test de la cátedra (sin modificar)
  test_chat_cli.py        # tests propios de la interfaz (mockeados, sin red)
logs/
  ejercicio1/            # un log .md por modelo probado
  ejercicio2/            # logs de los intentos (ganador + quemados)
reports/
  ejercicio3.md          # informe final de tokens/costos
vida.py                  # entregado tal cual salió del chat (no se edita a mano)
```
