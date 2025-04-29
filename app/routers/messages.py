from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel

from ..core.database import get_db
from ..core.auth import verify_api_token
from ..models.models import Message, Source, APIToken
from ..schemas.schemas import Message as MessageSchema
from ..core.config import get_settings

settings = get_settings()


class TimePeriod(str, Enum):
    """Predefined time periods for message filtering"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class DateFilterParams(BaseModel):
    """Parameters for date-based filtering"""
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    period: Optional[TimePeriod] = None

    class Config:
        json_schema_extra = {
            "example": {
                "from_date": "2024-03-01T00:00:00",
                "to_date": "2024-03-20T00:00:00",
                "period": "week"
            }
        }

router = APIRouter(
    prefix="/messages",
    tags=["Messages"],
    responses={
        404: {"description": "Not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    },
)


def apply_date_filters(query, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, period: Optional[TimePeriod] = None):
    """Helper function to apply date filters to a query"""
    if period:
        now = datetime.now()
        if period == TimePeriod.DAY:
            from_date = now - timedelta(days=1)
        elif period == TimePeriod.WEEK:
            from_date = now - timedelta(weeks=1)
        elif period == TimePeriod.MONTH:
            from_date = now - timedelta(days=30)
        to_date = now
    
    if from_date:
        query = query.filter(Message.date >= from_date)
    if to_date:
        query = query.filter(Message.date <= to_date)
    
    return query


@router.get("/", 
    response_model=List[MessageSchema],
    summary="Get all messages",
    description="Retrieve a list of messages with optional date filtering and pagination",
    response_description="List of messages matching the criteria"
)
async def read_messages(
    skip: int = Query(settings.API_PAGINATION_DEFAULT_SKIP, ge=0, description="Number of records to skip", example=0),
    limit: int = Query(settings.API_PAGINATION_DEFAULT_LIMIT, ge=1, le=settings.API_PAGINATION_MAX_LIMIT, description="Maximum number of records to return", example=100),
    from_date: Optional[datetime] = Query(None, description="Filter messages from this date (ISO format)", example="2024-03-01T00:00:00"),
    to_date: Optional[datetime] = Query(None, description="Filter messages until this date (ISO format)", example="2024-03-20T00:00:00"),
    period: Optional[TimePeriod] = Query(None, description="Predefined time period for filtering", example=TimePeriod.WEEK),
    db: Session = Depends(get_db),
    api_token: APIToken = Depends(verify_api_token)
):
    """
    Get all messages with optional date filtering.
    
    Parameters:
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (pagination)
    - **from_date**: Filter messages from this date (ISO format)
    - **to_date**: Filter messages until this date (ISO format)
    - **period**: Predefined time period (day, week, month)
    
    Returns:
    - List of messages matching the criteria
    """
    query = db.query(Message).select_from(Message).join(
        Source,
        Message.source_id == Source.id
    ).filter(
        Source.session_id == api_token.telegram_session_id
    )
    
    query = apply_date_filters(query, from_date, to_date, period)
    return query.offset(skip).limit(limit).all()


@router.get("/sources/{source_id}/messages", 
    response_model=List[MessageSchema],
    summary="Get source messages",
    description="Retrieve all messages from a specific source with optional date filtering",
    response_description="List of messages from the specified source"
)
async def read_messages_by_source(
    source_id: int = Path(..., description="ID of the source", example=123),
    skip: int = Query(settings.API_PAGINATION_DEFAULT_SKIP, ge=0, description="Number of records to skip", example=0),
    limit: int = Query(settings.API_PAGINATION_DEFAULT_LIMIT, ge=1, le=settings.API_PAGINATION_MAX_LIMIT, description="Maximum number of records to return", example=100),
    from_date: Optional[datetime] = Query(None, description="Filter messages from this date (ISO format)", example="2024-03-01T00:00:00"),
    to_date: Optional[datetime] = Query(None, description="Filter messages until this date (ISO format)", example="2024-03-20T00:00:00"),
    period: Optional[TimePeriod] = Query(None, description="Predefined time period for filtering", example=TimePeriod.WEEK),
    db: Session = Depends(get_db),
    api_token: APIToken = Depends(verify_api_token)
):
    """
    Gets all messages for a specific source with date filtering.
    
    Parameters:
    - **source_id**: ID of the source
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (pagination)
    - **from_date**: Filter messages from this date (ISO format)
    - **to_date**: Filter messages until this date (ISO format)
    - **period**: Predefined time period (day, week, month)
    
    Returns:
    - List of messages from the specified source
    """
    query = db.query(Message).select_from(Message).join(
        Source,
        Message.source_id == Source.id
    ).filter(
        Message.source_id == source_id,
        Source.session_id == api_token.telegram_session_id
    )
    
    query = apply_date_filters(query, from_date, to_date, period)
    return query.offset(skip).limit(limit).all()


@router.get("/filters/{filter_id}/messages", 
    response_model=List[MessageSchema],
    summary="Get filter messages",
    description="Retrieve all messages from a specific filter with optional date filtering",
    response_description="List of messages from the specified filter"
)
async def read_messages_by_filter(
    filter_id: int = Path(..., description="ID of the filter", example=456),
    skip: int = Query(settings.API_PAGINATION_DEFAULT_SKIP, ge=0, description="Number of records to skip", example=0),
    limit: int = Query(settings.API_PAGINATION_DEFAULT_LIMIT, ge=1, le=settings.API_PAGINATION_MAX_LIMIT, description="Maximum number of records to return", example=100),
    from_date: Optional[datetime] = Query(None, description="Filter messages from this date (ISO format)", example="2024-03-01T00:00:00"),
    to_date: Optional[datetime] = Query(None, description="Filter messages until this date (ISO format)", example="2024-03-20T00:00:00"),
    period: Optional[TimePeriod] = Query(None, description="Predefined time period for filtering", example=TimePeriod.WEEK),
    db: Session = Depends(get_db),
    api_token: APIToken = Depends(verify_api_token)
):
    """
    Gets all messages for a specific filter with date filtering.
    
    Parameters:
    - **filter_id**: ID of the filter
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (pagination)
    - **from_date**: Filter messages from this date (ISO format)
    - **to_date**: Filter messages until this date (ISO format)
    - **period**: Predefined time period (day, week, month)
    
    Returns:
    - List of messages from the specified filter
    """
    query = db.query(Message).select_from(Message).join(
        Source,
        Message.source_id == Source.id
    ).filter(
        Message.filter_id == filter_id,
        Source.session_id == api_token.telegram_session_id
    )
    
    query = apply_date_filters(query, from_date, to_date, period)
    return query.offset(skip).limit(limit).all()


@router.get("/{message_id}", 
    response_model=MessageSchema,
    summary="Get message by ID",
    description="Retrieve a specific message by its ID",
    response_description="The requested message",
    responses={
        404: {"description": "Message not found"}
    }
)
async def read_message(
    message_id: int = Path(..., description="ID of the message", example=789),
    db: Session = Depends(get_db),
    api_token: APIToken = Depends(verify_api_token)
):
    """
    Get a specific message by ID.
    
    Parameters:
    - **message_id**: ID of the message to retrieve
    
    Returns:
    - The requested message
    
    Raises:
    - 404: Message not found
    """
    message = db.query(Message).select_from(Message).join(
        Source,
        Message.source_id == Source.id
    ).filter(
        Message.id == message_id,
        Source.session_id == api_token.telegram_session_id
    ).first()
    
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.delete("/{message_id}",
    summary="Delete message",
    description="Delete a specific message by its ID",
    response_description="Success message",
    responses={
        404: {"description": "Message not found"},
        200: {"description": "Message deleted successfully"}
    }
)
async def delete_message(
    message_id: int = Path(..., description="ID of the message to delete", example=789),
    db: Session = Depends(get_db),
    api_token: APIToken = Depends(verify_api_token)
):
    """
    Delete a message.
    
    Parameters:
    - **message_id**: ID of the message to delete
    
    Returns:
    - Success message
    
    Raises:
    - 404: Message not found
    """
    message = db.query(Message).select_from(Message).join(
        Source,
        Message.source_id == Source.id
    ).filter(
        Message.id == message_id,
        Source.session_id == api_token.telegram_session_id
    ).first()
    
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    
    db.delete(message)
    db.commit()
    return {"message": "Message deleted successfully"} 
