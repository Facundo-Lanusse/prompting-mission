# El prompt mínimo — interfaz multi-modelo sobre OpenRouter

Interfaz de chat propia que sirve cuatro modelos de cuatro proveedores a
través de OpenRouter, con contabilidad completa de tokens (entrada, salida,
razonamiento, cacheados) y costo en dólares por respuesta, y log `.md`
auditable por conversación.

Con esa interfaz se resolvió un objetivo de programación —el Juego de la
Vida de Conway (`vida.py`)— en **un solo prompt**, con los 9 tests de
aceptación en verde y un gasto total de **$0.0085 USD** en esa etapa.

| Resultado | Valor |
|---|---|
| Prompts hasta el script correcto | 1 (sin intentos descartados) |
| Tests de aceptación de `vida.py` | 9/9 en verde |
| Tests propios de la interfaz | 14/14 en verde |
| Costo total reconstruido desde logs | $0.017343 USD |
| Cache hit medido (slot 2) | 5593 tokens, −89% de costo de entrada |

## Índice

- [Setup](#setup)
- [Uso](#uso)
- [Arquitectura](#arquitectura)
- [Etapa 1 — la interfaz de chat](#etapa-1--la-interfaz-de-chat)
- [Etapa 2 — generación de `vida.py`](#etapa-2--generación-de-vidapy)
- [Etapa 3 — informe de consumo](#etapa-3--informe-de-consumo)
- [Investigación previa](#investigación-previa)
- [Verificación y tests](#verificación-y-tests)
- [Estructura del repositorio](#estructura-del-repositorio)

## Setup

Requiere Python 3.9+ y una API key de OpenRouter con crédito.

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # pegar ahí OPENROUTER_API_KEY
```

Dependencias: `requests` (cliente HTTP) y `python-dotenv` (carga de la key).
Nada más: sin frameworks, sin SDK de proveedor.

## Uso

```bash
python3 src/chat_cli.py            # chat interactivo con los 4 modelos
python3 src/run_ejercicio1_demo.py --contexto <archivo>   # regenera los logs de prueba de los 4 modelos
python3 src/run_ejercicio2.py      # regenera vida.py de forma scripteada y auditable
```

Dentro del chat:

| Comando | Efecto |
|---|---|
| texto libre | manda el turno y muestra la respuesta + el usage |
| `/modelo` | cierra la conversación actual (con su log) y abre una nueva con otro slot |
| `/salir` | cierra la conversación y termina |

Después de cada respuesta la CLI imprime la línea de usage que se guarda
también en el log:

```
[usage] in=1147 · out=24848 · reasoning=24438 · cached=0 · cost=$0.004541
```

## Arquitectura

```
chat_cli.py ──── Conversation ──┬── ModelSlot.build_request()   (models.py)
  (interactivo)                 ├── OpenRouterClient            (openrouter_client.py)
run_ejercicio2.py ──────────────┴── ConversationLogger          (conversation_logger.py)
  (scripteado)                            │
                                          └── logs/*.md  (evidencia auditable)
```

Ambos caminos de entrada —la CLI interactiva y el runner scripteado— usan la
misma clase `Conversation`, así que el log de una corrida automatizada es
idéntico en forma y contenido al de una sesión tipeada a mano. El detalle
de diseño de cada módulo está en [`SPEC.md`](SPEC.md).

## Etapa 1 — la interfaz de chat

Cuatro slots, uno por proveedor, cada uno ejercitando una capacidad distinta
de la API:

| Slot | Modelo | Capacidad | Implementación |
|---|---|---|---|
| 1 | `openai/gpt-5.6-luna` | reasoning effort configurable | `reasoning: {"effort": low\|medium\|high}` |
| 2 | `anthropic/claude-haiku-4.5` | prompt caching explícito | system message con `cache_control: {"type": "ephemeral"}` |
| 3 | `google/gemini-3.7-flash` | salidas estructuradas | `response_format: {"type": "json_schema", ...}` con `strict` |
| 4 | `deepseek/deepseek-v4-flash-0731` | escalón barato + reasoning | `reasoning: {"enabled": true}`, caching automático por prefijo |

Evidencia en `logs/ejercicio1/` (un log por modelo). Dos mediciones
destacadas:

**Efecto del reasoning effort (slot 1).** Misma pregunta, dos niveles:

| Effort | in | out | reasoning | costo |
|---|---:|---:|---:|---:|
| `low` | 63 | 97 | 0 | $0.000129 |
| `high` | 63 | 140 | 60 | $0.000181 |

**Cache hit explícito (slot 2).** Mismo contexto estático (~17.200
caracteres) en dos turnos consecutivos:

| Turno | in | cached | costo |
|---|---:|---:|---:|
| 1 (escritura de cache) | 5627 | 0 | $0.007165 |
| 2 (lectura de cache) | 5688 | 5593 | $0.000899 |

El segundo turno cuesta un 87% menos que el primero pese a mandar más
tokens de entrada: 5593 de los 5688 se facturaron a tarifa de lectura de
cache.

## Etapa 2 — generación de `vida.py`

`vida.py` se generó con el slot 4 desde la propia interfaz y entró al
repositorio **tal cual salió del chat**, sin ediciones manuales. El prompt
vive en `src/prompt_vida.py`, partido en dos:

- `CONTEXTO_ESTATICO`: rol, contexto, instrucciones, restricciones y
  ejemplos few-shot. Idéntico byte a byte entre corridas, por diseño, para
  habilitar el caching automático por prefijo.
- `pedido_final()`: la única parte variable, al final del mensaje.

`run_ejercicio2.py` manda el prompt, extrae el código de la respuesta,
lo escribe en `vida.py` y corre los tests de aceptación contra él en el
mismo paso. Resultado: **correcto en el primer intento**, 9/9 tests, sin
corridas descartadas.

Log ganador:
`logs/ejercicio2/slot4_deepseek-deepseek-v4-flash-0731_intento1_20260918T180145Z.md`.
El `vida.py` de la raíz coincide con el código de ese log (verificado con
diff; la única diferencia son los fences ` ```python ` que el runner
recorta al extraer el bloque).

## Etapa 3 — informe de consumo

El informe completo —tokens por corrida, análisis de tokens de
razonamiento, ahorro por caching, gasto total contra el dashboard de la
cuenta y conclusiones— está en
[`reports/informe-de-consumo.md`](reports/informe-de-consumo.md). Todos los
números salen de los logs, sin estimaciones ni redondeos.

## Investigación previa

### 1. ¿Qué es un router de modelos y qué problema resuelve?

Un **model router** (`openrouter/auto` en OpenRouter) es un modelo virtual
que, en vez de responder él mismo, **elige a qué modelo real de qué
proveedor mandar cada request**, según qué modelo respondió mejor tareas
parecidas en el mercado de OpenRouter durante los últimos 7 días.

El problema que resuelve: nadie tiene que decidir a mano "esto es una tarea
de código, mando a Claude" / "esto es barato, mando a DeepSeek". El router
externaliza esa decisión y además da resiliencia (fallback automático a otro
proveedor si el elegido está caído o saturado), sin cambiar una línea de
código del lado del cliente: siempre es el mismo endpoint, cambia solo el
campo `model`.

*Limitación conocida: la ficha pública de `openrouter/auto` no expone en su
HTML estático el mecanismo interno de selección más allá de lo descrito
arriba.*

### 2. Mapa de modelos — el más avanzado de cada proveedor

Datos de `GET https://openrouter.ai/api/v1/models` (catálogo real,
consultado el 2026-09-18). Criterio de "más avanzado": el modelo no-batch
más caro y más reciente (`created`) de cada proveedor — proxy razonable
cuando no hay acceso programático al gráfico de benchmarks.

| Proveedor | Modelo | Precio in / out (por 1M tok) | Contexto |
|---|---|---|---|
| OpenAI | `openai/gpt-5.5-pro` | $30.00 / $180.00 | 1.05M |
| Anthropic | `anthropic/claude-fable-5.1` | $10.00 / $50.00 | 1.0M |
| xAI | `x-ai/grok-4.6` | $2.00 / $6.00 | 500K |
| Google | `google/gemini-3.1-pro-preview` | $2.00 / $12.00 | 1.05M |
| DeepSeek | `deepseek/deepseek-v4-pro-0813` | $0.578 / $1.734 | 1.05M |
| Qwen | `qwen/qwen3.8-max-0902` | $2.00 / $6.00 | 1.0M |
| Moonshot | `moonshotai/kimi-k3` | $2.10 / $10.95 | 1.05M |

**Hallazgo:** la posición en benchmarks que publica `openrouter.ai/discover`
se renderiza como gráfico interactivo (JS), no como texto plano, así que no
es extraíble con un fetch de solo lectura. Queda documentado como limitación
en lugar de reportar un número no verificado.

### 3. Comparación de `supported_parameters`

De los 4 modelos usados, según la misma consulta al catálogo:

| Modelo | `supported_parameters` relevantes |
|---|---|
| `openai/gpt-5.6-luna` | `reasoning`, `reasoning_effort`, `include_reasoning`, `response_format`, `structured_outputs`, `tools`, `tool_choice`, `seed`, `max_completion_tokens` — **sin** `temperature`/`top_p`/`top_k` |
| `anthropic/claude-haiku-4.5` | `reasoning`, `include_reasoning`, `response_format`, `structured_outputs`, `temperature`, `top_p`, `top_k`, `tools` — **sin** `reasoning_effort` |
| `google/gemini-3.7-flash` | `reasoning`, `reasoning_effort`, `include_reasoning`, `response_format`, `structured_outputs`, `temperature`, `top_p`, `tools` |
| `deepseek/deepseek-v4-flash-0731` | superset de lo anterior + `frequency_penalty`, `presence_penalty`, `repetition_penalty`, `logit_bias`, `logprobs`, `top_logprobs`, `min_p`, `top_a`, `parallel_tool_calls` |

**Conclusión:** los 4 aceptan `reasoning` y `response_format`/
`structured_outputs`, que es lo que hace viable el diseño de slots de esta
interfaz. Pero **solo OpenAI y Google exponen `reasoning_effort` como nivel
discreto**: Anthropic controla el presupuesto de pensamiento con
`reasoning.max_tokens` en lugar de un enum, y por eso el slot 2 no ofrece
selección de effort. DeepSeek es el que más parámetros de sampling clásico
soporta (penalties, logprobs, top-k/top-a), coherente con su posición de
modelo barato para uso programático.

Los 4 IDs usados siguen vigentes en el catálogo al 2026-09-18; no hizo falta
sustituir ninguno.

## Verificación y tests

```bash
python3 tests/test_vida.py vida.py                 # 9 tests de aceptación de vida.py
python3 -m unittest discover -s tests -p 'test_chat_cli.py'   # 14 tests de la interfaz
```

Estado al 2026-09-18: **9/9 y 14/14 en verde**. Los tests de la interfaz
corren con la red mockeada (no consumen créditos ni requieren API key):
cubren el armado del body por slot, el parseo de usage —incluida la
detección de razonamiento no declarado—, el formato del log y el flujo de
`Conversation.send()`.

## Estructura del repositorio

```
src/
  models.py                # registro de los 4 slots y su configuración por capacidad
  openrouter_client.py     # cliente HTTP + parseo de usage
  conversation_logger.py   # log .md por conversación
  chat_cli.py              # interfaz de chat interactiva
  prompt_vida.py           # especificación (prompt) para generar vida.py
  run_ejercicio1_demo.py   # regenera los logs de prueba de los 4 modelos
  run_ejercicio2.py        # corrida scripteada y auditable de la generación de vida.py
tests/
  test_vida.py             # tests de aceptación de vida.py (referencia, no se modifican)
  test_chat_cli.py         # tests propios de la interfaz (mockeados, sin red)
logs/
  ejercicio1/              # un log .md por modelo probado
  ejercicio2/              # logs de la generación de vida.py
reports/
  informe-de-consumo.md    # informe final de tokens, caching y costos
vida.py                    # generado por el modelo, sin ediciones manuales
SPEC.md                    # diseño técnico de la interfaz
CLAUDE.md                  # reglas de trabajo del repositorio
```
