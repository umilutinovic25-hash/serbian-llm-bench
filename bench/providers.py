"""Model backends. Ollama for local models, mock for offline testing."""

from __future__ import annotations

import json
import random
import urllib.error
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"


class ProviderError(RuntimeError):
    pass


class OllamaProvider:
    def __init__(self, model: str, timeout: int = 180):
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 256},
        }).encode("utf-8")
        request = urllib.request.Request(
            OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read())
        except urllib.error.URLError as exc:
            raise ProviderError(f"ollama nedostupan: {exc}") from exc
        text = body.get("response", "")
        # Reasoning models emit <think>...</think>; the graded answer follows it.
        if "</think>" in text:
            text = text.split("</think>")[-1]
        return text.strip()


class MockProvider:
    """Answers randomly. Used to sanity-check the harness without a model."""

    def __init__(self, model: str = "mock", seed: int = 0):
        self.model = model
        self._random = random.Random(seed)

    def generate(self, prompt: str) -> str:
        if "isključivo jednim slovom" in prompt:
            return self._random.choice(["A", "B", "C"])
        return "nepoznato"


def get_provider(spec: str):
    """spec is "ollama:qwen3:1.7b" or "mock"."""
    if spec == "mock":
        return MockProvider()
    if spec.startswith("ollama:"):
        return OllamaProvider(spec.split(":", 1)[1])
    raise ProviderError(f"nepoznat provider: {spec}")
