import secrets
import string
from typing import Optional
from sqlalchemy.orm import Session

from ..models.models import TelegramSession, APIToken
from ..schemas.schemas import ProxyConfig
from .telegram import map_proxy_type

def generate_api_token(length: int = 32) -> str:
    """
    Generates a random API token
    
    Args:
        length: Token length
        
    Returns:
        str: Generated token
    """
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

def create_telegram_session(
    db: Session,
    phone_number: str,
    session_string: str,
    api_id: int,
    api_hash: str,
    proxy: Optional[ProxyConfig] = None
) -> TelegramSession:
    """
    Creates a new Telegram session in the database
    
    Args:
        db: Database session
        phone_number: Phone number
        session_string: Telegram session string
        api_id: Telegram application ID
        api_hash: Telegram application hash
        proxy: Proxy configuration (optional)
        
    Returns:
        TelegramSession: Created session
    """
    db_session = TelegramSession(
        phone_number=phone_number,
        session_string=session_string,
        api_id=api_id,
        api_hash=api_hash
    )
    
    db_token = APIToken(token=generate_api_token(), name=f"Token for {phone_number}")
    db_session.api_token = db_token
    
    if proxy:
        proxy_type = map_proxy_type(proxy.proxy_type)
        if proxy_type is not None:
            db_session.proxy_type = proxy_type
            db_session.proxy_host = proxy.host
            db_session.proxy_port = proxy.port
            db_session.proxy_username = proxy.username
            db_session.proxy_password = proxy.password
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session 