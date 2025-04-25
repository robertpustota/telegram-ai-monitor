from telethon import events
from telethon.sessions import StringSession
from telethon import TelegramClient
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import asyncio
import logging
import json
from datetime import datetime

from ..models.models import Channel, Topic, Post, TelegramSession, APIToken
from ..services.llm_service import check_post_relevance
from ..utils.telegram import create_telegram_client
from ..schemas.schemas import ProxyConfig
from ..core.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()
logger.setLevel(settings.LOG_LEVEL)
formatter = logging.Formatter(settings.LOG_FORMAT)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def log_with_context(level: int, message: str, **context):
    """Helper function for structured logging"""
    extra = {k: v for k, v in context.items() if v is not None}
    logger.log(level, f"{message} | Context: {json.dumps(extra)}")

class MonitoringStats:
    def __init__(self):
        self._stats = {
            "total_messages": 0,
            "relevant_messages": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }

    def increment_total_messages(self):
        self._stats["total_messages"] += 1

    def increment_relevant_messages(self):
        self._stats["relevant_messages"] += 1

    def increment_errors(self):
        self._stats["errors"] += 1

    def get_stats(self):
        stats = self._stats.copy()
        stats["start_time"] = stats["start_time"].isoformat()
        uptime = datetime.utcnow() - self._stats["start_time"]
        stats["uptime"] = str(uptime)
        return stats

class TelegramClientManager:
    def __init__(self, db: Session):
        self.db = db
        self.clients: Dict[int, TelegramClient] = {}

    async def create_client(self, session: TelegramSession) -> Optional[TelegramClient]:
        try:
            log_with_context(logging.DEBUG, "Creating Telegram client", 
                           session_id=session.id,
                           phone=session.phone_number,
                           api_id=session.api_id)

            proxy_config = None
            if session.proxy_type and session.proxy_host and session.proxy_port:
                proxy_type_map = {
                    1: "http",
                    2: "socks4",
                    3: "socks5"
                }
                proxy_type_str = proxy_type_map.get(session.proxy_type)
                
                if not proxy_type_str:
                    log_with_context(logging.ERROR, "Invalid proxy type",
                                   proxy_type=session.proxy_type)
                    return None

                proxy_config = ProxyConfig(
                    proxy_type=proxy_type_str,
                    host=session.proxy_host,
                    port=session.proxy_port,
                    username=session.proxy_username,
                    password=session.proxy_password
                )
                log_with_context(logging.DEBUG, "Using proxy configuration",
                               proxy_type=proxy_type_str,
                               host=session.proxy_host,
                               port=session.proxy_port)

            # Создаем клиент напрямую
            client = TelegramClient(
                StringSession(session.session_string),
                api_id=session.api_id,
                api_hash=session.api_hash,
                proxy=(proxy_config.proxy_type, 
                       proxy_config.host, 
                       proxy_config.port, 
                       True, 
                       proxy_config.username, 
                       proxy_config.password) if proxy_config else None
            )
            
            log_with_context(logging.DEBUG, "Connecting to Telegram")
            await client.connect()
            
            if not await client.is_user_authorized():
                log_with_context(logging.ERROR, "Client not authorized",
                               session_id=session.id,
                               phone=session.phone_number)
                session.is_active = False
                self.db.commit()
                return None
                
            log_with_context(logging.INFO, "Successfully created and authorized client",
                           session_id=session.id,
                           phone=session.phone_number)
            return client

        except Exception as e:
            log_with_context(logging.ERROR, "Failed to create client", 
                           error=str(e),
                           error_type=type(e).__name__,
                           session_id=session.id,
                           phone=session.phone_number,
                           api_id=session.api_id)
            return None

    async def disconnect_client(self, api_token_id: int):
        if api_token_id in self.clients:
            await self.clients[api_token_id].disconnect()
            del self.clients[api_token_id]

class ChannelManager:
    def __init__(self, db: Session):
        self.db = db

    async def get_channel_ids(self, api_token_id: int, client: TelegramClient) -> List[int]:
        channels = self.db.query(Channel).join(TelegramSession).join(APIToken).filter(
            APIToken.id == api_token_id
        ).all()
        
        channel_ids = []
        for channel in channels:
            if channel.channel_id is None:
                try:
                    entity = await client.get_entity(channel.username)
                    channel.channel_id = entity.id
                    self.db.commit()
                    channel_ids.append(entity.id)
                except Exception as e:
                    log_with_context(logging.ERROR, "Failed to get channel ID",
                                   channel_username=channel.username,
                                   error=str(e))
            else:
                channel_ids.append(channel.channel_id)
        
        return channel_ids

    def update_channel_info(self, channel: Channel, channel_id: int, title: str):
        if not channel.channel_id:
            channel.channel_id = channel_id
            channel.title = title
            self.db.commit()

class MessageProcessor:
    def __init__(self, db: Session, stats: MonitoringStats):
        self.db = db
        self.stats = stats

    async def process_message(self, event, api_token_id: int):
        try:
            message = event.message
            channel = await event.get_chat()
            
            self.stats.increment_total_messages()
            
            log_with_context(logging.DEBUG, "Processing new message",
                           api_token_id=api_token_id,
                           channel_id=channel.id,
                           channel_title=channel.title,
                           message_id=message.id)
            
            db_channel = self.db.query(Channel).filter(
                Channel.username == channel.username,
                Channel.session_id == api_token_id
            ).first()
            
            if not db_channel:
                log_with_context(logging.WARNING, "Channel not found in database",
                               api_token_id=api_token_id,
                               channel_username=channel.username)
                return
            
            topics = self.db.query(Topic).all()
            relevant_topics = []
            
            for topic in topics:
                if check_post_relevance(message.text, topic.name, topic.description):
                    relevant_topics.append(topic.name)
                    post = Post(
                        channel_id=db_channel.id,
                        topic_id=topic.id,
                        text=message.text,
                        date=message.date
                    )
                    self.db.add(post)
                    self.stats.increment_relevant_messages()
            
            if relevant_topics:
                log_with_context(logging.INFO, "Found relevant topics for message",
                               api_token_id=api_token_id,
                               message_id=message.id,
                               relevant_topics=relevant_topics)
            
            self.db.commit()
                    
        except Exception as e:
            self.stats.increment_errors()
            log_with_context(logging.ERROR, "Failed to process message",
                           api_token_id=api_token_id,
                           error=str(e),
                           error_count=self.stats._stats["errors"])

class MonitoringManager:
    def __init__(self, db: Session):
        self.db = db
        self._monitoring_tasks: Dict[int, asyncio.Task] = {}
        self.settings = get_settings()

    async def start_monitoring(self, client: TelegramClient, api_token_id: int, channel_ids: List[int], message_processor: MessageProcessor):
        @client.on(events.NewMessage(chats=channel_ids))
        async def handle_new_message(event):
            await message_processor.process_message(event, api_token_id)

        task = asyncio.create_task(self._monitor_session(api_token_id))
        self._monitoring_tasks[api_token_id] = task

    async def stop_monitoring(self, api_token_id: int):
        if api_token_id in self._monitoring_tasks:
            self._monitoring_tasks[api_token_id].cancel()
            del self._monitoring_tasks[api_token_id]

    async def _monitor_session(self, api_token_id: int):
        try:
            while True:
                session = self.db.query(TelegramSession).join(APIToken).filter(
                    APIToken.id == api_token_id,
                    TelegramSession.is_active == True
                ).first()

                if not session:
                    break

                session.last_used = datetime.utcnow()
                self.db.commit()
                await asyncio.sleep(self.settings.TELEGRAM_SESSION_CHECK_INTERVAL)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            log_with_context(logging.ERROR, "Error in monitoring task", error=str(e))

class TelegramMonitor:
    def __init__(self, db: Session):
        self.db = db
        self.stats = MonitoringStats()
        self.client_manager = TelegramClientManager(db)
        self.channel_manager = ChannelManager(db)
        self.message_processor = MessageProcessor(db, self.stats)
        self.monitoring_manager = MonitoringManager(db)
        self.settings = get_settings()
        self._monitored_tokens = set()  # Храним ID токенов, для которых уже запущен мониторинг

    async def start_monitoring(self, api_token_id: int):
        if api_token_id in self._monitored_tokens:
            log_with_context(logging.DEBUG, "Monitoring already started for API token", api_token_id=api_token_id)
            return

        session = self.db.query(TelegramSession).join(APIToken).filter(
            APIToken.id == api_token_id,
            TelegramSession.is_active == True
        ).first()

        if not session:
            log_with_context(logging.ERROR, "No active session found for API token", api_token_id=api_token_id)
            return

        log_with_context(logging.INFO, "Starting monitoring for API token", 
                        api_token_id=api_token_id,
                        phone=session.phone_number)

        client = await self.client_manager.create_client(session)
        if not client:
            log_with_context(logging.ERROR, "Failed to create client for API token", api_token_id=api_token_id)
            return

        self.client_manager.clients[api_token_id] = client
        channel_ids = await self.channel_manager.get_channel_ids(api_token_id, client)
        
        if channel_ids:
            log_with_context(logging.INFO, "Starting monitoring for channels", 
                           api_token_id=api_token_id,
                           channel_count=len(channel_ids))
            await self.monitoring_manager.start_monitoring(
                client, api_token_id, channel_ids, self.message_processor
            )
            self._monitored_tokens.add(api_token_id)
        else:
            log_with_context(logging.WARNING, "No channels to monitor for API token", api_token_id=api_token_id)

    async def stop_monitoring(self, api_token_id: int):
        if api_token_id not in self._monitored_tokens:
            return

        log_with_context(logging.INFO, "Stopping monitoring for API token", api_token_id=api_token_id)
        await self.monitoring_manager.stop_monitoring(api_token_id)
        await self.client_manager.disconnect_client(api_token_id)
        self._monitored_tokens.remove(api_token_id)

    def _log_stats(self):
        """Log current monitoring statistics"""
        stats = self.stats.get_stats()
        log_with_context(logging.INFO, "Monitoring statistics", **stats)

    async def start(self):
        log_with_context(logging.INFO, "Starting Telegram monitor service")
        
        # При первом запуске мониторим все активные токены
        api_tokens = self.db.query(APIToken).filter(
            APIToken.is_active == True
        ).all()

        log_with_context(logging.INFO, "Initializing monitoring for active API tokens", 
                        token_count=len(api_tokens))
        
        for token in api_tokens:
            await self.start_monitoring(token.id)

        # Основной цикл только проверяет новые токены
        while True:
            try:
                # Получаем все активные токены
                active_tokens = self.db.query(APIToken).filter(
                    APIToken.is_active == True
                ).all()

                # Находим новые токены
                new_tokens = [token for token in active_tokens if token.id not in self._monitored_tokens]
                
                if new_tokens:
                    log_with_context(logging.INFO, "Found new active API tokens", 
                                   new_token_count=len(new_tokens),
                                   new_token_ids=[t.id for t in new_tokens])
                    
                    for token in new_tokens:
                        await self.start_monitoring(token.id)

                # Проверяем неактивные токены
                inactive_tokens = [token_id for token_id in self._monitored_tokens 
                                 if not any(t.id == token_id for t in active_tokens)]
                
                if inactive_tokens:
                    log_with_context(logging.INFO, "Found inactive API tokens", 
                                   inactive_token_count=len(inactive_tokens),
                                   inactive_token_ids=inactive_tokens)
                    
                    for token_id in inactive_tokens:
                        await self.stop_monitoring(token_id)

                # Log statistics every hour
                if datetime.utcnow().minute == 0:
                    self._log_stats()

                await asyncio.sleep(self.settings.TELEGRAM_MONITOR_INTERVAL)

            except Exception as e:
                self.stats.increment_errors()
                log_with_context(logging.ERROR, "Error in main monitoring loop", 
                               error=str(e),
                               error_count=self.stats._stats["errors"])
                await asyncio.sleep(self.settings.TELEGRAM_MONITOR_INTERVAL) 
