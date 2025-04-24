from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, ForwardRef


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

class TopicBase(BaseModel):
    name: str
    description: Optional[str] = None

class TopicCreate(TopicBase):
    channel_usernames: Optional[List[str]] = None

class Topic(TopicBase):
    id: int
    channel_usernames: List[str] = Field(default_factory=list, description="Список username'ов каналов")
    
    class Config:
        from_attributes = True

class PostBase(BaseModel):
    text: str
    date: datetime

class PostCreate(PostBase):
    channel_id: int
    topic_id: Optional[int] = None

class Post(PostBase):
    id: int
    channel_id: int
    topic_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class ChannelBase(BaseModel):
    username: str
    title: Optional[str] = None


class ChannelCreate(BaseModel):
    username: str
    title: Optional[str] = None


class Channel(ChannelBase):
    id: int
    channel_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class ChannelUsernames(BaseModel):
    channel_usernames: List[str] = Field(..., description="Список username'ов каналов для добавления")


class ChannelUsernamesDelete(BaseModel):
    channel_usernames: List[str] = Field(..., description="Список username'ов каналов для удаления")


Topic.model_rebuild()
Post.model_rebuild()
Channel.model_rebuild() 