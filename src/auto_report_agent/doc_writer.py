from __future__ import annotations

import re
from pathlib import Path

from docx import Document

PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def extract_placeholders(docx_path: str) -> dict[str, str]:
    doc = Document(docx_path)
    found: dict[str, str] = {}

    for p in doc.paragraphs:
        text = p.text or ""
        for match in PLACEHOLDER_RE.finditer(text):
            key = match.group(1)
            found.setdefault(key, text.strip())

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text = cell.text or ""
                for match in PLACEHOLDER_RE.finditer(text):
                    key = match.group(1)
                    found.setdefault(key, text.strip())

    return found


def fill_docx_template(docx_input: str, docx_output: str, replacements: dict[str, str]) -> None:
    doc = Document(docx_input)

    def replace_text(text: str) -> str:
        for key, value in replacements.items():
            text = text.replace(f"{{{{{key}}}}}", value)
        return text

    for p in doc.paragraphs:
        if p.text:
            p.text = replace_text(p.text)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text:
                    cell.text = replace_text(cell.text)

    output_path = Path(docx_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
