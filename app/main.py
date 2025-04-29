from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from .core.database import SessionLocal
from .models.base import Base
from .services.telegram_monitor import TelegramMonitor
from .routers import auth, filters, messages

app = FastAPI(
    title="Telegram Monitor",
    description="API for monitoring messages from various Telegram sources",
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
app.include_router(filters.router)
app.include_router(messages.router)


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=SessionLocal().get_bind())
    global telegram_monitor
    db = SessionLocal()
    telegram_monitor = TelegramMonitor(db)
    asyncio.create_task(telegram_monitor.start())
