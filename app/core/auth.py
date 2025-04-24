from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from ..models.models import APIToken
from ..core.database import get_db

logger = logging.getLogger(__name__)
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_token(api_key: str = Depends(api_key_header), db: Session = Depends(get_db)) -> APIToken:
    """Verifies API token"""
    try:
        token = db.query(APIToken).filter(
            and_(APIToken.token == api_key, APIToken.is_active == True)
        ).first()
        
        if not token:
            logger.warning(f"Invalid token attempt: {api_key[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API token",
                headers={"WWW-Authenticate": "ApiKey"},
            )
            
        return token
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token validation"
        ) 