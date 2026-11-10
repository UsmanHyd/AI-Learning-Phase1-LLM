import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai

from app.config import settings

client = genai.Client(api_key=settings.provider_api_key)

for m in client.models.list():
    print(m.name, "|", m.supported_actions)
