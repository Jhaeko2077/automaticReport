from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path

from docx import Document

PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
QUESTION_RE = re.compile(r"pregunta\s*\d+\s*[:：]", re.IGNORECASE)


@dataclass
class QuestionSlot:
    question: str
    table_idx: int
    question_row_idx: int
    answer_row_idx: int
    col_idx: int


@dataclass
class DocAnalysis:
    placeholders: dict[str, str]
    questions: list[QuestionSlot]
    has_summary_section: bool
    has_diagram_section: bool


def _normalize(text: str) -> str:
    return " ".join(text.split()).strip().lower()


def _strip_question_label(text: str) -> str:
    return QUESTION_RE.sub("", text).strip()


def _is_question_text(text: str) -> bool:
    normalized = _normalize(text)
    return "pregunta" in normalized and "?" in normalized


def analyze_docx(docx_path: str) -> DocAnalysis:
    doc = Document(docx_path)
    placeholders: dict[str, str] = {}
    questions: list[QuestionSlot] = []
    has_summary_section = False
    has_diagram_section = False


def extract_placeholders(docx_path: str) -> dict[str, str]:
    doc = Document(docx_path)
    found: dict[str, str] = {}

    for p in doc.paragraphs:
        text = p.text or ""
        for match in PLACEHOLDER_RE.finditer(text):
            key = match.group(1)
            placeholders.setdefault(key, text.strip())

    for table_idx, table in enumerate(doc.tables):
        for row_idx, row in enumerate(table.rows):
            for col_idx, cell in enumerate(row.cells):
                text = (cell.text or "").strip()
                for match in PLACEHOLDER_RE.finditer(text):
                    key = match.group(1)
                    placeholders.setdefault(key, text)

                normalized = _normalize(text)
                if normalized.startswith("resumen"):
                    has_summary_section = True
                if normalized.startswith("diagrama"):
                    has_diagram_section = True

                if _is_question_text(text) and row_idx + 1 < len(table.rows):
                    answer_cell = table.rows[row_idx + 1].cells[col_idx]
                    answer_text = (answer_cell.text or "").strip()
                    if not _is_question_text(answer_text):
                        questions.append(
                            QuestionSlot(
                                question=_strip_question_label(text),
                                table_idx=table_idx,
                                question_row_idx=row_idx,
                                answer_row_idx=row_idx + 1,
                                col_idx=col_idx,
                            )
                        )

    return DocAnalysis(
        placeholders=placeholders,
        questions=questions,
        has_summary_section=has_summary_section,
        has_diagram_section=has_diagram_section,
    )
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


def fill_docx_sections(
    docx_input: str,
    docx_output: str,
    question_answers: list[str],
    summary: str | None,
    diagram: str | None,
    placeholder_replacements: dict[str, str] | None = None,
) -> None:
    doc = Document(docx_input)

    if placeholder_replacements:
        def replace_text(text: str) -> str:
            for key, value in placeholder_replacements.items():
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

    q_idx = 0
    for table in doc.tables:
        for row_idx, row in enumerate(table.rows):
            for col_idx, cell in enumerate(row.cells):
                text = (cell.text or "").strip()
                normalized = _normalize(text)

                if _is_question_text(text) and row_idx + 1 < len(table.rows) and q_idx < len(question_answers):
                    answer_cell = table.rows[row_idx + 1].cells[col_idx]
                    answer_cell.text = question_answers[q_idx]
                    q_idx += 1

                if summary and normalized.startswith("resumen"):
                    cell.text = f"Resumen\n\n{summary.strip()}"

                if diagram and normalized.startswith("diagrama"):
                    cell.text = f"Diagrama\n\n{diagram.strip()}"

    output_path = Path(docx_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
