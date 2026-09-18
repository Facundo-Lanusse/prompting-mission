# Ejercicio 3 — la cuenta final

Todos los números de este informe salen directo de los logs en `logs/` (no
se estiman ni se redondean a mano) y de una consulta a
`GET https://openrouter.ai/api/v1/key` con la propia API key, que devuelve
el equivalente al dashboard de actividad de OpenRouter.

## 1. Ejercicio 2 — tokens por intento

Hubo **un solo intento**, y ganó: `vida.py` salió correcto (9/9 tests) en
**1 prompt**. No hubo intentos quemados.

| Corrida | Rol | in | out | reasoning | cached | costo USD |
|---|---|---:|---:|---:|---:|---:|
| Intento 1 | **Ganador** (1 prompt, cuenta para 2.1/2.2) | 1147 | 24848 | 24438 | 0 | 0.004541 |
| Verif. caching #1 | No es un intento de resolución — repite el mismo prefijo estático para chequear si cachea | 1147 | 8122 | 7802 | 0 | 0.002070 |
| Verif. caching #2 | Ídem, inmediatamente después (sin demora) | 1147 | 11059 | 10745 | 0 | 0.001888 |
| **Total Ejercicio 2** | | **3441** | **44029** | **42985** | **0** | **0.008499** |

Log ganador: `logs/ejercicio2/slot4_deepseek-deepseek-v4-flash-0731_intento1_20260918T180145Z.md`.
El `vida.py` entregado en la raíz del repo es exactamente el código de ese
log (verificado con diff; la única diferencia son los fences ` ```python `
que el runner recorta al extraerlo, no una edición de la lógica).

## 2. Tokens de pensamiento y su facturación

Las 3 corridas del Ejercicio 2 usaron `reasoning: {"enabled": true}` sobre
`deepseek/deepseek-v4-flash-0731`, y el modelo **sí declaró** sus
`reasoning_tokens` en las tres (columna `reasoning` arriba) — no se dio el
caso de "razona pero no lo declara" que advierte `mission.md`. Dato
llamativo: el **98% de los tokens de salida del intento ganador fueron de
razonamiento** (24438 de 24848), no de código — el script final tiene
apenas 67 líneas.

En el Ejercicio 1 también se verificó explícitamente este hallazgo con
`openai/gpt-5.6-luna` (slot 1, el modelo que la consigna señala como
candidato a este comportamiento): con `effort=low` devolvió
`reasoning_tokens=0` y **sin** bloque de razonamiento en el mensaje — o
sea, efectivamente no razonó, no que haya razonado sin declararlo. Con
`effort=high` sí declaró 60 tokens de razonamiento. No detectamos ningún
caso de razonamiento oculto/no facturado en ninguna de las 9 llamadas
reales hechas en esta misión (el cliente (`openrouter_client.py`) tiene un
chequeo automático para esto: compara si el mensaje trae un bloque
`reasoning`/`reasoning_content` contra si `reasoning_tokens` es 0).

## 3. Tokens cacheados y ahorro

**Ejercicio 2 (DeepSeek): `cached_tokens` quedó en 0 en las 3 corridas**,
incluidas las dos verificaciones hechas una atrás de la otra con el
prefijo estático **byte a byte idéntico**. Hallazgo, no excusa: el
prefijo estático de `vida.py` (`src/prompt_vida.py`) tiene ~3450
caracteres (~860 tokens estimados) — por debajo del umbral típico de
~1024 tokens que varios proveedores exigen para activar el cacheo
automático de prefijo. El contexto que sí mostró cache hit (ver abajo)
tenía ~17200 caracteres (~4300 tokens). Diseñar para "1 prompt mínimo"
compite directamente con "prefijo lo bastante largo para cachear": acá
ganó lo primero, y el ahorro de caching en el Ejercicio 2 fue $0.

**Ejercicio 1, slot 2 (Anthropic, caching explícito): sí hubo cache hit.**
Turno 1 (escritura): `in=5627, cached=0, costo=$0.007165`. Turno 2 (mismo
contexto estático, `cache_control: ephemeral`): `in=5688, cached=5593,
costo=$0.000899`. Ahorro calculado sobre el turno 2: sin caching, los
5688 tokens de entrada se hubieran facturado a la tarifa normal
($0.000001/tok = $0.005688); con caching, 5593 tokens salieron a la
tarifa de lectura de cache ($0.0000001/tok = $0.0005593) y solo 95 a
tarifa normal ($0.000095) — **ahorro de ~$0.0050 en ese turno, ~89% menos
costo de entrada**, consistente con el costo total reportado
($0.000899 ≈ $0.0005593 + $0.000095 + $0.000245 de output).

## 4. Gasto total en USD vs. dashboard

| Fuente | Monto |
|---|---:|
| Suma de logs — Ejercicio 1 | $0.008820 |
| Llamada de humo inicial (slot 4, sin log, solo para validar el cliente) | $0.000024 |
| Suma de logs — Ejercicio 2 | $0.008499 |
| **Total reconstruido desde logs propios** | **$0.017343** |
| `usage` reportado por `GET /api/v1/key` (equivalente al dashboard) | **$0.027187** |
| **Diferencia sin explicar** | **$0.009844** |

**La diferencia no cierra, y lo decimos en vez de esconderlo.** No
tomamos una foto del `usage` de la cuenta *antes* de empezar (el único
error real de proceso de esta entrega), así que no podemos separar qué
parte de esos ~$0.0098 es actividad previa de la cuenta (la cátedra pide
una cuenta con crédito ya cargado, y la key pudo haberse probado antes de
esta sesión) de un gasto nuestro no registrado. Descartamos que sean
llamadas nuestras sin loguear: la única no logueada fue la de humo
($0.000024, ya sumada arriba) y las consultas a `/api/v1/models` y
`/api/v1/key` no tienen costo. **Decisión tomada a partir de esto:**
la próxima vez, snapshot de `usage` antes y después de la sesión.

## 5. Conclusión (3 líneas, decisión concreta)

1. **Bajar `reasoning.effort` de "high" a "medium" en el slot 4 para el
   prompt de `vida.py`**: el 98% del output del intento ganador fue
   razonamiento, no código, y el contrato ya es una especificación
   completa con ejemplos — probablemente no necesita el nivel más alto.
2. Si se quiere que el caching de DeepSeek realmente entre en juego,
   **inflar el prefijo estático por encima de ~1024 tokens** (por ejemplo
   incluyendo los 9 casos de `test_vida.py` como ejemplos adicionales en
   vez de los 6 actuales) — pero esto es una decisión de diseño explícita
   a tomar, no algo automático.
3. Antes de comprometerse a "medium", correr un control con effort
   reducido: si deja de salir bien a la primera, el costo de reintentos
   (otra corrida completa de reasoning) puede superar el ahorro buscado.

## Trabajo previo obligatorio

Ver `README.md` — respuestas a las 3 preguntas obligatorias (qué es un
router, mapa de los 7 proveedores, comparación de `supported_parameters`),
con datos reales de `GET /api/v1/models` consultado el 2026-09-18.
