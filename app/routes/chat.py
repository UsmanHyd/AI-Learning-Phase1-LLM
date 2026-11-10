import logging

from fastapi import APIRouter, HTTPException

from app.llm.client import LLMError, generate
from app.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    try:
        reply = await generate(body.prompt)
    except LLMError as exc:
        logger.warning("LLM call failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="The AI service could not produce a usable answer.",
        )
    return ChatResponse(reply=reply)
