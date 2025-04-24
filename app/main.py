from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

from .core.database import SessionLocal
from .models.base import Base
from .services.telegram_monitor import TelegramMonitor
from .routers import auth, topics, posts

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

app = FastAPI(
    title="Telegram Monitor",
    description="API for monitoring posts by topics from Telegram channels",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(topics.router)
app.include_router(posts.router)


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=SessionLocal().get_bind())
    global telegram_monitor
    db = SessionLocal()
    telegram_monitor = TelegramMonitor(db)
    asyncio.create_task(telegram_monitor.start())
