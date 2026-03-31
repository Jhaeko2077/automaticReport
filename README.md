# Agente local de documentación automática con Ollama

## ¿Qué hace?

1. Lee el repositorio objetivo:
   - estructura de archivos,
   - `README` (si existe),
   - fragmentos de código,
   - últimos commits de Git.
2. Lee el `.docx` y detecta:
   - filas de preguntas (`Pregunta 01: ... ?`),
   - sección `Resumen`,
   - sección `Diagrama`,
   - placeholders `{{CAMPO}}` (opcional).
3. Envía todo a **Ollama local** (por defecto `llama3`) y solicita:
   - respuesta para cada pregunta,
   - resumen largo y detallado del proyecto,
   - diagrama en Mermaid.
4. Escribe el resultado en un nuevo `.docx`:
   - cada respuesta debajo de su pregunta,
   - resumen en el bloque “Resumen”,
   - diagrama en el bloque “Diagrama”.
2. Lee una plantilla `.docx` y detecta placeholders con formato `{{NOMBRE_CAMPO}}`.
3. Usa **Ollama local** (por defecto modelo `llama3`) para generar contenido de cada campo.
4. Guarda un nuevo `.docx` con los datos completos.

---

## Requisitos

- Python 3.10+
- Ollama instalado y corriendo localmente
- Modelo descargado (ejemplo):

```bash
ollama pull llama3
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

---

## Cómo preparar tu documento Word

Con tu formato actual **no necesitas placeholders obligatorios**.

### Formato recomendado
- Preguntas en filas con texto tipo: `Pregunta 01: ¿...?...`
- Justo debajo de cada pregunta, una fila/celda vacía para respuesta.
- Una celda o bloque que inicie con `Resumen`.
- Una celda o bloque que inicie con `Diagrama`.

### Opcional: placeholders
También puedes usar `{{PROJECT_SUMMARY}}`, `{{QUESTION_1}}`, etc. y el sistema los completa desde el JSON `fields`.
## Formato de la plantilla `.docx`

Dentro de tu documento, coloca placeholders así:

- `{{PROJECT_SUMMARY}}`
- `{{CODE_DIAGRAM}}`
- `{{QUESTION_1}}`
- `{{QUESTION_2}}`

El agente reemplaza cada placeholder por texto generado en base al repositorio.

> Recomendación: usa nombres claros. Si el placeholder contiene `DIAGRAM`, el agente intentará devolver un diagrama en formato Mermaid.

---

## Uso

```bash
python run_agent.py \
  --repo-path /ruta/a/tu/repositorio \
  --docx-input /ruta/PIAD-426_FORMATOALUMNOTRABAJOFINAL.docx \
  --docx-output /ruta/PIAD-426_COMPLETADO.docx \
python -m auto_report_agent.cli \
  --repo-path /ruta/a/tu/repositorio \
  --docx-input /ruta/plantilla.docx \
  --docx-output /ruta/reporte_completado.docx \
  --model llama3
```

Opciones útiles:

- `--ollama-url` (default: `http://localhost:11434`)
- `--max-files` cantidad de archivos para muestrear
- `--max-file-chars` caracteres por archivo
- `--commit-limit` cantidad de commits recientes
- `--read-all-code` fuerza lectura de todos los archivos de código soportados
- `--debug-llm` imprime en consola claves JSON y preview de la salida cruda del modelo
- `--debug-llm-max-chars` tamaño máximo del preview de debug en consola
- `--debug-llm-file` guarda la respuesta cruda completa del modelo en un archivo para diagnóstico

---

## Guía paso a paso para que te funcione en local

1. **Clona este repositorio** en tu PC.
2. **Instala Python 3.10+**.
3. **Instala Ollama** y abre el servicio (`ollama serve`).
4. Descarga modelo local: `ollama pull llama3`.
5. En la carpeta del proyecto, instala dependencias: `pip install -r requirements.txt`.
6. Coloca tu documento `.docx` de formato en una ruta local.
7. Ejecuta el comando de `python run_agent.py ...`.
8. Abre el archivo de salida `.docx` y revisa:
   - respuestas bajo cada pregunta,
   - resumen largo en “Resumen”,
   - diagrama en “Diagrama”.

---

## Limitaciones actuales

- Soporta `.docx` (no `.doc` legacy).
- El diagrama se inserta como texto Mermaid (no imagen renderizada).
- Si el formato Word cambia drásticamente, puede requerir ajustar la detección de preguntas/secciones.

---

## Mejoras siguientes sugeridas

- Renderizar diagrama Mermaid a imagen e incrustarlo en Word.
- Soporte para múltiples tipos de plantillas académicas.
- Validación automática de calidad de respuestas.
- Modo “solo actualizar secciones vacías”.

---

## Ejemplo de flujo completo

1. Creas tu plantilla `.docx` con placeholders.
2. Ejecutas el comando.
3. Obtienes el documento completo y listo para revisar.
4. Iteras ajustando prompt, placeholders y modelo.

---

## Qué conectar para que funcione en tu máquina

- **Ollama local** activo (`ollama serve`)
- **Modelo local** descargado (`llama3` u otro)
- **Repositorio objetivo** ya clonado localmente
- **Plantilla `.docx`** con placeholders

---

## Mejoras recomendadas (siguiente paso)

- Validación de calidad por sección (auto-revisión de respuestas)
- Soporte para `.doc` legado vía conversión a `.docx`
- Modo incremental para actualizar solo campos vacíos
- Exportar además a Markdown/PDF
