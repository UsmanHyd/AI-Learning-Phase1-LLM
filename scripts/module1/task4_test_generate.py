import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.llm.client import LLMError, generate


async def main() -> None:
    print("--- normal call ---")
    print(await generate("Say hello in one short sentence."))

    print("\n--- truncated call (cap of 5 tokens) ---")
    try:
        print(await generate("Explain how the internet works in detail.", max_output_tokens=500))
    except LLMError as e:
        print("Caught LLMError:", e)


asyncio.run(main())
