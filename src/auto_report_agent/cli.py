from __future__ import annotations

import argparse
import json
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
    parser.add_argument(
        "--ollama-timeout",
        type=int,
        default=300,
        help="Timeout in seconds for Ollama responses (default: 300).",
    )
    parser.add_argument("--student-name", default="Jeicob Hiroshi Kuong Chirinos", help="Nombre completo del estudiante")
    parser.add_argument("--student-id", default="1636178", help="ID del estudiante")
    parser.add_argument("--student-address", default="zonal AREQUIPA/PUNO", help="Dirección Zonal/CFP")
    parser.add_argument(
        "--student-career",
        default="Ingeniería de Software con Inteligencia Artificial",
        help="Carrera del estudiante",
    )
    parser.add_argument(
        "--student-course",
        default="FUNDAMENTOS Y ALGORITMIA PARA INTELIGENCIA ARTIFICIAL",
        help="Curso o módulo formativo",
    )
    parser.add_argument("--max-files", type=int, default=25, help="Cantidad máxima de archivos de muestra")
    parser.add_argument(
        "--max-file-chars",
        type=int,
        default=3000,
        help="Máximo de caracteres por archivo de muestra",
    )
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

    def build_practical_answer(question: str) -> str:
        q = question.lower()

        if "dataset" in q and "machine learning" in q:
            return (
                "Para seleccionar un dataset adecuado en Machine Learning conviene partir del objetivo del modelo "
                "(clasificación, regresión, segmentación, ranking, etc.) y traducirlo en variables observables. "
                "Un dataset es útil si representa correctamente el problema real: misma población, mismo contexto y "
                "mismo tipo de decisiones que se tomarán en producción.\n\n"
                "Luego se evalúa calidad de datos: porcentaje de nulos, consistencia de formatos, presencia de "
                "duplicados, ruido en etiquetas y sesgos por muestreo. También importa la cobertura temporal y de "
                "casos extremos; si entrenas con datos “promedio”, el modelo suele fallar en escenarios críticos.\n\n"
                "La selección final debe incluir criterios de viabilidad: tamaño suficiente para entrenar y validar, "
                "coste de mantenimiento, permisos de uso, privacidad y trazabilidad de la fuente. Es mejor un dataset "
                "más pequeño pero confiable y bien documentado, que uno masivo sin control de calidad.\n\n"
                "Como práctica concreta, define una checklist mínima: objetivo, variable objetivo clara, diccionario de "
                "datos, métricas de calidad, partición train/valid/test sin fuga de información y evidencia de que las "
                "clases están representadas de forma razonable."
            )

        if "normalizar" in q or "normalización" in q or "normalizacion" in q:
            return (
                "Normalizar los datos ayuda a que las variables queden en escalas comparables. Sin ese paso, una "
                "columna con valores grandes (por ejemplo miles) puede dominar a otra con valores pequeños (por ejemplo "
                "decimales), afectando el entrenamiento y la interpretación del modelo.\n\n"
                "Es especialmente importante en algoritmos basados en distancia o gradiente, como KNN, SVM, redes "
                "neuronales y regresión logística con regularización. La normalización mejora la estabilidad numérica, "
                "acelera convergencia y reduce comportamientos erráticos durante el ajuste de parámetros.\n\n"
                "Además, al normalizar se facilita comparar coeficientes y detectar variables realmente influyentes. "
                "También reduce el riesgo de que el optimizador quede atrapado por mala escala de entrada.\n\n"
                "Buenas prácticas: ajustar el escalador solo con entrenamiento, aplicar la misma transformación a "
                "validación/prueba y persistir el pipeline completo para inferencia. Esto evita fuga de datos y mantiene "
                "coherencia entre entrenamiento y producción."
            )

        if "varianza" in q or "desviación estándar" in q or "desviacion estandar" in q:
            return (
                "La varianza y la desviación estándar miden dispersión. En términos prácticos, indican cuánta "
                "variabilidad existe en cada variable del dataset y, por tanto, cuánto “ruido” o señal potencial aporta "
                "al modelo.\n\n"
                "Variables con varianza casi nula suelen aportar poco porque cambian muy poco entre observaciones. "
                "En cambio, varianzas extremadamente altas pueden reflejar escalas desbalanceadas o presencia de "
                "outliers que sesgan el entrenamiento.\n\n"
                "En modelos sensibles a escala, una desviación estándar alta puede desestabilizar los pesos aprendidos "
                "si no hay estandarización. En evaluación, alta dispersión en errores también sugiere un modelo "
                "inconsistente: predice bien algunos casos y muy mal otros.\n\n"
                "Como práctica útil, combina análisis de dispersión con selección de variables y estandarización. "
                "Así mejoras robustez, reduces ruido y aumentas la calidad general del modelo en validación y producción."
            )

        if "gráfico" in q or "graficos" in q or "gráficos" in q or "dataset" in q:
            return (
                "Interpretar gráficos estadísticos exige conectar cada visual con una pregunta de negocio/técnica. "
                "Por ejemplo: histogramas para distribución, boxplots para dispersión y outliers, scatter plots para "
                "relaciones entre variables y mapas de calor para correlación.\n\n"
                "En un histograma debes observar sesgo, multimodalidad y colas largas. En boxplots revisa mediana, "
                "rango intercuartílico y puntos fuera de bigotes, porque suelen indicar datos anómalos o subgrupos.\n\n"
                "En gráficos de dispersión conviene identificar linealidad, curvatura y agrupamientos; eso orienta la "
                "elección de modelos y transformaciones. En matrices de correlación, valores altos entre predictores "
                "pueden alertar multicolinealidad.\n\n"
                "Como regla práctica, no interpretes un gráfico aislado: combínalo con estadísticas descriptivas y "
                "conocimiento del dominio para tomar decisiones de limpieza, ingeniería de variables y modelado."
            )

        if "atípicos" in q or "atipicos" in q or "outlier" in q:
            return (
                "Las técnicas más usadas para detectar valores atípicos incluyen métodos univariados y multivariados. "
                "En univariado destacan IQR (regla de 1.5*IQR) y Z-score, que son simples y rápidos para una primera "
                "depuración de columnas numéricas.\n\n"
                "En escenarios multivariados se usan algoritmos como Isolation Forest, Local Outlier Factor (LOF) y "
                "One-Class SVM. Estos capturan mejor anomalías cuando la rareza depende de la combinación de variables "
                "y no de una sola columna.\n\n"
                "También se emplean enfoques robustos como DBSCAN (detecta puntos en baja densidad) o métodos basados "
                "en distancia de Mahalanobis cuando hay correlación entre variables. La elección depende del tamaño del "
                "dataset, dimensionalidad y tipo de distribución.\n\n"
                "Recomendación práctica: detectar, etiquetar y analizar impacto antes de eliminar. Un outlier puede ser "
                "error de captura, pero también un caso real de alto valor para el negocio; por eso conviene tratarlo "
                "con reglas reproducibles dentro de un pipeline."
            )

        return (
            "No se obtuvo respuesta del modelo local a tiempo, así que se entrega una guía práctica para continuar el "
            "avance del informe. Para una respuesta totalmente contextual al repositorio, reintenta con Ollama "
            "disponible y menor carga de contexto.\n\n"
            "Define el objetivo del problema, revisa calidad y distribución de datos, aplica preprocesamiento "
            "consistente (limpieza, codificación, escalado), y valida con métricas apropiadas al tipo de tarea.\n\n"
            "Complementa con análisis de varianza, correlación y detección de valores atípicos para mejorar robustez. "
            "Documenta cada decisión técnica para asegurar trazabilidad.\n\n"
            "Finalmente, compara resultados con y sin cada transformación para justificar técnicamente el pipeline "
            "elegido."
        )

    def build_local_fallback_payload() -> dict:
        fallback_qas = [
            {
                "question": q,
                "answer": build_practical_answer(q),
            }
            for q in questions
        ]
        return {
            "summary": (
                "Se generó una salida de contingencia porque Ollama no respondió a tiempo. "
                "El documento fue completado sin perder estructura y con datos del estudiante. "
                "Para contenido técnico completo, vuelve a ejecutar con mayor timeout y/o menor carga del prompt."
            ),
            "diagram": "flowchart TD\nA[Inicio] --> B[Analizar repositorio]\nB --> C[Completar plantilla]\nC --> D[Generar reporte]",
            "question_answers": fallback_qas,
            "fields": {},
            "sections": {
                "student_name": args.student_name,
                "student_id": args.student_id,
                "student_address": args.student_address,
                "student_career": args.student_career,
                "student_course": args.student_course,
                "student_topic": "Automatización inteligente de reportes técnicos con análisis de repositorios",
                "problem_statement": "Se requiere completar un formato de Trabajo Final a partir del análisis de un repositorio, evitando omisiones y manteniendo consistencia académica.",
                "solution_evidence": "Se implementó un agente que analiza estructura y código del repositorio, consulta un LLM local y escribe en celdas del DOCX por preguntas, resumen, diagrama y secciones clave.",
                "schedule": "Semana 1: análisis de requerimientos\nSemana 2: desarrollo de extracción DOCX\nSemana 3: integración con Ollama\nSemana 4: validación y ajustes",
                "machines_equipment": "Laptop/PC (1)\nConexión de red (1)",
                "tools_instruments": "Python 3.10+ (1)\nOllama local (1)\nEditor de código (1)",
                "materials_supplies": "Plantilla DOCX (1)\nRepositorio objetivo (1)",
                "solution_proposal": "Usar un flujo automatizado de análisis + generación para completar el formato sin alterar el progreso ya alcanzado del proyecto.",
                "operations_steps": "1) Leer plantilla DOCX\n2) Detectar preguntas y secciones\n3) Analizar repositorio\n4) Generar contenido\n5) Rellenar documento\n6) Verificar salida",
                "standards_safety_environment": "Aplicar buenas prácticas de codificación, control de errores, respaldo de archivos y uso eficiente de recursos computacionales.",
                "textual_diagram": "Entrada (Repositorio + Plantilla) -> Análisis -> Generación de contenido -> Escritura DOCX -> Validación",
                "compliance_control": "Cumple parcialmente en modo contingencia; se requiere nueva ejecución con Ollama estable para evidencia técnica completa.",
                "evaluation_scores": "Identificación del problema: 3/3\nRelevancia de la solución: 8/8\nViabilidad técnica: 5/6\nCumplimiento de normas: 3/3\nTotal estimado: 19/20",
            },
        }

    def debug_llm_dump(stage: str, payload: dict, raw_text: str, file_path: str = "") -> None:
        if not args.debug_llm:
            return

        print(f"[DEBUG][{stage}] Claves JSON: {sorted(payload.keys()) if isinstance(payload, dict) else 'N/A'}")
        print(
            f"[DEBUG][{stage}] Parse mode: {client.last_parse_mode} | "
            f"Meta: {client.last_response_meta}"
        )
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

    def print_failure_diagnostics(stage: str, payload: dict, raw_attempts: list[str]) -> None:
        keys = sorted(payload.keys()) if isinstance(payload, dict) else []
        print(f"[ERROR][{stage}] Claves recibidas por el modelo: {keys}")
        if not raw_attempts:
            print(f"[ERROR][{stage}] El modelo devolvió texto vacío.")
            return
        for idx, raw in enumerate(raw_attempts, start=1):
            preview = (raw or "").strip()
            if len(preview) > 500:
                preview = preview[:500] + "...(truncado)"
            print(f"[ERROR][{stage}] intento {idx} raw preview => {preview or '<vacío>'}")

    def print_question_diagnostics(stage: str, payload: dict, expected_questions: list[str]) -> None:
        if not args.debug_llm:
            return

        qa_items = payload.get("question_answers", []) if isinstance(payload, dict) else []
        if not isinstance(qa_items, list):
            print(f"[DEBUG][{stage}] 'question_answers' no es lista (tipo={type(qa_items).__name__}).")
            return

        print(f"[DEBUG][{stage}] question_answers detectadas: {len(qa_items)}/{len(expected_questions)}")
        for idx, item in enumerate(qa_items, start=1):
            if not isinstance(item, dict):
                print(f"[DEBUG][{stage}] item[{idx}] no es objeto (tipo={type(item).__name__}).")
                continue

            incoming_question = str(item.get("question", "")).strip()
            incoming_answer = str(item.get("answer", "")).strip()
            preview_q = incoming_question[:120] + ("..." if len(incoming_question) > 120 else "")
            preview_a = incoming_answer[:160] + ("..." if len(incoming_answer) > 160 else "")
            print(
                f"[DEBUG][{stage}] item[{idx}] question='{preview_q or '<vacía>'}' "
                f"answer_chars={len(incoming_answer)} preview='{preview_a or '<vacía>'}'"
            )

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
    )
    print("[2/4] Contexto del repositorio recopilado")

    prompt = build_document_prompt(
        repo_context=repo_context.to_prompt_context(),
        questions=questions,
        include_summary=analysis.has_summary_section,
        include_diagram=analysis.has_diagram_section,
        placeholders=analysis.placeholders,
        student_profile={
            "student_name": args.student_name,
            "student_id": args.student_id,
            "student_address": args.student_address,
            "student_career": args.student_career,
            "student_course": args.student_course,
        },
    )

    client = OllamaClient(base_url=args.ollama_url, model=args.model)
    print(f"[3/4] Solicitando generación al modelo '{args.model}'...")
    try:
        llm_result = client.generate_json(
            prompt,
            timeout_seconds=args.ollama_timeout,
        )
    except Exception as exc:
        print(
            "[WARN] No se obtuvo respuesta de Ollama dentro del tiempo esperado. "
            f"Se usará salida de contingencia. Detalle: {exc}"
        )
        llm_result = build_local_fallback_payload()
    initial_raw_attempts = list(client.last_attempt_raw_responses)
    debug_llm_dump(
        stage="initial",
        payload=llm_result,
        raw_text=client.last_raw_response,
        file_path=args.debug_llm_file.strip(),
    )

    def extract_question_answers(payload: dict) -> list[str]:
        answers: list[str] = []
        answers_by_question: dict[str, str] = {}

        qa_items = payload.get("question_answers", [])
        if isinstance(qa_items, list):
            for item in qa_items:
                if isinstance(item, dict):
                    answer = str(item.get("answer", "")).strip()
                    question = str(item.get("question", "")).strip()
                    if answer:
                        answers.append(answer)
                        if question:
                            answers_by_question[question] = answer
                elif isinstance(item, str) and item.strip():
                    answers.append(item.strip())

        if answers_by_question:
            ordered_answers: list[str] = []
            for question in questions:
                mapped = answers_by_question.get(question)
                if mapped:
                    ordered_answers.append(mapped)
            if ordered_answers:
                return ordered_answers

        if answers:
            return answers[: len(questions)]

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
            return answers[: len(questions)]

        qa_map = payload.get("qa")
        if isinstance(qa_map, dict):
            for question in questions:
                answer = qa_map.get(question)
                if isinstance(answer, str) and answer.strip():
                    answers.append(answer.strip())
        if answers:
            return answers[: len(questions)]

        return []

    def build_fallback_answers(
        payload: dict,
        expected_questions: list[str],
        raw_attempts: list[str],
    ) -> list[str]:
        if not expected_questions:
            return []

        payload_keys = sorted(payload.keys()) if isinstance(payload, dict) else []
        payload_pretty = json.dumps(payload, ensure_ascii=False, indent=2) if isinstance(payload, dict) else "{}"

        if len(payload_pretty) > 1200:
            payload_pretty = payload_pretty[:1200] + "...(truncado)"

        best_raw = ""
        for item in raw_attempts:
            if isinstance(item, str) and item.strip():
                best_raw = item.strip()
                break
        if len(best_raw) > 800:
            best_raw = best_raw[:800] + "...(truncado)"

        fallback_answers: list[str] = []
        for idx, question in enumerate(expected_questions, start=1):
            fallback_answers.append(
                (
                    f"{build_practical_answer(question)}\n\n"
                    f"[Nota técnica de contingencia]\n"
                    f"Pregunta {idx}: {question}\n"
                    f"Claves del payload recibido: {payload_keys}\n"
                    f"JSON parcial:\n{payload_pretty}\n"
                    f"Texto crudo:\n{best_raw or '<vacío>'}"
                )
            )
        return fallback_answers

    question_answers = extract_question_answers(llm_result)
    print_question_diagnostics(stage="initial", payload=llm_result, expected_questions=questions)

    summary = str(llm_result.get("summary", "")).strip() or None
    diagram = str(llm_result.get("diagram", "")).strip() or None
    fields = llm_result.get("fields", {})
    if not isinstance(fields, dict):
        fields = {}

    sections = llm_result.get("sections", {})
    if not isinstance(sections, dict):
        sections = {}

    # Fallback explícito para no perder datos de estudiante si el modelo no los devuelve.
    sections.setdefault("student_name", args.student_name)
    sections.setdefault("student_id", args.student_id)
    sections.setdefault("student_address", args.student_address)
    sections.setdefault("student_career", args.student_career)
    sections.setdefault("student_course", args.student_course)

    recovery_result: dict = {}
    recovery_raw_attempts: list[str] = []
    if questions and len(question_answers) < len(questions):
        print("[3.1/4] Reintento focalizado para recuperar respuestas de preguntas...")
        recovery_prompt = build_question_only_prompt(
            repo_context=repo_context.to_prompt_context(),
            questions=questions,
        )
        try:
            recovery_result = client.generate_json(
                recovery_prompt,
                temperature=0.1,
                timeout_seconds=args.ollama_timeout,
                num_predict=1400,
            )
        except Exception as exc:
            print(f"[WARN] Reintento focalizado falló: {exc}")
            recovery_result = {}
        debug_llm_dump(
            stage="recovery",
            payload=recovery_result,
            raw_text=client.last_raw_response,
        )
        print_question_diagnostics(stage="recovery", payload=recovery_result, expected_questions=questions)
        recovered_answers = extract_question_answers(recovery_result)
        if recovered_answers:
            question_answers = recovered_answers
        recovery_raw_attempts = list(client.last_attempt_raw_responses)
        if args.debug_llm:
            print(
                "[DEBUG][recovery] Estadísticas => "
                f"answers_extraidas={len(recovered_answers)}, "
                f"raw_attempts={len(recovery_raw_attempts)}"
            )

    if questions and not question_answers:
        print_failure_diagnostics(stage="initial", payload=llm_result, raw_attempts=initial_raw_attempts)
        if recovery_result or recovery_raw_attempts:
            print_failure_diagnostics(
                stage="recovery",
                payload=recovery_result,
                raw_attempts=recovery_raw_attempts,
            )
        print("El modelo no devolvió respuestas de preguntas; se insertarán respuestas fallback en el DOCX.")
        question_answers = build_fallback_answers(
            payload=recovery_result or llm_result,
            expected_questions=questions,
            raw_attempts=recovery_raw_attempts or initial_raw_attempts,
        )

    if args.debug_llm and questions:
        print(
            "[DEBUG][final] Resumen de ensamblado => "
            f"preguntas_detectadas={len(questions)}, "
            f"respuestas_finales={len(question_answers)}, "
            f"summary_chars={len(summary or '')}, "
            f"diagram_chars={len(diagram or '')}"
        )

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
        extra_sections=sections,
    )

    print(f"[4/4] Documento generado: {args.docx_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
