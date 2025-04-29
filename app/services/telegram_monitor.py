from telethon import events
from telethon.sessions import StringSession
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User
from sqlalchemy.orm import Session
from typing import Dict, Optional, Set, Any
import asyncio
import re
from loguru import logger

from ..models.models import Source, Filter, Message, SourceType
from ..services.llm_service import check_post_relevance


class TelegramMonitor:
    def __init__(self, db: Session):
        self.db = db
        self._clients: Dict[int, TelegramClient] = {}
        self._active_handlers: Dict[int, Any] = {}
        self._monitored_filters: Set[int] = set()
        self._filter_states: Dict[int, dict] = {}

    async def _get_client(self, filter: Filter) -> Optional[TelegramClient]:
        """Gets or creates a client for the filter"""
        if filter.id in self._clients:
            client = self._clients[filter.id]
            try:
                if not client.is_connected():
                    await client.connect()
                return client
            except Exception as e:
                logger.error(f"Error reusing client for filter {filter.name}: {e}")
                del self._clients[filter.id]
                return None

        session = filter.session
        if not session or not session.is_active:
            logger.warning(f"No active session found for filter {filter.name}")
            return None

        try:
            client = TelegramClient(
                StringSession(session.session_string),
                api_id=session.api_id,
                api_hash=session.api_hash
            )
            await client.connect()
            
            if not await client.is_user_authorized():
                session.is_active = False
                self.db.commit()
                logger.warning(f"Client is not authorized for filter {filter.name}")
                return None
                
            logger.info(f"Client successfully created and connected for filter {filter.name}")
            self._clients[filter.id] = client
            return client
        except Exception as e:
            logger.error(f"Error creating client for filter {filter.name}: {e}")
            return None

    async def _get_or_create_source(self, chat: Any, source_type: SourceType) -> Optional[Source]:
        """Gets or creates a source"""
        source = self.db.query(Source).filter(Source.source_id == chat.id).first()
        if source:
            return source
            
        source = self.db.query(Source).filter(
            Source.username == (chat.username or str(chat.id))
        ).first()
        
        if source:
            source.source_id = chat.id
            source.source_type = source_type
            source.title = getattr(chat, "title", None)
        else:
            source = Source(
                username=chat.username or str(chat.id),
                title=getattr(chat, "title", None),
                source_id=chat.id,
                source_type=source_type
            )
            self.db.add(source)
        
        self.db.commit()
        logger.info(f"{'Updated' if source.id else 'Created'} source: {source.username} (ID: {source.source_id})")
        return source

    async def _process_message(self, event: events.NewMessage.Event, filter: Filter) -> None:
        """Processes a received message"""
        try:
            chat = await event.get_chat()
            message = event.message
            
            source_type = SourceType.CHANNEL if isinstance(chat, Channel) else \
                         SourceType.GROUP if isinstance(chat, Chat) else \
                         SourceType.PRIVATE if isinstance(chat, User) else None
            
            if not source_type:
                logger.warning(f"Unknown chat type: {chat}")
                return
            
            source = await self._get_or_create_source(chat, source_type)
            if not source:
                return
            
            if filter.prompt:
                try:
                    if not check_post_relevance(message.text or "", filter.name, filter.prompt):
                        logger.info(f"Message not relevant for filter {filter.name}")
                        return
                    logger.info(f"Message relevant for filter {filter.name}")
                except Exception as e:
                    logger.error(f"Error checking relevance: {e}")
                    return
            
            message_obj = Message(
                text=message.text or "",
                date=message.date,
                message_id=message.id,
                source_id=source.id,
                filter_id=filter.id
            )
            self.db.add(message_obj)
            self.db.commit()
            logger.info(f"New message received from {source.username} for filter {filter.name}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _setup_filter_handler(self, filter: Filter) -> None:
        """Sets up a handler for the filter"""
        client = await self._get_client(filter)
        if not client:
            return

        chats_to_monitor = set()
        is_blacklist = False
        
        if filter.include_sources:
            sources = {s.username: s for s in self.db.query(Source).all()}
            for username in filter.include_sources:
                source = sources.get(username)
                if source and source.source_id:
                    chats_to_monitor.add(source.source_id)
                else:
                    try:
                        entity = await client.get_entity(username)
                        chats_to_monitor.add(entity.id)
                        logger.info(f"Got source ID {entity.id} for included sources for {username} from Telegram")
                    except Exception as e:
                        logger.error(f"Error getting source ID for {username}: {e}")
            logger.info(f"Filter {filter.name} will monitor included sources: {', '.join(filter.include_sources)}")
        elif filter.exclude_sources:
            sources = {s.username: s for s in self.db.query(Source).all()}
            for username in filter.exclude_sources:
                source = sources.get(username)
                if source and source.source_id:
                    chats_to_monitor.add(source.source_id)
                else:
                    try:
                        entity = await client.get_entity(username)
                        chats_to_monitor.add(entity.id)
                        logger.info(f"Got source ID {entity.id} for exclude sources for {username} from Telegram")
                    except Exception as e:
                        logger.error(f"Error getting source ID for {username}: {e}")
            is_blacklist = True
            logger.info(f"Filter {filter.name} will exclude sources: {', '.join(filter.exclude_sources)}")
        else:
            logger.info(f"Filter {filter.name} will monitor all available sources")
        
        pattern = None
        if filter.pattern:
            try:
                pattern = re.compile(f"(?i)({filter.pattern})")
            except re.error as e:
                logger.error(f"Regex error: {e}")

        logger.info(f"Setting up handler with chats: {chats_to_monitor}, blacklist: {is_blacklist}, pattern: {pattern}")
        
        @client.on(events.NewMessage(
            chats=list(chats_to_monitor) if chats_to_monitor else None,
            blacklist_chats=is_blacklist,
            pattern=pattern
        ))
        async def handle_message(event, filter=filter):
            await self._process_message(event, filter)

        self._active_handlers[filter.id] = handle_message
        logger.info(f"Handler set up for filter {filter.name}")

    def _get_filter_state(self, filter: Filter) -> dict:
        """Gets current filter state"""
        return {
            "name": filter.name,
            "prompt": filter.prompt,
            "pattern": filter.pattern,
            "include_sources": filter.include_sources,
            "exclude_sources": filter.exclude_sources,
            "session_id": filter.session_id
        }

    def _has_filter_changed(self, filter: Filter) -> bool:
        """Checks if filter has changed"""
        current_state = self._get_filter_state(filter)
        last_state = self._filter_states.get(filter.id)
        
        if not last_state or current_state != last_state:
            self._filter_states[filter.id] = current_state
            return True
        return False

    async def start_monitoring(self, filter_id: int) -> None:
        """Starts monitoring for a filter"""
        if filter_id in self._monitored_filters:
            return

        filter = self.db.query(Filter).filter(Filter.id == filter_id).first()
        if not filter:
            logger.warning(f"Filter with ID {filter_id} not found")
            return

        await self._setup_filter_handler(filter)
        self._monitored_filters.add(filter_id)
        self._filter_states[filter_id] = self._get_filter_state(filter)
        logger.info(f"Started monitoring for filter {filter.name}")

    async def stop_monitoring(self, filter_id: int) -> None:
        """Stops monitoring for a filter"""
        if filter_id not in self._monitored_filters:
            return

        if filter_id in self._active_handlers:
            handler = self._active_handlers[filter_id]
            if filter_id in self._clients:
                client = self._clients[filter_id]
                client.remove_event_handler(handler)
                await client.disconnect()
                del self._clients[filter_id]
            del self._active_handlers[filter_id]
            logger.info(f"Stopped monitoring for filter {filter_id}")

        self._monitored_filters.remove(filter_id)
        if filter_id in self._filter_states:
            del self._filter_states[filter_id]

    async def start(self) -> None:
        """Starts the main monitoring loop"""
        logger.info("Starting monitoring")
        while True:
            try:
                filters = self.db.query(Filter).all()
                current_filter_ids = {f.id for f in filters}

                for filter_id in list(self._monitored_filters):
                    if filter_id not in current_filter_ids:
                        await self.stop_monitoring(filter_id)

                for filter in filters:
                    if filter.id in self._monitored_filters:
                        if self._has_filter_changed(filter):
                            logger.info(f"Filter {filter.name} has been updated, restarting monitoring")
                            await self.stop_monitoring(filter.id)
                            await self.start_monitoring(filter.id)
                    else:
                        await self.start_monitoring(filter.id)

                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)

    async def stop(self) -> None:
        """Stops monitoring"""
        logger.info("Stopping monitoring")
        for filter_id in list(self._monitored_filters):
            await self.stop_monitoring(filter_id) 
