from __future__ import annotations

import json


def build_document_prompt(
    repo_context: str,
    questions: list[str],
    include_summary: bool,
    include_diagram: bool,
    placeholders: dict[str, str],
) -> str:
    questions_json = json.dumps(questions, ensure_ascii=False, indent=2)
    placeholders_json = json.dumps(placeholders, ensure_ascii=False, indent=2)

    summary_instruction = (
        '"summary": "Escribe aquí un resumen completo del proyecto (mínimo 250 palabras). '
        'Describe su propósito, arquitectura, tecnologías usadas y flujo principal.",'
        if include_summary
        else '"summary": "",'
    )

    diagram_instruction = (
        '"diagram": "Escribe aquí un diagrama Mermaid válido usando flowchart TD '
        'que muestre la arquitectura o flujo principal del proyecto.",'
        if include_diagram
        else '"diagram": "",'
    )

    n = len(questions)

    return f"""Eres un arquitecto de software senior. Tu única tarea es analizar el código fuente de un repositorio y responder preguntas técnicas sobre él.

PROHIBIDO ABSOLUTO:
- No menciones commits, hashes, fechas de commits, autores de commits, ramas de git, ni historial de versiones.
- No respondas con información de git log, git blame, ni git show.
- No uses la palabra "commit" en ninguna respuesta.
- No inventes librerías ni archivos que no estén en el contexto.
- No escribas texto fuera del JSON.

TAREA:
Analiza el código fuente del repositorio y devuelve EXACTAMENTE este JSON válido:

{{
  {summary_instruction}
  {diagram_instruction}
  "question_answers": [
    {{"question": "pregunta original 1", "answer": "respuesta técnica de 1-2 párrafos basada en el código"}},
    {{"question": "pregunta original 2", "answer": "respuesta técnica de 1-2 párrafos basada en el código"}}
  ],
  "fields": {{
    "PLACEHOLDER_EJEMPLO": "valor completado"
  }}
}}

EJEMPLO de respuesta correcta para una pregunta:
{{
  "question": "¿Cómo seleccionar un dataset adecuado para un problema de Machine Learning?",
  "answer": "Para seleccionar un dataset adecuado se deben considerar tres criterios principales: representatividad, volumen y calidad. El dataset debe reflejar con precisión el fenómeno que se desea modelar, incluyendo todos los casos borde relevantes. En cuanto al volumen, reglas empíricas sugieren al menos 10 veces más muestras que parámetros del modelo. Finalmente, la calidad implica ausencia de valores nulos excesivos, etiquetas correctas y distribución balanceada entre clases."
}}

Preguntas a responder (exactamente {n}):
{questions_json}

Placeholders a completar:
{placeholders_json}

CÓDIGO FUENTE DEL REPOSITORIO:
{repo_context}

Responde ÚNICAMENTE con el JSON final. Sin explicaciones, sin texto adicional, sin bloques de código markdown.
""".strip()


def build_placeholder_prompt(repo_context: str, placeholders: dict[str, str]) -> str:
    placeholders_json = json.dumps(placeholders, ensure_ascii=False, indent=2)
    placeholder_keys = list(placeholders.keys())

    return f"""Eres un asistente técnico senior. Analiza el código fuente de un repositorio y completa los campos indicados.

PROHIBIDO:
- No menciones commits, git log, hashes ni historial de versiones.
- No inventes archivos o librerías que no estén en el contexto.
- No escribas nada fuera del JSON.

TAREA:
Devuelve exactamente este JSON con los placeholders completados:

{{
  "fields": {{
    "NOMBRE_PLACEHOLDER": "contenido completado aquí"
  }}
}}

Claves que DEBES incluir obligatoriamente: {json.dumps(placeholder_keys, ensure_ascii=False)}

Regla especial: si una clave contiene la palabra DIAGRAM, escribe un diagrama Mermaid válido (flowchart TD).

Contexto de cada placeholder (clave -> contexto):
{placeholders_json}

CÓDIGO FUENTE DEL REPOSITORIO:
{repo_context}

Responde ÚNICAMENTE con el JSON. Sin texto adicional.
""".strip()


def build_question_only_prompt(repo_context: str, questions: list[str]) -> str:
    questions_json = json.dumps(questions, ensure_ascii=False, indent=2)
    n = len(questions)

    example_structure = json.dumps(
        {
            "question_answers": [
                {
                    "question": f"<pregunta {i + 1} exactamente como está>",
                    "answer": f"<respuesta técnica {i + 1} en español>",
                }
                for i in range(n)
            ]
        },
        ensure_ascii=False,
        indent=2,
    )

    return f"""Eres un arquitecto de software senior. Analiza el código fuente del repositorio y responde las preguntas técnicas.

PROHIBIDO ABSOLUTO:
- No menciones commits, hashes, fechas de commits, autores ni ramas de git.
- No uses la palabra "commit" en ninguna respuesta.
- No respondas con información de git log ni historial de versiones.
- No escribas texto fuera del JSON.
- No omitas ninguna pregunta.

INSTRUCCIONES:
1. Lee el código fuente del repositorio.
2. Responde cada pregunta basándote exclusivamente en el código, la arquitectura y las tecnologías presentes.
3. Cada respuesta debe tener 1-2 párrafos en español técnico y claro.
4. Conserva el texto exacto de cada pregunta en el campo "question".

El JSON de salida debe tener exactamente {n} elementos en "question_answers":

{example_structure}

Preguntas (responde las {n} sin excepción):
{questions_json}

CÓDIGO FUENTE DEL REPOSITORIO:
{repo_context}

Responde ÚNICAMENTE con el JSON final. Sin markdown, sin explicaciones previas, sin bloques de código.
""".strip()
