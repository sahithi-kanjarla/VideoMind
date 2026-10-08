import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


class GeminiGenerationError(RuntimeError):
    pass


class GeminiGenerator:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model

    def answer(self, question: str, context: list[dict]) -> str:
        if not self.api_key:
            raise GeminiGenerationError("Gemini is not configured. Set GEMINI_API_KEY.")
        excerpts = "\n\n".join(
            f"[{item['metadata'].get('start', 0):.2f}s–{item['metadata'].get('end', 0):.2f}s] {item['text']}"
            for item in context
        )
        prompt = (
            "Answer the question using only the supplied excerpts from a YouTube video. "
            "Synthesize a concise, useful answer. If the excerpts do not support an answer, "
            "say that the information was not found in the video. Do not guess.\n\n"
            f"Excerpts:\n{excerpts}\n\nQuestion: {question}"
        )
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        request = Request(
            endpoint,
            data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=45) as response:
                payload = json.loads(response.read())
            return payload["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (HTTPError, URLError, TimeoutError, KeyError, IndexError, ValueError) as exc:
            raise GeminiGenerationError("Gemini could not generate an answer.") from exc
