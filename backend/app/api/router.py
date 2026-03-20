from fastapi import APIRouter

from app.api import chat, conversations, files, settings

api_router = APIRouter()
api_router.include_router(conversations.router)
api_router.include_router(chat.router)
api_router.include_router(files.router)
api_router.include_router(settings.router)
