# CLAUDE.md — prompting-mission

Este repo es la entrega de la misión "el prompt mínimo" (curso IA
Generativa). Contiene **dos cosas de naturaleza distinta** y no hay que
mezclarlas:

1. **La interfaz de chat** (`src/`, `tests/test_chat_cli.py`): código propio,
   con TDD y commits normales. Acá sí se itera, se refactoriza, se corrige.
2. **`vida.py`**: entra al repo tal cual salió del chat con el modelo del
   slot 4. **Nunca se edita a mano.** Si algo está mal, se reescribe el
   prompt en `src/prompt_vida.py` y se corre `run_ejercicio2.py` de nuevo en
   una conversación nueva — no se toca el `.py` generado. La rúbrica de la
   cátedra invalida el ejercicio si el script entregado no coincide con el
   que aparece en el log ganador.

## Reglas de trabajo

- Los tests de la cátedra (`tests/test_vida.py`) **no se modifican, nunca**.
- Los logs de conversación en `logs/` son evidencia de auditoría: no se
  editan a mano después de generados, no se borran los intentos "quemados".
- El contexto estático del prompt de `vida.py` (`src/prompt_vida.py`) tiene
  que quedar **idéntico** entre todos los intentos del Ejercicio 2 — solo
  cambia la parte variable al final. Esto es lo que hace que el caching
  automático de DeepSeek funcione entre corridas.
- Nunca commitear `.env` (tiene la API key). Usar `.env.example` como
  plantilla.
- `reports/ejercicio3.md` tiene que reconciliar con los números reales de
  `logs/ejercicio2/*.md` — no se redondea ni se estima, se copian los
  valores de usage tal cual los devolvió la API.

## Cómo correr esto

```bash
pip install -r requirements.txt
cp .env.example .env  # pegar OPENROUTER_API_KEY
python3 src/chat_cli.py          # Ejercicio 1, interactivo
python3 src/run_ejercicio2.py     # Ejercicio 2, scripteado
python3 tests/test_vida.py vida.py
python3 -m unittest tests/test_chat_cli.py
```

Ver `SPEC.md` para el diseño de la interfaz y `README.md` para el
trabajo previo obligatorio y las instrucciones de setup.
