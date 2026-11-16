# Semáforo Amigo 🚦

Trabajo final «Voces que Importan» (NLP e IA agéntica). Agente conversacional en Chainlit que ayuda a
chicos y chicas de 8 años a entender **qué tan seria es una situación de la escuela** (verde, amarillo o
rojo) y les da **tres pasos simples**. Informa, acompaña y deriva a un adulto: no diagnostica.

## Cómo correrlo

Requiere Python 3.11 o superior (probado con 3.13).

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # y pegar la GROQ_API_KEY
python -m scripts.entrenar_nlp                         # entrena los clasificadores (ya vienen entrenados)
python -m scripts.construir_indice                     # después de bajar los PDF (ver docs/LEEME.md)
chainlit run app.py -w
```

La primera vez, `construir_indice` descarga el modelo de embeddings (unos 220 MB).

## Arquitectura

```
mensaje
  │
  ├─ 1. Guardrail (src/guardrail.py)  patrones de riesgo ──► respuesta fija + líneas de ayuda (el LLM no responde)
  ├─ 2. ¿Pide teléfonos? ──► tarjeta fija con las líneas verificadas
  ├─ 3. analizar_situacion (src/nlp.py)  tema · intención · sentimiento · semáforo
  ├─ 4. Agente LangChain + Groq (src/agente.py), memoria de 6 mensajes
  │        ├─ consultar_evidencia  RAG sobre docs/ con Chroma + embeddings multilingües, devuelve cita
  │        └─ orientar_recursos    líneas verificadas de data/recursos.json
  └─ 5. Tarjeta (app.py): mascota + color + 3 pasos + bloque «para el adulto que acompaña» con fuentes
```

| Requisito de la consigna | Dónde está |
|---|---|
| Chainlit | `app.py`, `public/` (tema, CSS, mascota animada, guía de colores), preguntas pregrabadas |
| NLP con métricas | `src/nlp.py`, `scripts/entrenar_nlp.py`, `metricas/nlp.json` |
| LangChain + LLM + memoria corta | `src/agente.py` |
| RAG + embeddings con cita | `src/rag.py`, `scripts/construir_indice.py`, `scripts/evaluar_rag.py` |
| 3 herramientas | `src/herramientas.py` |
| Seguridad | `src/guardrail.py`, `scripts/prueba_seguridad.py`, `metricas/prueba_seguridad.md` |
| Latencia | `metricas/latencias.csv` (se llena al usar la app; no guarda el texto) |

## Decisiones de diseño

- **El guardrail no depende del sentimiento.** Corre antes que todo y, si salta, la respuesta es fija.
- **`analizar_situacion` corre siempre**, no a criterio del LLM. Las otras dos herramientas las decide el agente.
- **El semáforo es el máximo entre el clasificador y reglas simples**, para no subestimar una situación.
  Describe la situación, no a la persona.
- **Los teléfonos nunca los escribe el LLM de memoria**: salen de `data/recursos.json`, cada uno con su fuente.
- **Dos niveles de lectura**: arriba, texto corto para el chico; abajo, detalle y fuentes para el adulto.

## Métricas actuales del NLP

Validación cruzada de 5 particiones sobre 162 frases ficticias (`data/dataset.csv`):

| Etiqueta | Accuracy | F1 macro |
|---|---|---|
| Tema | 0,70 | 0,71 |
| Intención | 0,68 | 0,51 |
| Sentimiento | 0,69 | 0,58 |
| Semáforo (solo modelo) | 0,70 | 0,63 |
| Semáforo (modelo + reglas) | 0,74 | 0,71 |

Recall de la clase rojo: 0,57 con el modelo solo y 0,76 con reglas. Para mejorar: sumar frases al dataset
(sobre todo de intención `pedir_ayuda` y `ayudar_a_otro`) y volver a entrenar.

## Limitaciones

- Dataset chico y escrito por el equipo: las métricas son orientativas.
- El guardrail es por patrones: puede cortar de más («me quiero morir de vergüenza») y puede no detectar
  formas de decirlo que no previmos.
- Líneas de ayuda solo para Argentina; algunas tienen verificaciones pendientes (campo `pendiente` del JSON).
- No reemplaza a un adulto ni a un profesional, y no atiende emergencias.

## Pruebas sin API key

```bash
python -m tests.probar_todo         # guardrail, NLP, recursos, RAG y agente con LLM simulado
python -m scripts.prueba_seguridad  # genera metricas/prueba_seguridad.md
```
