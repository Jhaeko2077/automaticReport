from __future__ import annotations

import json


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
