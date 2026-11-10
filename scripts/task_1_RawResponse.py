import json
import sys
from pathlib import Path

# Make "app" importable when running this file directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai

from app.config import settings

client = genai.Client(api_key=settings.provider_api_key)

response = client.models.generate_content(
    model=settings.default_model,
    contents="Explain what an API is in two sentences.",
)

print("=== RAW RESPONSE (full object) ===")
print(response)

print("\n=== AS JSON ===")
print(json.dumps(response.model_dump(exclude_none=True), indent=2, default=str))

print("\n=== THE FIELDS WE CARE ABOUT ===")
print("text:           ", response.text)
print("finish_reason:  ", response.candidates[0].finish_reason)
print("prompt tokens:  ", response.usage_metadata.prompt_token_count)
print("output tokens:  ", response.usage_metadata.candidates_token_count)
print("total tokens:   ", response.usage_metadata.total_token_count)
print("model_version:  ", response.model_version)
