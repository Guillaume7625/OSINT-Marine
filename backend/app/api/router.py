from fastapi import APIRouter, Depends

from app.api import chat, conversations, files, settings
from app.core.dependencies import require_api_token

api_router = APIRouter(dependencies=[Depends(require_api_token)])
api_router.include_router(conversations.router)
api_router.include_router(chat.router)
api_router.include_router(files.router)
api_router.include_router(settings.router)
