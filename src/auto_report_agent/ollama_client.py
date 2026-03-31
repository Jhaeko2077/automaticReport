from __future__ import annotations

import json
import re
from typing import Any

import requests


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _extract_text(self, data: dict[str, Any]) -> str:
        response_text = data.get("response")
        if isinstance(response_text, str) and response_text.strip():
            return response_text.strip()

        message = data.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()

        return ""

    def _parse_json_from_text(self, text: str) -> dict[str, Any]:
        candidate = text.strip()
        if not candidate:
            raise json.JSONDecodeError("empty payload", candidate, 0)

        # Respuesta ideal: JSON puro.
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
            raise ValueError("Model response JSON must be an object.")
        except json.JSONDecodeError:
            pass

        # Respuesta en markdown con bloque ```json ... ```.
        fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", candidate, flags=re.IGNORECASE)
        if fenced:
            fenced_content = fenced.group(1).strip()
            parsed = json.loads(fenced_content)
            if isinstance(parsed, dict):
                return parsed
            raise ValueError("Model response JSON must be an object.")

        # Fallback: extraer primer objeto JSON.
        match = re.search(r"\{[\s\S]*\}", candidate)
        if match:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
            raise ValueError("Model response JSON must be an object.")

        raise json.JSONDecodeError("no JSON object found", candidate, 0)

    def generate_json(self, prompt: str, temperature: float = 0.2) -> dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        base_payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature,
            },
        }

        attempts = [
            prompt,
            prompt
            + "\n\nIMPORTANTE: responde con UN SOLO objeto JSON válido, sin texto adicional.",
        ]

        last_error: Exception | None = None
        for attempt_prompt in attempts:
            payload = {**base_payload, "prompt": attempt_prompt}
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise ValueError(f"Ollama error: {data['error']}")

            text = self._extract_text(data)
            try:
                return self._parse_json_from_text(text)
            except (json.JSONDecodeError, ValueError):
                last_error = ValueError(
                    "Ollama did not return valid JSON. "
                    f"Model='{self.model}', response_chars={len(text)}"
                )

        assert last_error is not None
        raise last_error
