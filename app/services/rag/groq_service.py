import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


class GroqGenerationError(RuntimeError):
    pass


class GroqGenerator:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.groq_api_key
        self.model = model or "openai/gpt-oss-120b"  # Most powerful available

    def answer(self, question: str, context: list[dict]) -> str:
        if not self.api_key:
            raise GroqGenerationError("Groq is not configured. Set GROQ_API_KEY in .env")

        excerpts = "\n\n".join(
            f"[{item['metadata'].get('start', 0):.0f}s] {item['text']}"
            for item in context
        )

        prompt = (
            "You are answering questions about a video ONLY using these exact excerpts.\n"
            "CRITICAL: Do NOT use outside knowledge. Answer ONLY from the excerpts.\n\n"
            "If the answer is NOT in these excerpts, say: 'This information is not in the video.'\n\n"
            f"VIDEO EXCERPTS:\n{excerpts}\n\n"
            f"QUESTION: {question}\n\n"
            "ANSWER (use only the excerpts above):"
        )

        endpoint = "https://api.groq.com/openai/v1/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,  # Lower = more focused on facts, less creative
            "top_p": 0.8,
            "max_tokens": 300,  # Concise answers only
        }

        request = Request(
            endpoint,
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "MindVault/1.0 (VideoMind RAG System)"
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=30) as response:
                result = json.loads(response.read())
            return result["choices"][0]["message"]["content"].strip()
        except (HTTPError, URLError, TimeoutError, KeyError, IndexError, ValueError) as exc:
            raise GroqGenerationError(f"Groq error: {str(exc)}") from exc
