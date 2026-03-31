# Agente local de documentación automática con Ollama

Este proyecto crea un **agente en consola (CLI)** que analiza un repositorio y completa un documento `.docx` local con respuestas generadas por IA.

Está pensado para casos como tu formato de trabajo final:
- tabla con **Preguntas 01, 02, 03...**,
- sección **Resumen**,
- sección **Diagrama**.

El agente ahora **lee las preguntas directamente desde el cuadro** (aunque cambien en cada documento) y escribe las respuestas en el espacio inferior correspondiente.

---

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

---

## Uso

```bash
python run_agent.py \
  --repo-path /ruta/a/tu/repositorio \
  --docx-input /ruta/PIAD-426_FORMATOALUMNOTRABAJOFINAL.docx \
  --docx-output /ruta/PIAD-426_COMPLETADO.docx \
  --model llama3
```

Opciones útiles:

- `--ollama-url` (default: `http://localhost:11434`)
- `--max-files` cantidad de archivos para muestrear
- `--max-file-chars` caracteres por archivo
- `--commit-limit` cantidad de commits recientes

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
