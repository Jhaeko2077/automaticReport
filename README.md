# Agente local de documentación automática con Ollama

Este proyecto crea un **agente en consola (CLI)** que analiza un repositorio y completa una plantilla `.docx` local con respuestas generadas por IA.

## ¿Qué hace?

1. Lee el repositorio objetivo:
   - estructura de archivos,
   - `README` (si existe),
   - fragmentos de código,
   - últimos commits de Git.
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

