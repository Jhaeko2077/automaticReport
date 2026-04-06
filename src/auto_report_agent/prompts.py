from __future__ import annotations

import json


def build_document_prompt(
    repo_context: str,
    questions: list[str],
    include_summary: bool,
    include_diagram: bool,
    placeholders: dict[str, str],
    student_profile: dict[str, str] | None = None,
) -> str:
    questions_json = json.dumps(questions, ensure_ascii=False, indent=2)
    placeholders_json = json.dumps(placeholders, ensure_ascii=False, indent=2)

    summary_instruction = (
        '"summary": "Escribe una propuesta de solución completa (mínimo 800 palabras) en español, '
        'con redacción clara, profesional y persuasiva. Debe presentar el repositorio analizado como '
        'una solución técnica integral, explicando de forma amplia y ordenada: (1) contexto y problema '
        'que aborda, (2) arquitectura y componentes principales del proyecto, (3) flujo de ejecución del agente, '
        '(4) tecnologías y por qué fueron elegidas, (5) valor práctico para el usuario/negocio, '
        '(6) plan de implementación o mejora continua y (7) resultados/evidencias esperadas. '
        'No la enfoques como un simple resumen; debe sonar a propuesta formal de solución basada en el código real.",'
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
    student_profile_json = json.dumps(student_profile or {}, ensure_ascii=False, indent=2)

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
    {{"question": "pregunta original 1", "answer": "respuesta técnica en español (mínimo 4 párrafos densos) basada en el código"}},
    {{"question": "pregunta original 2", "answer": "respuesta técnica en español (mínimo 4 párrafos densos) basada en el código"}}
  ],
  "fields": {{
    "PLACEHOLDER_EJEMPLO": "valor completado"
  }},
  "sections": {{
    "student_name": "nombre completo del estudiante",
    "student_id": "id del estudiante",
    "student_address": "dirección zonal/cfp",
    "student_career": "carrera",
    "student_course": "curso o módulo formativo",
    "student_topic": "tema del trabajo final (debe derivarse del repositorio)",
    "problem_statement": "problemática del caso práctico",
    "solution_evidence": "propuesta de solución y evidencias",
    "schedule": "cronograma de actividades en texto tabular",
    "machines_equipment": "máquinas y equipos con cantidades",
    "tools_instruments": "herramientas e instrumentos con cantidades",
    "materials_supplies": "materiales e insumos con cantidades",
    "solution_proposal": "propuesta de solución consolidada",
    "operations_steps": "operaciones/pasos/subpasos",
    "standards_safety_environment": "normas técnicas/seguridad/medio ambiente",
    "textual_diagram": "diagrama textual del flujo de trabajo",
    "compliance_control": "control de cumplimiento (cumple/no cumple + evidencia)",
    "evaluation_scores": "valoración con puntajes y justificación"
  }}
}}

EJEMPLO de respuesta correcta para una pregunta:
{{
  "question": "¿Cómo seleccionar un dataset adecuado para un problema de Machine Learning?",
  "answer": "Para seleccionar un dataset adecuado para Machine Learning se deben evaluar múltiples dimensiones de calidad. En primer lugar, la representatividad: el dataset debe cubrir todos los escenarios reales que el modelo enfrentará en producción, incluyendo casos borde y distribuciones minoritarias que suelen ser críticas para el rendimiento final.\n\nEn segundo lugar, el volumen de datos es determinante. Modelos simples como regresión logística pueden funcionar con cientos de muestras, mientras que redes neuronales profundas típicamente requieren decenas de miles o más. Una heurística común es tener al menos 10 veces más ejemplos que parámetros entrenables del modelo.\n\nEn tercer lugar, la calidad de las etiquetas y la ausencia de sesgos sistémicos. Un dataset grande pero mal etiquetado producirá un modelo sesgado de forma consistente (garbage in, garbage out). Se recomienda auditar una muestra aleatoria manualmente antes de entrenar.\n\nFinalmente, se debe considerar el balance de clases. En problemas de clasificación con clases desbalanceadas, técnicas como oversampling (SMOTE), undersampling o ajuste de class_weight son necesarias para evitar que el modelo ignore las clases minoritarias."
}}

Preguntas a responder (exactamente {n}):
{questions_json}

Placeholders a completar:
{placeholders_json}

Datos del estudiante que debes respetar literalmente en la sección "sections" (excepto student_topic, que debe ser inferido):
{student_profile_json}

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
3. Cada respuesta debe tener mínimo 4 párrafos densos en español técnico.
4. Incluye en cada respuesta: (1) definición del concepto, (2) relación explícita con el código del repositorio, (3) justificación técnica detallada y (4) ejemplos concretos o casos de uso.
5. Conserva el texto exacto de cada pregunta en el campo "question".

El JSON de salida debe tener exactamente {n} elementos en "question_answers":

{example_structure}

Preguntas (responde las {n} sin excepción):
{questions_json}

CÓDIGO FUENTE DEL REPOSITORIO:
{repo_context}

Responde ÚNICAMENTE con el JSON final. Sin markdown, sin explicaciones previas, sin bloques de código.
""".strip()
