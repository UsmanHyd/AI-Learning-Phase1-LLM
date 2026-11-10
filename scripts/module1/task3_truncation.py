import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from google import genai
from google.genai import types

from app.config import settings

client = genai.Client(api_key=settings.provider_api_key)

PROMPT = "Explain how the internet works in detail."
LIMITS = [5, 20, 60, 1000]


def run(limit: int) -> None:
    print(f"\n=== max_output_tokens = {limit} ===")

    response = client.models.generate_content(
        model=settings.default_model,
        contents=PROMPT,
        config=types.GenerateContentConfig(max_output_tokens=limit),
    )

    candidate = response.candidates[0] if response.candidates else None
    finish = candidate.finish_reason if candidate else None
    text = response.text or ""
    usage = response.usage_metadata

    print(f"finish_reason : {finish}")
    print(f"truncated     : {finish is not None and finish.name == 'MAX_TOKENS'}")
    print(f"prompt tokens : {usage.prompt_token_count}")
    print(f"output tokens : {usage.candidates_token_count}")
    print(f"thought tokens: {usage.thoughts_token_count}")
    print(f"total tokens  : {usage.total_token_count}")
    print(f"text length   : {len(text)} characters")
    print(f"text          : {text[:300]!r}")


for limit in LIMITS:
    run(limit)
    time.sleep(13)
