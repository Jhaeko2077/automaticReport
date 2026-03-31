from __future__ import annotations

import argparse
import sys

from .doc_writer import extract_placeholders, fill_docx_template
from .ollama_client import OllamaClient
from .prompts import build_placeholder_prompt
from .repo_analyzer import build_repo_context


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Completa una plantilla DOCX analizando un repositorio con Ollama local."
    )
    parser.add_argument("--repo-path", required=True, help="Ruta del repositorio a analizar")
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()

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
