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


def _label_matches_cell(label: str, normalized_text: str, key: str) -> bool:
    if key == "student_id":
        return normalized_text.startswith("id:") or normalized_text == "id"
    return label in normalized_text


def _strip_question_label(text: str) -> str:
    return QUESTION_RE.sub("", text).strip()


def _is_question_text(text: str) -> bool:
    normalized = _normalize(text)
    return "pregunta" in normalized and "?" in normalized


def _extract_question_from_row(row) -> tuple[str | None, int]:
    row_cells = [(cell.text or "").strip() for cell in row.cells]
    row_text = " ".join(part for part in row_cells if part)
    if not row_text:
        return None, 0

    match = QUESTION_RE.search(row_text)
    if not match:
        return None, 0

    question = row_text[match.end() :].strip()
    if not question:
        return None, 0

    # Intentamos ubicar la columna más probable para la respuesta.
    # Prioridad: celda con signo de pregunta, luego celda con texto más largo.
    col_idx = 0
    cells_with_q = [idx for idx, cell_text in enumerate(row_cells) if "?" in cell_text]
    if cells_with_q:
        col_idx = cells_with_q[0]
    else:
        non_empty_cells = [(idx, len(text)) for idx, text in enumerate(row_cells) if text]
        if non_empty_cells:
            col_idx = max(non_empty_cells, key=lambda item: item[1])[0]

    return question, col_idx


def analyze_docx(docx_path: str) -> DocAnalysis:
    doc = Document(docx_path)
    placeholders: dict[str, str] = {}
    questions: list[QuestionSlot] = []
    has_summary_section = False
    has_diagram_section = False

    for p in doc.paragraphs:
        text = p.text or ""
        for match in PLACEHOLDER_RE.finditer(text):
            key = match.group(1)
            placeholders.setdefault(key, text.strip())

    for table_idx, table in enumerate(doc.tables):
        for row_idx, row in enumerate(table.rows):
            row_question, row_col_idx = _extract_question_from_row(row)
            if row_question and row_idx + 1 < len(table.rows):
                answer_cell = table.rows[row_idx + 1].cells[row_col_idx]
                answer_text = (answer_cell.text or "").strip()
                next_row_question, _ = _extract_question_from_row(table.rows[row_idx + 1])
                if not _is_question_text(answer_text) and not next_row_question:
                    questions.append(
                        QuestionSlot(
                            question=row_question,
                            table_idx=table_idx,
                            question_row_idx=row_idx,
                            answer_row_idx=row_idx + 1,
                            col_idx=row_col_idx,
                        )
                    )

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

                # Compatibilidad adicional: pregunta contenida íntegramente en una sola celda.
                if _is_question_text(text) and row_idx + 1 < len(table.rows):
                    answer_cell = table.rows[row_idx + 1].cells[col_idx]
                    answer_text = (answer_cell.text or "").strip()
                    if not _is_question_text(answer_text):
                        question_text = _strip_question_label(text)
                        if not any(
                            q.table_idx == table_idx and q.question_row_idx == row_idx and q.col_idx == col_idx
                            for q in questions
                        ):
                            questions.append(
                                QuestionSlot(
                                    question=question_text,
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


def extract_placeholders(docx_path: str) -> dict[str, str]:
    return analyze_docx(docx_path).placeholders


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
    extra_sections: dict[str, str] | None = None,
) -> None:
    doc = Document(docx_input)
    analysis = analyze_docx(docx_input)

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

    for q_idx, slot in enumerate(analysis.questions):
        if q_idx >= len(question_answers):
            break
        table = doc.tables[slot.table_idx]
        answer_cell = table.rows[slot.answer_row_idx].cells[slot.col_idx]
        answer_cell.text = question_answers[q_idx]

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text = (cell.text or "").strip()
                normalized = _normalize(text)

                if summary and normalized.startswith("resumen"):
                    cell.text = f"Resumen\n\n{summary.strip()}"

                if diagram and normalized.startswith("diagrama"):
                    cell.text = f"Diagrama\n\n{diagram.strip()}"

    section_map = {
        "apellidos y nombres": "student_name",
        "id": "student_id",
        "dirección zonal/cfp": "student_address",
        "direccion zonal/cfp": "student_address",
        "carrera": "student_career",
        "curso/ mod. formativo": "student_course",
        "curso/mod. formativo": "student_course",
        "tema de trabajo final": "student_topic",
        "identifica la problemática del caso práctico propuesto": "problem_statement",
        "identifica propuesta de solución y evidencias": "solution_evidence",
        "cronograma de actividades": "schedule",
        "máquinas y equipos": "machines_equipment",
        "maquinas y equipos": "machines_equipment",
        "herramientas e instrumentos": "tools_instruments",
        "materiales e insumos": "materials_supplies",
        "propuesta de solución": "solution_proposal",
        "operaciones / pasos / subpasos": "operations_steps",
        "normas técnicas": "standards_safety_environment",
        "normas tecnicas": "standards_safety_environment",
        "dibujo / esquema / diagrama de propuesta": "textual_diagram",
        "verificar el cumplimiento": "compliance_control",
        "califica el impacto": "evaluation_scores",
    }

    if extra_sections:
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    raw_text = (cell.text or "").strip()
                    if not raw_text:
                        continue
                    normalized = _normalize(raw_text)

                    for label, key in section_map.items():
                        if label in normalized and extra_sections.get(key):
                            value = str(extra_sections[key]).strip()
                            if not value:
                                continue

                            # Campos de estudiante: mantener etiqueta y completar en la misma celda.
                            if key.startswith("student_"):
                                first_line = raw_text.splitlines()[0].strip()
                                if ":" in first_line:
                                    prefix = first_line.split(":", 1)[0].strip()
                                else:
                                    prefix = first_line
                                cell.text = f"{prefix}: {value}"
                            else:
                                # Secciones amplias: mantener encabezado y añadir contenido.
                                if value not in raw_text:
                                    cell.text = f"{raw_text}\n\n{value}"
                            break

    output_path = Path(docx_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
