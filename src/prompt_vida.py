"""Especificacion (prompt) para generar vida.py.

`CONTEXTO_ESTATICO` tiene que quedar IDENTICO entre todos los intentos (el
ganador y los descartados): es lo que permite que DeepSeek cachee el
prefijo entre corridas. Lo unico que cambia es `pedido_final()`.
"""
from __future__ import annotations

CONTEXTO_ESTATICO = '''\
# Rol

Sos un desarrollador Python senior especializado en escribir scripts de \
linea de comandos correctos, minimalistas y sin dependencias externas.

# Contexto

Necesito un unico archivo `vida.py` que implemente el Juego de la Vida de \
Conway. Se va a ejecutar tal cual, sin retoques, y se va a validar contra \
una bateria de tests automatizados que invocan el script como subproceso \
y comparan su stdout byte a byte. Por eso el formato de salida tiene que \
ser exacto.

# Instrucciones

1. El script se invoca asi: `python3 vida.py <archivo_estado_inicial> <generaciones>`.
2. `<archivo_estado_inicial>` es la ruta a un archivo de texto con una \
grilla rectangular: una linea por fila, `#` = celula viva, `.` = celula \
muerta. Todas las filas tienen el mismo largo.
3. `<generaciones>` es un entero >= 0.
4. El mundo es FINITO, del mismo tamano que la grilla de entrada. No hay \
wrap-around: toda celda fuera de los limites de la grilla se considera \
muerta siempre, para siempre.
5. Reglas estandar de Conway por generacion, aplicadas simultaneamente a \
toda la grilla (no in-place secuencial):
   - Una celula viva con 2 o 3 vecinas vivas (de las 8 adyacentes) sigue viva.
   - Una celula viva con menos de 2 o mas de 3 vecinas vivas muere.
   - Una celula muerta con exactamente 3 vecinas vivas nace.
6. Con `generaciones = 0`, el script imprime el estado inicial exactamente \
como vino en el archivo (sin recalcular nada).
7. Tras calcular la generacion N, el script imprime por stdout la grilla \
resultante en el mismo formato de entrada (una linea por fila, `#`/`.`), \
sin lineas en blanco extra antes, en medio o al final, sin ningun otro \
texto (nada de logs, nada de "Resultado:", nada de barras de progreso).
8. Solo biblioteca estandar de Python (nada de numpy ni paquetes externos).
9. El script debe terminar con exit code 0 en todos los casos validos.

# Restricciones

- No agregues manejo de errores para casos que no se piden (no hace falta \
validar que el archivo exista, ni que la grilla sea rectangular): asumi \
input valido segun el contrato de arriba.
- No imprimas nada que no sea la grilla final. Ni un print de debug.
- No uses wrap-around (toroide). Es finito, con bordes muertos.

# Ejemplos

## Ejemplo 1 — generacion 0 (passthrough)
Archivo de entrada:
```
.....
..#..
..#..
..#..
.....
```
`python3 vida.py estado.txt 0` imprime exactamente lo mismo:
```
.....
..#..
..#..
..#..
.....
```

## Ejemplo 2 — blinker, oscila de vertical a horizontal en 1 generacion
Entrada (blinker vertical):
```
.....
..#..
..#..
..#..
.....
```
`python3 vida.py estado.txt 1` imprime (blinker horizontal):
```
.....
.....
.###.
.....
.....
```
Y con `generaciones=2` vuelve a la forma vertical original.

## Ejemplo 3 — bloque, naturaleza muerta (no cambia nunca)
Entrada:
```
....
.##.
.##.
....
```
`python3 vida.py estado.txt 5` imprime exactamente lo mismo (bloque estable).

## Ejemplo 4 — celula aislada muere por soledad
Entrada:
```
...
.#.
...
```
`python3 vida.py estado.txt 1` imprime:
```
...
...
...
```

## Ejemplo 5 — nacimiento por exactamente 3 vecinas
Entrada:
```
....
.##.
.#..
....
```
`python3 vida.py estado.txt 1` imprime:
```
....
.##.
.##.
....
```

## Ejemplo 6 — sin wrap-around: un blinker pegado al borde superior
Entrada:
```
###
...
...
```
`python3 vida.py estado.txt 1` imprime (las celulas "de afuera" del borde \
superior estan muertas, asi que el comportamiento difiere de un mundo con \
wrap):
```
.#.
.#.
...
```
'''


def pedido_final(intento: int) -> str:
    """La parte VARIABLE del prompt (va al final, despues del contexto
    estatico). Cambia de texto entre intentos descartados (nunca se corrige el
    codigo a mano), pero el contrato que transmite es siempre el mismo.
    """
    if intento == 1:
        return (
            "# Input\n\n"
            "Generá el archivo `vida.py` completo, listo para ejecutar, "
            "que cumpla exactamente la especificación de arriba. "
            "Respondé solo con el código del archivo, sin explicaciones "
            "antes ni después, sin markdown ni bloques de código extra: "
            "el contenido completo de `vida.py` y nada más."
        )
    return (
        "# Input\n\n"
        f"(Intento {intento} — prompt reescrito desde cero tras un intento "
        "descartado, el contrato de arriba no cambió)\n\n"
        "Generá el archivo `vida.py` completo desde cero, listo para "
        "ejecutar, que cumpla exactamente la especificación de arriba. "
        "Prestá atención especial a: aplicar las reglas de forma "
        "simultánea a toda la grilla (no in-place), no imprimir nada más "
        "que la grilla final, y no usar wrap-around en los bordes. "
        "Respondé solo con el código del archivo, sin explicaciones ni "
        "markdown: el contenido completo de `vida.py` y nada más."
    )
