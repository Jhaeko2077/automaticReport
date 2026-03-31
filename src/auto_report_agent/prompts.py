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

    return f"""
Eres un arquitecto de software senior. Analiza el contexto del repositorio y completa un documento académico.

Reglas estrictas:
1) Responde SOLO JSON válido.
2) Responde en español técnico, claro y detallado.
3) En las respuestas a preguntas usa 1-2 párrafos por pregunta.
4) Si se solicita resumen, debe ser largo y completo (mínimo 250 palabras).
5) Si se solicita diagrama, entrega Mermaid válido (flowchart TD).
6) No inventes librerías/archivos que no estén en el contexto.

Estructura JSON requerida:
{{
  "summary": "texto o cadena vacía",
  "diagram": "texto mermaid o cadena vacía",
  "question_answers": [
    {{"question": "pregunta original", "answer": "respuesta"}}
  ],
  "fields": {{
    "PLACEHOLDER": "valor"
  }}
}}

Preguntas detectadas:
{questions_json}

¿Debe generar resumen?: {str(include_summary).lower()}
¿Debe generar diagrama?: {str(include_diagram).lower()}

Placeholders detectados:
def build_placeholder_prompt(repo_context: str, placeholders: dict[str, str]) -> str:
    placeholders_json = json.dumps(placeholders, ensure_ascii=False, indent=2)
    return f"""
Eres un asistente técnico senior. Tu tarea es completar placeholders de un documento.

Reglas estrictas:
1) Responde SOLO en JSON válido.
2) El JSON de salida debe tener esta forma exacta:
{{
  "fields": {{
    "NOMBRE_PLACEHOLDER": "contenido..."
  }}
}}
3) Debes devolver exactamente los mismos placeholders solicitados.
4) Si un placeholder contiene la palabra DIAGRAM, entrega un diagrama Mermaid (flowchart TD).
5) Responde en español.

Placeholders detectados (clave -> contexto de línea del documento):
{placeholders_json}

Contexto del repositorio:
{repo_context}

Devuelve únicamente el JSON final.
""".strip()
