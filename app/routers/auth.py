from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from telethon import errors
from typing import Dict

from ..core.database import get_db
from ..models.models import TelegramSession
from ..schemas.schemas import (
    TelegramAuthRequest,
    TelegramCodeVerify,
    TelegramSession as TelegramSessionSchema,
)
from ..utils.telegram import create_telegram_client
from ..utils.auth import create_telegram_session

router = APIRouter(prefix="/auth", tags=["Auth"])
telegram_auth_data: Dict[str, Dict] = {}

@router.post("/request", response_model=TelegramAuthRequest)
async def request_telegram_auth(auth_request: TelegramAuthRequest, db: Session = Depends(get_db)):
    """Requests verification code for Telegram login"""
    if db.query(TelegramSession).filter(TelegramSession.phone_number == auth_request.phone_number).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session already exists")

    client = create_telegram_client(auth_request.api_id, auth_request.api_hash, auth_request.proxy)
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(auth_request.phone_number)
            telegram_auth_data[auth_request.phone_number] = {
                "client": client,
                "proxy": auth_request.proxy,
                "api_id": auth_request.api_id,
                "api_hash": auth_request.api_hash
            }
            return auth_request
        
        session_string = client.session.save()
        db_session = create_telegram_session(
            db, auth_request.phone_number, session_string,
            auth_request.api_id, auth_request.api_hash, auth_request.proxy
        )
        await client.disconnect()
        return db_session
    except errors.PhoneNumberInvalidError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phone number")
    except errors.PhoneNumberBannedError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is banned")
    finally:
        await client.disconnect()

@router.post("/verify", response_model=TelegramSessionSchema)
async def verify_telegram_code(verification: TelegramCodeVerify, db: Session = Depends(get_db)):
    """Verifies code and creates session"""
    auth_data = telegram_auth_data.get(verification.phone_number)
    if not auth_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending verification")

    client = auth_data["client"]
    await client.connect()
    
    try:
        try:
            await client.sign_in(verification.phone_number, verification.code)
        except errors.SessionPasswordNeededError:
            if verification.password:
                await client.sign_in(password=verification.password)
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA password is required")
        
        if not await client.is_user_authorized():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization failed")
            
        session_string = client.session.save()
        db_session = create_telegram_session(
            db, verification.phone_number, session_string,
            auth_data["api_id"], auth_data["api_hash"], auth_data["proxy"]
        )

        del telegram_auth_data[verification.phone_number]
        await client.disconnect()
        return db_session
    except errors.PhoneCodeInvalidError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")
    except errors.PhoneCodeExpiredError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired")
    except errors.PasswordHashInvalidError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA password")
    finally:
        await client.disconnect()