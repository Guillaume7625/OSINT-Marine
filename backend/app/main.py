from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.migrations import run_migrations
from app.core.dependencies import get_ingestion_queue

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(debug=settings.app_debug)
    settings.upload_root.mkdir(parents=True, exist_ok=True)
    worker_task: asyncio.Task[None] | None = None

    if settings.app_env != "test":
        if settings.auto_migrate_on_startup:
            logger.info("AUTO_MIGRATE_ON_STARTUP=true: running Alembic upgrade head")
            run_migrations(database_url=settings.database_url)
            logger.info("Alembic startup migration completed")
        else:
            logger.info(
                "AUTO_MIGRATE_ON_STARTUP=false: run 'cd backend && alembic upgrade head' before starting the app"
            )

        queue = get_ingestion_queue()
        queue.recover_in_progress_jobs()
        worker_task = asyncio.create_task(queue.run_forever())

    try:
        yield
    finally:
        if worker_task:
            worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await worker_task


settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.app_debug, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
