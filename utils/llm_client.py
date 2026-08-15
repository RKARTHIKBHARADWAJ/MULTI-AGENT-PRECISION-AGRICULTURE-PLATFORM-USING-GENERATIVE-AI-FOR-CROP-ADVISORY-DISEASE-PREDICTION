"""
Thin, provider-agnostic wrapper around whichever LLM backend is configured.
"""

from config import (
    LLM_PROVIDER,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)
from utils.logger import get_logger

logger = get_logger("llm_client")


class LLMClient:
    def __init__(self, provider: str = None):
        self.provider = (provider or LLM_PROVIDER).lower()

        if self.provider == "anthropic":
            if not ANTHROPIC_API_KEY:
                raise EnvironmentError("ANTHROPIC_API_KEY is not set.")
            import anthropic
            self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        elif self.provider == "openai":
            if not OPENAI_API_KEY:
                raise EnvironmentError("OPENAI_API_KEY is not set.")
            import openai
            self._client = openai.OpenAI(api_key=OPENAI_API_KEY)

        elif self.provider == "gemini":
            if not GEMINI_API_KEY:
                raise EnvironmentError(
                    "GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com"
                )
            from google import genai
            self._client = genai.Client(api_key=GEMINI_API_KEY)

        else:
            raise ValueError(f"Unknown LLM_PROVIDER: {self.provider}")

    def generate(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        try:
            if self.provider == "anthropic":
                response = self._client.messages.create(
                    model=ANTHROPIC_MODEL,
                    max_tokens=max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": prompt}],
                )
                return "".join(
                    b.text for b in response.content if b.type == "text"
                ).strip()

            elif self.provider == "openai":
                response = self._client.chat.completions.create(
                    model=OPENAI_MODEL,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                )
                return response.choices[0].message.content.strip()

            elif self.provider == "gemini":
                from google.genai import types
                response = self._client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system,
                        max_output_tokens=max_tokens,
                    ),
                )
                return (response.text or "").strip()

        except Exception as exc:
            logger.error(f"LLM call failed: {exc}")
            return (
                "[LLM unavailable - returning fallback message] "
                "Unable to generate advisory text right now. "
                "Please check your API key and network connection."
            )
