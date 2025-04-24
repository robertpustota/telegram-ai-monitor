from telethon import TelegramClient
from telethon.sessions import StringSession
from socks import HTTP, SOCKS4, SOCKS5
from typing import Optional

from ..schemas.schemas import ProxyConfig


def create_telegram_client(
    api_id: int,
    api_hash: str,
    proxy: Optional[ProxyConfig] = None
) -> TelegramClient:
    """
    Creates a Telegram client with specified parameters
    
    Args:
        api_id: Telegram application ID
        api_hash: Telegram application hash
        proxy: Proxy configuration (optional)
        
    Returns:
        TelegramClient: Configured Telegram client
    """
    client_params = {
        "api_id": api_id,
        "api_hash": api_hash,
    }

    if proxy:
        proxy_type_map = {
            "http": HTTP,
            "socks4": SOCKS4,
            "socks5": SOCKS5
        }
        proxy_type = proxy_type_map.get(proxy.proxy_type.lower())
        if proxy_type:
            client_params["proxy"] = {
                "proxy_type": proxy_type,
                "addr": proxy.host,
                "port": proxy.port,
                "username": proxy.username,
                "password": proxy.password
            }

    return TelegramClient(StringSession(), **client_params)


def map_proxy_type(proxy_type: str) -> Optional[int]:
    """
    Converts string proxy type to numeric value
    
    Args:
        proxy_type: String proxy type (http, socks4, socks5)
        
    Returns:
        int: Numeric proxy type or None
    """
    return {"http": HTTP, "socks4": SOCKS4, "socks5": SOCKS5}.get(proxy_type.lower()) 
