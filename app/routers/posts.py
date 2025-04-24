from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel

from ..core.database import get_db
from ..core.auth import verify_api_token
from ..models.models import Post, Channel, APIToken
from ..schemas.schemas import Post as PostSchema
from ..core.config import get_settings

settings = get_settings()

class TimePeriod(str, Enum):
    """Predefined time periods for post filtering"""
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
    prefix="/posts",
    tags=["Posts"],
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
        query = query.filter(Post.date >= from_date)
    if to_date:
        query = query.filter(Post.date <= to_date)
    
    return query


@router.get("/", 
    response_model=List[PostSchema],
    summary="Get all posts",
    description="Retrieve a list of posts with optional date filtering and pagination",
    response_description="List of posts matching the criteria"
)
async def read_posts(
    skip: int = Query(settings.API_PAGINATION_DEFAULT_SKIP, ge=0, description="Number of records to skip", example=0),
    limit: int = Query(settings.API_PAGINATION_DEFAULT_LIMIT, ge=1, le=settings.API_PAGINATION_MAX_LIMIT, description="Maximum number of records to return", example=100),
    from_date: Optional[datetime] = Query(None, description="Filter posts from this date (ISO format)", example="2024-03-01T00:00:00"),
    to_date: Optional[datetime] = Query(None, description="Filter posts until this date (ISO format)", example="2024-03-20T00:00:00"),
    period: Optional[TimePeriod] = Query(None, description="Predefined time period for filtering", example=TimePeriod.WEEK),
    db: Session = Depends(get_db),
    api_token: APIToken = Depends(verify_api_token)
):
    """
    Get all posts with optional date filtering.
    
    Parameters:
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (pagination)
    - **from_date**: Filter posts from this date (ISO format)
    - **to_date**: Filter posts until this date (ISO format)
    - **period**: Predefined time period (day, week, month)
    
    Returns:
    - List of posts matching the criteria
    """
    query = db.query(Post).select_from(Post).join(
        Channel,
        Post.channel_id == Channel.id
    ).filter(
        Channel.session_id == api_token.telegram_session_id
    )
    
    query = apply_date_filters(query, from_date, to_date, period)
    return query.offset(skip).limit(limit).all()


@router.get("/channels/{channel_id}/posts", 
    response_model=List[PostSchema],
    summary="Get channel posts",
    description="Retrieve all posts from a specific channel with optional date filtering",
    response_description="List of posts from the specified channel"
)
async def read_posts_by_channel(
    channel_id: int = Path(..., description="ID of the channel", example=123),
    skip: int = Query(settings.API_PAGINATION_DEFAULT_SKIP, ge=0, description="Number of records to skip", example=0),
    limit: int = Query(settings.API_PAGINATION_DEFAULT_LIMIT, ge=1, le=settings.API_PAGINATION_MAX_LIMIT, description="Maximum number of records to return", example=100),
    from_date: Optional[datetime] = Query(None, description="Filter posts from this date (ISO format)", example="2024-03-01T00:00:00"),
    to_date: Optional[datetime] = Query(None, description="Filter posts until this date (ISO format)", example="2024-03-20T00:00:00"),
    period: Optional[TimePeriod] = Query(None, description="Predefined time period for filtering", example=TimePeriod.WEEK),
    db: Session = Depends(get_db),
    api_token: APIToken = Depends(verify_api_token)
):
    """
    Gets all posts for a specific channel with date filtering.
    
    Parameters:
    - **channel_id**: ID of the channel
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (pagination)
    - **from_date**: Filter posts from this date (ISO format)
    - **to_date**: Filter posts until this date (ISO format)
    - **period**: Predefined time period (day, week, month)
    
    Returns:
    - List of posts from the specified channel
    """
    query = db.query(Post).select_from(Post).join(
        Channel,
        Post.channel_id == Channel.id
    ).filter(
        Post.channel_id == channel_id,
        Channel.session_id == api_token.telegram_session_id
    )
    
    query = apply_date_filters(query, from_date, to_date, period)
    return query.offset(skip).limit(limit).all()


@router.get("/topics/{topic_id}/posts", 
    response_model=List[PostSchema],
    summary="Get topic posts",
    description="Retrieve all posts from a specific topic with optional date filtering",
    response_description="List of posts from the specified topic"
)
async def read_posts_by_topic(
    topic_id: int = Path(..., description="ID of the topic", example=456),
    skip: int = Query(settings.API_PAGINATION_DEFAULT_SKIP, ge=0, description="Number of records to skip", example=0),
    limit: int = Query(settings.API_PAGINATION_DEFAULT_LIMIT, ge=1, le=settings.API_PAGINATION_MAX_LIMIT, description="Maximum number of records to return", example=100),
    from_date: Optional[datetime] = Query(None, description="Filter posts from this date (ISO format)", example="2024-03-01T00:00:00"),
    to_date: Optional[datetime] = Query(None, description="Filter posts until this date (ISO format)", example="2024-03-20T00:00:00"),
    period: Optional[TimePeriod] = Query(None, description="Predefined time period for filtering", example=TimePeriod.WEEK),
    db: Session = Depends(get_db),
    api_token: APIToken = Depends(verify_api_token)
):
    """
    Gets all posts for a specific topic with date filtering.
    
    Parameters:
    - **topic_id**: ID of the topic
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (pagination)
    - **from_date**: Filter posts from this date (ISO format)
    - **to_date**: Filter posts until this date (ISO format)
    - **period**: Predefined time period (day, week, month)
    
    Returns:
    - List of posts from the specified topic
    """
    query = db.query(Post).select_from(Post).join(
        Channel,
        Post.channel_id == Channel.id
    ).filter(
        Post.topic_id == topic_id,
        Channel.session_id == api_token.telegram_session_id
    )
    
    query = apply_date_filters(query, from_date, to_date, period)
    return query.offset(skip).limit(limit).all()


@router.get("/{post_id}", 
    response_model=PostSchema,
    summary="Get post by ID",
    description="Retrieve a specific post by its ID",
    response_description="The requested post",
    responses={
        404: {"description": "Post not found"}
    }
)
async def read_post(
    post_id: int = Path(..., description="ID of the post", example=789),
    db: Session = Depends(get_db),
    api_token: APIToken = Depends(verify_api_token)
):
    """
    Get a specific post by ID.
    
    Parameters:
    - **post_id**: ID of the post to retrieve
    
    Returns:
    - The requested post
    
    Raises:
    - 404: Post not found
    """
    post = db.query(Post).select_from(Post).join(
        Channel,
        Post.channel_id == Channel.id
    ).filter(
        Post.id == post_id,
        Channel.session_id == api_token.telegram_session_id
    ).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.delete("/{post_id}",
    summary="Delete post",
    description="Delete a specific post by its ID",
    response_description="Success message",
    responses={
        404: {"description": "Post not found"},
        200: {"description": "Post deleted successfully"}
    }
)
async def delete_post(
    post_id: int = Path(..., description="ID of the post to delete", example=789),
    db: Session = Depends(get_db),
    api_token: APIToken = Depends(verify_api_token)
):
    """
    Delete a post.
    
    Parameters:
    - **post_id**: ID of the post to delete
    
    Returns:
    - Success message
    
    Raises:
    - 404: Post not found
    """
    post = db.query(Post).select_from(Post).join(
        Channel,
        Post.channel_id == Channel.id
    ).filter(
        Post.id == post_id,
        Channel.session_id == api_token.telegram_session_id
    ).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}
