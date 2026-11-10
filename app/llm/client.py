from google import genai
from google.genai import types

from app.config import settings

_client = genai.Client(api_key=settings.provider_api_key)


class LLMError(Exception):
    """Raised when the model call returns something we cannot use."""


async def generate(
    prompt: str,
    *,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
) -> str:
    response = await _client.aio.models.generate_content(
        model=settings.default_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        ),
    )

    candidate = response.candidates[0] if response.candidates else None
    if candidate is None:
        raise LLMError("The model returned no answer (the prompt may have been blocked).")

    finish = candidate.finish_reason.name if candidate.finish_reason else "UNKNOWN"
    if finish != "STOP":
        raise LLMError(f"Generation did not finish normally (finish_reason={finish}).")

    text = (response.text or "").strip()
    if not text:
        raise LLMError("The model returned empty text.")

    return text
