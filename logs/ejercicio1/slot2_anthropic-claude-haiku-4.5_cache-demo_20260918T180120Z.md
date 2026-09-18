# Conversacion — slot 2 — `anthropic/claude-haiku-4.5`

Inicio (UTC): 2026-09-18T18:01:20.722481+00:00

## contexto estático (system, 17222 caracteres)

<details><summary>ver contenido</summary>

```
Documento de referencia (consigna de una materia universitaria). Id de corrida: 36656969d8e447658f7a6c94b3445446. Vas a responder preguntas puntuales sobre este documento, citando partes concretas cuando corresponda.

=== mission.md ===
# Misión: el prompt mínimo

## La idea

Armar un chat propio que sirve varios modelos, y con él resolver un target de programación en la **mínima cantidad de prompts posible**, midiendo todo: tokens de entrada, de salida, de pensamiento, tokens cacheados y gasto en dólares. Esta misión pone bajo presupuesto las técnicas de la clase de prompting.

Cada punto de calidad se paga en tokens, latencia y dinero. Cada prompt de más queda registrado en la factura.

## Qué es OpenRouter

Todo pasa por **OpenRouter** (https://openrouter.ai). Es una **API unificada** sobre los modelos de todos los proveedores: una sola key, un solo endpoint (compatible con el formato de OpenAI) y el mismo request sirve para llamar a GPT, Claude, Gemini, DeepSeek, Grok, Qwen o Kimi cambiando solo el id del modelo.

Los servicios que provee:

- **Catálogo y comparación**: fichas por modelo con precios, ventana de contexto, benchmarks y parámetros soportados, más una vista comparativa en paralelo.
- **Routing**: el Auto Router elige el modelo según la tarea, y hay fallbacks entre proveedores cuando uno se cae o se satura.
- **Contabilidad centralizada**: cada respuesta trae su usage y su costo, y el dashboard de actividad acumula el gasto de toda la cuenta, venga del modelo que venga.

Para qué sirve más allá de esta misión:

- **Cambiar el modelo backend de sus herramientas**: Codex, Claude Code y otras aceptan un endpoint compatible, así que se las puede apuntar a OpenRouter y trabajar con el modelo que cada uno prefiera.
- **Probar modelos nuevos** apenas salen, sin crear una cuenta en cada proveedor.
- **Eficientizar el gasto**: mandar cada tarea a un modelo barato que la resuelva igual, a mano o vía routing.

### Requisitos

- Una cuenta de OpenRouter por grupo, con crédito cargado (el monto lo define la cátedra; con los modelos de esta misión, el gasto total son centavos).
- Python y su IA para programar de preferencia: Claude Code, Antigravity, Copilot o Codex.

## Antes de todo (obligatorio)

Antes de escribir código, exploren la plataforma y anoten lo que encuentren:

1. **Qué es un router.** Miren https://openrouter.ai/models?arch=Router&model_authors=openrouter y la ficha del **Auto Router** (https://openrouter.ai/openrouter/auto), que elige el modelo según lo que el mercado de OpenRouter usó para tareas parecidas en los últimos 7 días. Contesten en una línea: ¿qué hace un router de modelos y qué problema resuelve?
2. **El mapa de modelos.** En https://openrouter.ai/discover, busquen el **modelo más avanzado de cada proveedor conocido**: OpenAI, Anthropic, Grok, Gemini, DeepSeek, Qwen y Kimi. Anoten para cada uno: precio por millón de tokens de entrada y de salida, tamaño de ventana de contexto, y qué posición ocupa en los benchmarks que muestra la página. Para verlos en paralelo está la **vista comparativa**: `openrouter.ai/compare/<proveedor>/<modelo>/<proveedor>/<modelo>/...` compara precios, contexto, benchmarks y parámetros en una misma pantalla (por ejemplo, los cuatro modelos del ejercicio 1: https://openrouter.ai/compare/openai/gpt-5.6-luna/anthropic/claude-haiku-4.5/google/gemini-3.7-flash/deepseek/deepseek-v4-flash-0731).
3. **Parámetros comunes.** En https://openrouter.ai/models, el click en un modelo abre su ficha (`openrouter.ai/<proveedor>/<modelo>`), con descripción, ventana de contexto, precios y parámetros. Comparen dos o tres fichas de proveedores distintos: qué parámetros acepta cada uno (reasoning/effort, salidas estructuradas, temperatura y demás perillas de sampling). La versión programática de lo mismo: `GET https://openrouter.ai/api/v1/models` devuelve cada modelo con su campo `supported_parameters`. No todos aceptan lo mismo.

## Ejercicio 1: una interfaz de chat, cuatro modelos

Armen una **interfaz de chat** que sirva estos **4 modelos** vía OpenRouter. No tiene que estar "linda" ni tener nada alrededor: es simplemente un chat que permite elegir el modelo y guarda las conversaciones. La pueden codear con su IA para programar (Claude Code, Antigravity, Copilot, Codex).

| Slot | Modelo | Capacidad que ejercita | Qué aplica de la clase |
|---|---|---|---|
| 1 | `openai/gpt-5.6-luna` | **Effort configurable**: la interfaz permite elegir el nivel de `reasoning_effort` | Effort y thinking |
| 2 | `anthropic/claude-haiku-4.5` | **Prompt caching explícito** (`cache_control`), con un contexto estático grande para provocar hits | Caching y su economía |
| 3 | `google/gemini-3.7-flash` | **Salidas estructuradas** (JSON Schema) | Prompts estructurados |
| 4 | `deepseek/deepseek-v4-flash-0731` | **El escalón barato**: 15 veces más barato que el slot 2; comparen el costo de la misma pregunta | Elegir modelo, cascading |

(IDs verificados al 2026-09-02; si alguno desaparece del catálogo, reemplácenlo por el equivalente vigente del mismo proveedor y anótenlo en el informe.)

- OpenRouter incluye el **usage en cada respuesta** y no hace falta pedirlo con ningún parámetro: `usage.prompt_tokens`, `completion_tokens`, `prompt_tokens_details.cached_tokens`, `completion_tokens_details.reasoning_tokens`, `cost` y `cache_discount`.
- El **razonamiento** se controla con el parámetro unificado `reasoning`: `{"effort": "low" | "medium" | "high" | ...}` en el modelo del slot 1 (OpenAI); Claude y Gemini aceptan además `{"max_tokens": N}` como presupuesto de pensamiento.
- El **caching** es automático en OpenAI, Gemini y DeepSeek; en Anthropic y Qwen se activa marcando los bloques estáticos con `"cache_control": {"type": "ephemeral"}`. El hit se ve en `cached_tokens` y en `cache_discount`.

Requisitos de la interfaz:

- Muestra, **después de cada respuesta**, el usage que devuelve la API: tokens de entrada, de salida, de razonamiento y cacheados, y el costo.
- Permite **switchear de modelo**; cambiar de modelo inicia una conversación nueva.
- **Guarda el log de cada conversación en un archivo `.md`** (rol, mensaje, usage por respuesta). El log es la evidencia de auditoría del ejercicio 2: con él la cátedra verifica cuántos prompts hubo, qué se gastó en cada intento y si hubo cache hits. Una corrida sin log no se puede auditar y no cuenta.
- Sirve los cuatro modelos, cada uno de un proveedor distinto.

**Criterio de éxito:** desde la interfaz se puede chatear con los 4 modelos, ver el usage de cada respuesta, y queda un log `.md` por conversación. En el slot 1 se ve el efecto de cambiar el effort; en el slot 2 se ve un cache hit (el costo de entrada baja en la segunda pasada del mismo contexto).

## Ejercicio 2: el target en 1 prompt

El target: **el juego de la vida de Conway** (las reglas y los patrones clásicos están explicados en https://es.wikipedia.org/wiki/Juego_de_la_vida), en un solo script de Python (`vida.py`), solo con la biblioteca estándar. El modelo: **`deepseek/deepseek-v4-flash-0731`** (el del slot 4), con el razonamiento activado.

El contrato exacto (su prompt tiene que transmitirlo completo):

- Uso: `python3 vida.py <archivo_estado_inicial> <generaciones>`.
- El archivo de estado es una grilla rectangular: una línea por fila, `#` célula viva, `.` célula muerta.
- El mundo es **finito**, del tamaño de la grilla: fuera de los bordes todo está muerto. Sin wrap-around.
- El script imprime por stdout la grilla resultante tras N generaciones, en el mismo formato.
- Con `generaciones = 0` imprime el estado inicial tal cual.

La cátedra provee los tests: `tests/test_vida.py` (9 casos: osciladores, naturalezas muertas, el glider, nacimiento, muerte por soledad, bordes y generación cero). Reciben la ruta del script y ejecutan los tests contra su interfaz estándar: `python3 test_vida.py ruta/a/vida.py` (sin argumento buscan `vida.py` al lado). Por eso el contrato de arriba no es negociable: es la interfaz que los tests invocan.

Las reglas:

1. **A través de su chat** del ejercicio 1, pidan el script al modelo indicado.
2. Tiene que quedar **correcto en 1 prompt, o a lo sumo 2** (el segundo solo para pulir detalles).
3. Si se pasan de 2, **la corrida quedó quemada**: conversación nueva, prompt reescrito desde cero, y de vuelta. Prohibido parchear a mano o seguir chateando: lo que se mejora entre intentos es **el prompt**, no el código.
4. "Correcto" significa: **los 9 tests de `test_vida.py` pasan** con el script tal cual salió del chat.
5. **Usar caching es obligatorio.** En DeepSeek el cache es automático por prefijo repetido, así que se activa con el diseño del prompt. La parte estática (el contrato, las instrucciones, los ejemplos) va al principio, idéntica en todos los intentos; lo que cambia entre corridas va al final. A partir del segundo intento, el usage tiene que mostrar `cached_tokens` mayor que cero, y eso va al informe.

Un prompt que sale bien a la primera es una **especificación completa**. Los 6 componentes de la clase (rol, contexto, instrucciones, restricciones, ejemplos, input) más few-shot de los casos clave (el contrato de arriba trae varios listos para convertir en ejemplos) rinden más que cualquier pedido de "hacelo bien".

**Criterio de éxito:** el log de la conversación ganadora muestra 1 o 2 prompts en total, `test_vida.py` corre con los 9 tests en verde, y los intentos posteriores al primero muestran cache hits en el usage.

## Ejercicio 3: la cuenta final

Documenten, para **todos** los intentos del ejercicio 2 (los quemados también):

- Tokens de entrada y de salida por intento, y totales.
- Tokens de pensamiento (si usaron un razonador) y qué se facturó por ellos. Ojo: algunos modelos (la serie o de OpenAI) razonan sin devolver esos tokens en la respuesta; si les pasa, documéntenlo como hallazgo.
- Tokens cacheados y cuánto ahorraron.
- Gasto total en USD, contrastado contra el dashboard de actividad de OpenRouter.
- Una conclusión de tres líneas: qué cambiarían del prompt, del modelo o de los parámetros para bajar el costo sin perder el "1 prompt".

**Criterio de éxito:** los números del informe cierran contra el dashboard, y la conclusión nombra una decisión concreta (no "mejorar el prompt").

## La entrega

Se entrega **pusheando al repo de GitHub del grupo**, con la forma de trabajo de la clase 2: CLAUDE.md, SPEC.md, TDD e historia de commits limpia. Esa forma de trabajo aplica a lo que construyen ustedes con su IA para programar (la interfaz de chat y todo lo que rodea al LLM), no a `vida.py`: ese archivo entra al repo tal cual salió del chat, y sus tests son los de la cátedra. El repo tiene que contener:

- **El código de la interfaz** del ejercicio 1.
- **Un log de chat de prueba por cada uno de los 4 modelos** (`.md`): prueban que cada modelo es usable desde la interfaz y que las conversaciones se guardan con su usage.
- **Los logs del chat con el que crearon el script de Conway**: el de la conversación ganadora y los de los intentos quemados. Son la evidencia que respalda el informe del ejercicio 3.
- **El script `vida.py`** resultante.
- **El script de testing de la cátedra** (`test_vida.py`), tal cual se entregó, corriendo en verde contra su `vida.py`.
- **El informe** del ejercicio 3.


=== rubric.md ===
# Rúbrica — Misión: el prompt mínimo

Instrumento de corrección derivado de `mission.md`. Cada criterio se evalúa contra
**evidencia observable en el repositorio entregado**, no contra la descripción que el grupo
hace de su trabajo.

Total: 100 puntos.

---

## Regla de admisibilidad

La misión lo dice literalmente: *"una corrida sin log no se puede auditar y no cuenta"*.

**Sin los logs `.md` con su usage, el ejercicio 2 y el ejercicio 3 valen cero**, aunque el
script funcione y el informe esté escrito. No es una penalización de estilo: sin log no hay
forma de verificar cuántos prompts hubo, y ese es el objeto de la misión.

---

## Ejercicio 1 — Interfaz de chat, cuatro modelos (30 pts)

| # | Criterio | Pts | Evidencia que lo confirma |
|---|---|---|---|
| 1.1 | Sirve los cuatro modelos, uno por proveedor | 6 | Los cuatro ids en el código; un log por modelo |
| 1.2 | Muestra el usage después de cada respuesta | 6 | Entrada, salida, razonamiento, cacheados y costo, los cinco |
| 1.3 | Permite cambiar de modelo, y el cambio inicia conversación nueva | 4 | Código del selector; el log no mezcla modelos |
| 1.4 | Guarda un log `.md` por conversación con rol, mensaje y usage | 6 | Archivos en el repo, no capturas de pantalla |
| 1.5 | Slot 1: se ve el efecto de cambiar el nivel de esfuerzo | 4 | Dos corridas del mismo prompt con niveles distintos y sus tokens de razonamiento |
| 1.6 | Slot 2: se ve un cache hit | 4 | `cached_tokens` mayor que cero en la segunda pasada del mismo contexto |

**Descuentos.** Si sustituyeron algún modelo del catálogo sin anotarlo en el informe,
menos 2. Si el usage se muestra parcial (faltan tokens de razonamiento o cacheados),
1.2 va a la mitad.

**No se puntúa.** Que la interfaz sea linda. La misión lo dice explícitamente.

---

## Ejercicio 2 — El target en 1 prompt (40 pts)

| # | Criterio | Pts | Evidencia que lo confirma |
|---|---|---|---|
| 2.1 | Los 9 tests pasan con el script tal cual salió del chat | 12 | Correr `test_vida.py` contra el `vida.py` entregado |
| 2.2 | La conversación ganadora tiene 1 o 2 prompts en total | 12 | Contar turnos de usuario en el log ganador |
| 2.3 | Los intentos quemados están entregados, no escondidos | 6 | Un log por intento; el informe los cuenta todos |
| 2.4 | Caching en el diseño del prompt: `cached_tokens` > 0 del segundo intento en adelante | 6 | Usage de cada intento en su log |
| 2.5 | El prompt es una especificación, no un pedido | 4 | Rol, contexto, instrucciones, restricciones, ejemplos e input identificables |

**La regla dura.** Si el `vida.py` entregado **no coincide** con el que aparece en el log
ganador, 2.1 y 2.2 valen cero. Parchear a mano está prohibido por la consigna y es
verificable comparando los dos textos.

**Cómo se cuenta un prompt.** Turnos de rol `user` en la conversación ganadora. Un
mensaje que solo dice "corré los tests" cuenta igual que cualquier otro.

**Gradiente en 2.2.** Un prompt: 12. Dos prompts: 9. Tres o más sin abrir conversación
nueva: 0, porque la corrida estaba quemada y siguieron igual.

**Escala en 2.1.** Los nueve tests: 12. Siete u ocho: 6. Menos: 0. No hay crédito parcial
por "casi anda": el criterio de la misión es binario por test.

---

## Ejercicio 3 — La cuenta final (20 pts)

| # | Criterio | Pts | Evidencia que lo confirma |
|---|---|---|---|
| 3.1 | Tokens de entrada y salida por intento, y totales | 4 | Tabla en el informe, reconciliable contra los logs |
| 3.2 | Tokens de pensamiento y qué se facturó por ellos | 4 | Si el modelo no los devuelve, documentado como hallazgo |
| 3.3 | Tokens cacheados y ahorro calculado | 4 | El ahorro derivado, no solo el conteo |
| 3.4 | Gasto total en USD contrastado contra el dashboard | 4 | La comparación explícita, y la diferencia explicada si la hay |
| 3.5 | Conclusión de tres líneas con una decisión concreta | 4 | Nombra modelo, parámetro o cambio de prompt. "Mejorar el prompt" no puntúa |

**Verificación cruzada.** Los números del informe tienen que cerrar contra los logs. Una
discrepancia sin explicar cuesta la mitad del criterio afectado. Si el informe reporta
menos intentos de los que hay en los logs, 2.3 también cae.

---

## Forma de trabajo del repositorio (10 pts)

| # | Criterio | Pts | Evidencia que lo confirma |
|---|---|---|---|
| 4.1 | `CLAUDE.md` con instrucciones reales del proyecto | 3 | Que dirija el trabajo, no un archivo de relleno |
| 4.2 | `SPEC.md` que describe lo que se construyó | 3 | Coherente con el código entregado |
| 4.3 | Historia de commits limpia | 4 | Mensajes que explican el cambio; no un único commit "todo" |

---

## Trabajo previo obligatorio

La misión pide, **antes de escribir código**, tres respuestas: qué hace un router de
modelos, el mapa de los siete proveedores con precio, ventana y posición en benchmarks, y
la comparación de parámetros soportados entre fichas.

**No suma puntos por separado.** Se evalúa como parte del informe: si está ausente, el
ejercicio 3 no puede superar los 15 puntos, porque las decisiones de modelo quedan sin
fundamento.

---

## Señales de alarma

Cosas que conviene mirar de cerca antes de poner la nota.

- **El log ganador no tiene marcas de tiempo o las tiene fuera de orden.** Sugiere edición
  posterior.
- **El primer intento ya muestra `cached_tokens` mayor que cero.** Imposible con prefijo
  nuevo; sugiere que hubo corridas previas no entregadas.
- **El costo del informe es más bajo que la suma de los logs.** Suelen faltar intentos.
- **El `vida.py` tiene un estilo distinto al del código del log**, o comentarios que el
  modelo no escribió.
- **Todos los grupos entregan el mismo prompt.** No está prohibido colaborar, pero cambia
  qué se está midiendo y conviene saberlo antes de comparar.

---

## Planilla de salida

Por grupo, una fila:

| Grupo | Repo | E1 /30 | E2 /40 | E3 /20 | Repo /10 | Total | Prompts del ganador | Tests en verde | Gasto USD |
|---|---|---|---|---|---|---|---|---|---|

```

</details>

## user — 2026-09-18T18:01:20.722705+00:00

En una linea: ¿cuántos puntos vale en total el Ejercicio 2 segun la rubrica?

## assistant — 2026-09-18T18:01:22.639452+00:00

Según la rúbrica, el Ejercicio 2 vale **40 puntos** en total.

**usage:** in=5627 · out=28 · reasoning=0 · cached=0 · cost=$0.007165

## user — 2026-09-18T18:01:22.639812+00:00

En una linea: ¿qué pasa si el vida.py entregado no coincide con el del log ganador?

## assistant — 2026-09-18T18:01:24.288079+00:00

Si el `vida.py` entregado no coincide con el del log ganador, los criterios 2.1 y 2.2 valen cero (24 puntos en total).

**usage:** in=5688 · out=49 · reasoning=0 · cached=5593 · cost=$0.000899

Fin (UTC): 2026-09-18T18:01:24.288944+00:00