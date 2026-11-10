import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai
from google.genai import types

from app.config import settings

client = genai.Client(api_key=settings.provider_api_key)

PROMPT = "Write one sentence about the ocean."

RUNS = 5


def run_batch(temperature: float) -> None:
    print(f"\n=== temperature = {temperature} ===")
    answers = []

    for i in range(1, RUNS + 1):
        start = time.perf_counter()
        response = client.models.generate_content(
            model=settings.default_model,
            contents=PROMPT,
            config=types.GenerateContentConfig(temperature=temperature),
        )
        elapsed = time.perf_counter() - start

        text = (response.text or "").strip()
        answers.append(text)
        usage = response.usage_metadata

        print(
            f"run {i}: {text!r:40} "
            f"| out={usage.candidates_token_count} "
            f"thoughts={usage.thoughts_token_count} "
            f"| {elapsed:.1f}s"
        )
        time.sleep(13)

    print(f"-> unique answers: {len(set(answers))} out of {RUNS}")


run_batch(0.0)
run_batch(2.0)
