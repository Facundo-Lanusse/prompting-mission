# Informe de consumo — tokens, caching y costos

Todos los números salen directo de los logs en `logs/` (no se estiman ni se
redondean a mano) y de una consulta a `GET https://openrouter.ai/api/v1/key`
con la propia API key, que devuelve el gasto acumulado de la cuenta.

Fecha de las mediciones: 2026-09-18.

## 1. Generación de `vida.py` — tokens por corrida

Hubo **un solo intento de resolución, y salió correcto**: `vida.py` pasó los
9 tests de aceptación con **1 prompt**. No hubo corridas descartadas.

| Corrida | Rol | in | out | reasoning | cached | costo USD |
|---|---|---:|---:|---:|---:|---:|
| Intento 1 | **Ganador** — script correcto, 9/9 tests | 1147 | 24848 | 24438 | 0 | 0.004541 |
| Verificación de caching #1 | Repite el mismo prefijo estático para medir si cachea; no es un intento de resolución | 1147 | 8122 | 7802 | 0 | 0.002070 |
| Verificación de caching #2 | Ídem, inmediatamente después, sin demora | 1147 | 11059 | 10745 | 0 | 0.001888 |
| **Total** | | **3441** | **44029** | **42985** | **0** | **0.008499** |

Log ganador:
`logs/ejercicio2/slot4_deepseek-deepseek-v4-flash-0731_intento1_20260918T180145Z.md`.
El `vida.py` de la raíz del repositorio es exactamente el código de ese log
(verificado con diff; la única diferencia son los fences ` ```python ` que el
runner recorta al extraerlo, no una edición de la lógica).

## 2. Tokens de razonamiento y su facturación

Las 3 corridas usaron `reasoning: {"enabled": true}` sobre
`deepseek/deepseek-v4-flash-0731`, y el modelo **declaró sus
`reasoning_tokens` en las tres**. No se dio el caso de "razona pero no lo
declara".

Dato relevante para el costo: **el 98% de los tokens de salida del intento
ganador fueron de razonamiento** (24438 de 24848), no de código — el script
final tiene 67 líneas.

En la etapa 1 se verificó explícitamente el mismo comportamiento con
`openai/gpt-5.6-luna`, el modelo con effort configurable:

| Effort | reasoning_tokens | Bloque de razonamiento en el mensaje | Lectura |
|---|---:|---|---|
| `low` | 0 | ausente | efectivamente no razonó |
| `high` | 60 | presente | razonó y lo declaró |

No se detectó razonamiento oculto o no facturado en ninguna de las 9
llamadas reales de esta entrega. La comprobación no es manual:
`openrouter_client.py` compara automáticamente la presencia de un bloque
`reasoning`/`reasoning_content` contra `reasoning_tokens == 0` y marca el
`Usage` cuando difieren.

## 3. Tokens cacheados y ahorro

### Caching automático por prefijo (DeepSeek): 0 hits

`cached_tokens` quedó en **0 en las 3 corridas**, incluidas las dos
verificaciones hechas una atrás de la otra con el prefijo estático idéntico
byte a byte.

Explicación, no excusa: el prefijo estático de `prompt_vida.py` tiene ~3450
caracteres (~860 tokens), por debajo del umbral típico de ~1024 tokens que
varios proveedores exigen para activar el cacheo automático de prefijo. El
contexto que sí produjo cache hit (abajo) tenía ~17.200 caracteres (~4300
tokens).

Conclusión de diseño: **optimizar para "un solo prompt, lo más corto
posible" compite directamente con "prefijo lo bastante largo para
cachear"**. Acá ganó lo primero, y el ahorro por caching en esta etapa fue
$0.

### Caching explícito (Anthropic, slot 2): hit confirmado

Mismo contexto estático en dos turnos consecutivos, con
`cache_control: {"type": "ephemeral"}`:

| Turno | in | cached | costo USD |
|---|---:|---:|---:|
| 1 — escritura de cache | 5627 | 0 | 0.007165 |
| 2 — lectura de cache | 5688 | 5593 | 0.000899 |

Desglose del turno 2: sin caching, los 5688 tokens de entrada se habrían
facturado a tarifa normal ($0.000001/tok = $0.005688). Con caching, 5593
salieron a tarifa de lectura de cache ($0.0000001/tok = $0.0005593) y solo
95 a tarifa normal ($0.000095). **Ahorro de ~$0.0050 en ese turno, ~89%
menos costo de entrada**, consistente con el costo total reportado por la
API ($0.000899 ≈ $0.0005593 + $0.000095 + $0.000245 de salida).

Para que el hit fuera real y no heredado de una corrida anterior todavía
dentro del TTL de cache, el contexto estático incluye un identificador único
por corrida: el primer turno es siempre un miss genuino.

## 4. Gasto total en USD y reconciliación con la cuenta

| Fuente | Monto USD |
|---|---:|
| Suma de logs — etapa 1 (4 modelos, 6 llamadas) | 0.008820 |
| Llamada de humo inicial (slot 4, sin log, para validar el cliente) | 0.000024 |
| Suma de logs — etapa 2 (3 corridas) | 0.008499 |
| **Total reconstruido desde logs propios** | **0.017343** |
| `usage` reportado por `GET /api/v1/key` | **0.027187** |
| **Diferencia sin explicar** | **0.009844** |

**La diferencia no cierra, y queda reportada en vez de omitida.** No se tomó
una captura del `usage` de la cuenta *antes* de empezar —el único error real
de proceso de esta entrega—, así que no es posible separar qué parte de esos
~$0.0098 corresponde a actividad previa de la cuenta de un gasto propio no
registrado.

Lo que sí está descartado: llamadas propias sin loguear. La única fuera de
los logs fue la de humo ($0.000024, ya sumada arriba), y las consultas a
`/api/v1/models` y `/api/v1/key` no tienen costo.

**Corrección de proceso adoptada:** tomar snapshot de `usage` antes y después
de cada sesión de trabajo.

## 5. Conclusiones y decisiones

1. **Bajar el nivel de reasoning del slot 4 de alto a medio para el prompt de
   `vida.py`.** El 98% del output del intento ganador fue razonamiento y no
   código, y el prompt ya es una especificación completa con ejemplos: hay
   margen razonable para gastar menos pensamiento por el mismo resultado.
2. **Si se busca que el caching por prefijo entre en juego, hay que inflar el
   prefijo estático por encima de ~1024 tokens** (por ejemplo, sumando los 9
   casos de aceptación como ejemplos en vez de los 6 actuales). Es una
   decisión de diseño explícita, con su costo: más tokens de entrada en cada
   corrida a cambio de descuento a partir de la segunda.
3. **Antes de fijar el nivel medio, correr un control.** Si con menos
   razonamiento el script deja de salir bien a la primera, el costo de una
   corrida de reintento (otro ciclo completo de razonamiento) supera el
   ahorro buscado.
