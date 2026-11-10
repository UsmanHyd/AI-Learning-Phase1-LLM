from fastapi import FastAPI
from app.config import settings

from app.schemas import EchoRequest, EchoResponse

app = FastAPI(title=settings.app_name)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/echo", response_model=EchoResponse)
async def echo(body: EchoRequest):
    text = " ".join([body.message] * body.repeat)
    return EchoResponse(echoed=text, length=len(text))
