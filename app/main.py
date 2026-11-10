from fastapi import FastAPI

from app.config import settings
from app.routes.chat import router as chat_router

app = FastAPI(title=settings.app_name)
app.include_router(chat_router)
