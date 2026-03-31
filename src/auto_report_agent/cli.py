from __future__ import annotations

import argparse
import sys

from .doc_writer import analyze_docx, fill_docx_sections
from .ollama_client import OllamaClient
from .prompts import build_document_prompt
from .doc_writer import extract_placeholders, fill_docx_template
from .ollama_client import OllamaClient
from .prompts import build_placeholder_prompt
from .repo_analyzer import build_repo_context


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Completa una plantilla DOCX analizando un repositorio con Ollama local."
    )
    parser.add_argument("--repo-path", required=True, help="Ruta del repositorio a analizar")
    parser.add_argument("--docx-input", required=True, help="Documento DOCX de entrada")
    parser.add_argument("--docx-input", required=True, help="Plantilla DOCX con placeholders {{...}}")
    parser.add_argument("--docx-output", required=True, help="Ruta del DOCX de salida")
    parser.add_argument("--model", default="llama3", help="Modelo en Ollama (default: llama3)")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="URL base de Ollama")
    parser.add_argument("--max-files", type=int, default=25, help="Cantidad máxima de archivos de muestra")
    parser.add_argument(
        "--max-file-chars",
        type=int,
        default=3000,
        help="Máximo de caracteres por archivo de muestra",
    )
    parser.add_argument("--commit-limit", type=int, default=20, help="Cantidad de commits recientes")
    parser.add_argument(
        "--read-all-code",
        action="store_true",
        help="Lee todos los archivos de código soportados del repositorio (puede tardar más).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    analysis = analyze_docx(args.docx_input)
    questions = [slot.question for slot in analysis.questions]

    if not questions and not analysis.placeholders and not analysis.has_summary_section and not analysis.has_diagram_section:
        print("No se detectaron preguntas, placeholders, resumen ni diagrama en el DOCX.")
        return 2

    print(
        f"[1/4] Detectado en DOCX -> preguntas: {len(questions)}, "
        f"placeholders: {len(analysis.placeholders)}, "
        f"resumen: {analysis.has_summary_section}, diagrama: {analysis.has_diagram_section}"
    )

    repo_context = build_repo_context(
        repo_path=args.repo_path,
        max_files=0 if args.read_all_code else args.max_files,
    placeholders = extract_placeholders(args.docx_input)
    if not placeholders:
        print("No se encontraron placeholders {{...}} en el DOCX de entrada.")
        return 2

    print(f"[1/4] Placeholders detectados: {len(placeholders)}")
    repo_context = build_repo_context(
        repo_path=args.repo_path,
        max_files=args.max_files,
        max_file_chars=args.max_file_chars,
        commit_limit=args.commit_limit,
    )
    print("[2/4] Contexto del repositorio recopilado")

    prompt = build_document_prompt(
        repo_context=repo_context.to_prompt_context(),
        questions=questions,
        include_summary=analysis.has_summary_section,
        include_diagram=analysis.has_diagram_section,
        placeholders=analysis.placeholders,
    )

    client = OllamaClient(base_url=args.ollama_url, model=args.model)
    print(f"[3/4] Solicitando generación al modelo '{args.model}'...")
    llm_result = client.generate_json(prompt)

    qa_items = llm_result.get("question_answers", [])
    question_answers: list[str] = []
    if isinstance(qa_items, list):
        for item in qa_items:
            if isinstance(item, dict):
                question_answers.append(str(item.get("answer", "")).strip())

    summary = str(llm_result.get("summary", "")).strip() or None
    diagram = str(llm_result.get("diagram", "")).strip() or None
    fields = llm_result.get("fields", {})
    if not isinstance(fields, dict):
        fields = {}

    if questions and not question_answers:
        print("El modelo no devolvió respuestas de preguntas en 'question_answers'.")
        return 3

    while len(question_answers) < len(questions):
        question_answers.append("Respuesta no generada por el modelo.")

    placeholder_replacements = {k: str(fields.get(k, "")) for k in analysis.placeholders.keys()}

    fill_docx_sections(
        docx_input=args.docx_input,
        docx_output=args.docx_output,
        question_answers=question_answers,
        summary=summary,
        diagram=diagram,
        placeholder_replacements=placeholder_replacements,
    )
    prompt = build_placeholder_prompt(repo_context.to_prompt_context(), placeholders)
    client = OllamaClient(base_url=args.ollama_url, model=args.model)

    print(f"[3/4] Solicitando generación al modelo '{args.model}'...")
    llm_result = client.generate_json(prompt)
    fields = llm_result.get("fields")

    if not isinstance(fields, dict):
        print("La respuesta del modelo no incluye un objeto 'fields' válido.")
        return 3

    replacements = {key: str(fields.get(key, "")) for key in placeholders.keys()}
    fill_docx_template(args.docx_input, args.docx_output, replacements)

    print(f"[4/4] Documento generado: {args.docx_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
