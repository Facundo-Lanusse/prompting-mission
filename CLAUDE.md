# CLAUDE.md — reglas de trabajo del repositorio

Este repositorio contiene **dos cosas de naturaleza distinta**, y no hay que
mezclarlas:

1. **La interfaz de chat** (`src/`, `tests/test_chat_cli.py`): código propio.
   Acá se itera, se refactoriza y se corrige, con TDD e historia de commits
   limpia.
2. **`vida.py`**: entra al repositorio tal cual salió del chat con el modelo
   del slot 4. **Nunca se edita a mano.** Si algo está mal, se reescribe el
   prompt en `src/prompt_vida.py` y se corre `run_ejercicio2.py` de nuevo en
   una conversación nueva; no se toca el `.py` generado. El valor del
   resultado depende de que el script entregado coincida exactamente con el
   que aparece en el log ganador.

## Reglas

- `tests/test_vida.py` es la batería de aceptación de referencia: **no se
  modifica, nunca**.
- Los logs en `logs/` son evidencia de auditoría: no se editan después de
  generados y no se borran las corridas fallidas.
- El contexto estático de `src/prompt_vida.py` debe quedar **idéntico** entre
  todas las corridas; solo cambia la parte variable del final. Esa
  invariante es la que habilita el caching por prefijo.
- `reports/informe-de-consumo.md` reconcilia con los números reales de
  `logs/`: se copian los valores de usage tal cual los devolvió la API, sin
  estimar ni redondear.
- Nunca commitear `.env` (contiene la API key). `.env.example` es la
  plantilla.

## Comandos

```bash
pip install -r requirements.txt
cp .env.example .env                  # pegar OPENROUTER_API_KEY

python3 src/chat_cli.py               # chat interactivo
python3 src/run_ejercicio2.py         # generación scripteada de vida.py

python3 tests/test_vida.py vida.py                            # 9 tests de aceptación
python3 -m unittest discover -s tests -p 'test_chat_cli.py'   # 14 tests de la interfaz
```

Diseño de la interfaz: [`SPEC.md`](SPEC.md). Setup, resultados e
investigación previa: [`README.md`](README.md).
