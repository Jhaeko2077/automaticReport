from __future__ import annotations

import argparse
import sys

from .doc_writer import analyze_docx, fill_docx_sections
from .ollama_client import OllamaClient
from .prompts import build_document_prompt, build_question_only_prompt
from .repo_analyzer import build_repo_context


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Completa una plantilla DOCX analizando un repositorio con Ollama local."
    )
    parser.add_argument("--repo-path", required=True, help="Ruta del repositorio a analizar")
    parser.add_argument("--docx-input", required=True, help="Documento DOCX de entrada")
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
    parser.add_argument(
        "--debug-llm",
        action="store_true",
        help="Imprime en consola información de depuración del JSON devuelto por el modelo.",
    )
    parser.add_argument(
        "--debug-llm-max-chars",
        type=int,
        default=1200,
        help="Máximo de caracteres a imprimir por respuesta cruda del modelo en modo debug.",
    )
    parser.add_argument(
        "--debug-llm-file",
        default="",
        help="Ruta opcional para guardar el contenido crudo devuelto por el modelo.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    def debug_llm_dump(stage: str, payload: dict, raw_text: str, file_path: str = "") -> None:
        if not args.debug_llm:
            return

        print(f"[DEBUG][{stage}] Claves JSON: {sorted(payload.keys()) if isinstance(payload, dict) else 'N/A'}")
        preview = (raw_text or "").strip()
        if not preview:
            preview = "<respuesta vacía>"
        if len(preview) > args.debug_llm_max_chars:
            preview = preview[: args.debug_llm_max_chars] + "...(truncado)"
        print(f"[DEBUG][{stage}] Respuesta cruda (preview): {preview}")

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as handle:
                    handle.write(raw_text or "")
                print(f"[DEBUG][{stage}] Respuesta cruda guardada en: {file_path}")
            except Exception as exc:
                print(f"[DEBUG][{stage}] No se pudo guardar debug en archivo: {exc}")

    analysis = analyze_docx(args.docx_input)
    questions = [slot.question for slot in analysis.questions]

    if (
        not questions
        and not analysis.placeholders
        and not analysis.has_summary_section
        and not analysis.has_diagram_section
    ):
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
    debug_llm_dump(
        stage="initial",
        payload=llm_result,
        raw_text=client.last_raw_response,
        file_path=args.debug_llm_file.strip(),
    )

    def extract_question_answers(payload: dict) -> list[str]:
        answers: list[str] = []

        qa_items = payload.get("question_answers", [])
        if isinstance(qa_items, list):
            for item in qa_items:
                if isinstance(item, dict):
                    answer = str(item.get("answer", "")).strip()
                    if answer:
                        answers.append(answer)
                elif isinstance(item, str) and item.strip():
                    answers.append(item.strip())

        if answers:
            return answers

        alt_items = payload.get("answers", [])
        if isinstance(alt_items, list):
            for item in alt_items:
                if isinstance(item, dict):
                    answer = str(item.get("answer", "")).strip()
                    if answer:
                        answers.append(answer)
                elif isinstance(item, str) and item.strip():
                    answers.append(item.strip())
        if answers:
            return answers

        qa_map = payload.get("qa")
        if isinstance(qa_map, dict):
            for question in questions:
                answer = qa_map.get(question)
                if isinstance(answer, str) and answer.strip():
                    answers.append(answer.strip())
        if answers:
            return answers

        return []

    question_answers = extract_question_answers(llm_result)

    summary = str(llm_result.get("summary", "")).strip() or None
    diagram = str(llm_result.get("diagram", "")).strip() or None
    fields = llm_result.get("fields", {})
    if not isinstance(fields, dict):
        fields = {}

    if questions and len(question_answers) < len(questions):
        print("[3.1/4] Reintento focalizado para recuperar respuestas de preguntas...")
        recovery_prompt = build_question_only_prompt(
            repo_context=repo_context.to_prompt_context(),
            questions=questions,
        )
        recovery_result = client.generate_json(recovery_prompt, temperature=0.1)
        recovery_debug_file = ""
        if args.debug_llm_file.strip():
            recovery_debug_file = f"{args.debug_llm_file}.retry"
        debug_llm_dump(
            stage="retry",
            payload=recovery_result,
            raw_text=client.last_raw_response,
            file_path=recovery_debug_file,
        )
        recovered_answers = extract_question_answers(recovery_result)
        if recovered_answers:
            question_answers = recovered_answers

    if questions and not question_answers:
        if args.debug_llm:
            print(
                "[DEBUG][failure] No se pudieron extraer respuestas. "
                "Activa/usa --debug-llm-file para inspeccionar la salida cruda completa."
            )
        print("El modelo no devolvió respuestas de preguntas ni en el reintento focalizado.")
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

    print(f"[4/4] Documento generado: {args.docx_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
