from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config import get_settings
from .redis_client import close_redis, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_redis()
    yield
    await close_redis()


app = FastAPI(
    title="NewsHub API",
    description="Агрегатор новостей: статьи и видео независимых СМИ",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)
