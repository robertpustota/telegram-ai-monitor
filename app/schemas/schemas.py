from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, ForwardRef
from enum import Enum

from ..models.models import SourceType

class APITokenBase(BaseModel):
    name: str

class APITokenCreate(APITokenBase):
    pass

class APIToken(APITokenBase):
    id: int
    token: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ProxyConfig(BaseModel):
    proxy_type: str = Field(..., description="Тип прокси (socks5, http)")
    host: str = Field(..., description="Хост прокси")
    port: int = Field(..., description="Порт прокси")
    username: Optional[str] = Field(None, description="Имя пользователя прокси")
    password: Optional[str] = Field(None, description="Пароль прокси")

class TelegramSessionBase(BaseModel):
    phone_number: str
    api_id: int = 6 # android creds
    api_hash: str = "eb06d4abfb49dc3eeb1aeb98ae0f581e" # android creds
    proxy: Optional[ProxyConfig] = None

class TelegramSessionCreate(TelegramSessionBase):
    pass

class TelegramAuthRequest(BaseModel):
    phone_number: str
    api_id: int = 6 # android creds
    api_hash: str = "eb06d4abfb49dc3eeb1aeb98ae0f581e" # android creds
    proxy: Optional[ProxyConfig] = None

class TelegramCodeVerify(BaseModel):
    phone_number: str
    code: str
    password: Optional[str] = None

class TelegramSession(BaseModel):
    id: int
    phone_number: str
    api_id: int
    api_hash: str
    proxy_type: Optional[int] = None
    proxy_host: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    api_token: APIToken
    created_at: datetime
    last_used: datetime

    class Config:
        from_attributes = True

class SourceBase(BaseModel):
    username: str
    title: Optional[str] = None
    source_type: SourceType

class SourceCreate(SourceBase):
    pass

class Source(SourceBase):
    id: int
    source_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class FilterBase(BaseModel):
    name: str
    prompt: Optional[str] = Field(None, description="Инструкция для модели о том, какие сообщения обрабатывать")
    pattern: Optional[str] = Field(None)
    include_sources: Optional[List[str]] = Field(default_factory=list)
    exclude_sources: Optional[List[str]] = Field(default_factory=list)

class FilterCreate(FilterBase):
    pass

class Filter(FilterBase):
    id: int
    
    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    text: str
    date: datetime

class MessageCreate(MessageBase):
    source_id: int
    filter_id: Optional[int] = None

class Message(MessageBase):
    id: int
    source_id: int
    filter_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class SourceUsernames(BaseModel):
    source_usernames: List[str] = Field(..., description="Список username'ов источников для добавления")

class SourceUsernamesDelete(BaseModel):
    source_usernames: List[str] = Field(..., description="Список username'ов источников для удаления")

Source.model_rebuild()
Filter.model_rebuild()
Message.model_rebuild() 