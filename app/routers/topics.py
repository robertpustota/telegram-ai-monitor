from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import verify_api_token
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/topics", tags=["Topics"])

@router.post("/", response_model=schemas.Topic)
def create_topic(
    topic: schemas.TopicCreate,
    db: Session = Depends(get_db),
    api_token: models.APIToken = Depends(verify_api_token)
):
    """Create a new topic"""
    topic_data = {
        "name": topic.name,
        "description": topic.description
    }
    
    db_topic = models.Topic(**topic_data)
    
    if topic.channel_usernames:
        channels_to_add = []
        for username in topic.channel_usernames:
            channel = db.query(models.Channel).filter(
                models.Channel.username == username,
                models.Channel.session_id == api_token.telegram_session_id
            ).first()
            
            if not channel:
                channel = models.Channel(
                    username=username,
                    session_id=api_token.telegram_session_id
                )
                db.add(channel)
                db.flush()
            
            channels_to_add.append(channel)
        
        db_topic.channels.extend(channels_to_add)
    
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic


@router.get("/", response_model=List[schemas.Topic])
def read_topics(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    api_token: models.APIToken = Depends(verify_api_token)
):
    """Get all topics with optional filtering by channel"""
    topics = db.query(models.Topic).select_from(models.Topic).join(
        models.topic_channels
    ).join(
        models.Channel,
        models.topic_channels.c.channel_id == models.Channel.id
    ).filter(
        models.Channel.session_id == api_token.telegram_session_id
    ).offset(skip).limit(limit).all()
    
    # Добавляем username'ы каналов к каждому топику
    for topic in topics:
        topic.channel_usernames = [channel.username for channel in topic.channels]
    
    return topics

@router.get("/{topic_id}", response_model=schemas.Topic)
def read_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    api_token: models.APIToken = Depends(verify_api_token)
):
    """Get a specific topic by ID"""
    topic = db.query(models.Topic).select_from(models.Topic).join(
        models.topic_channels
    ).join(
        models.Channel,
        models.topic_channels.c.channel_id == models.Channel.id
    ).filter(
        models.Topic.id == topic_id,
        models.Channel.session_id == api_token.telegram_session_id
    ).first()
    
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Добавляем username'ы каналов к топику
    topic.channel_usernames = [channel.username for channel in topic.channels]
    
    return topic

@router.put("/{topic_id}/channels", response_model=schemas.Topic)
def add_channels_to_topic(
    topic_id: int,
    channels: schemas.ChannelUsernames,
    db: Session = Depends(get_db),
    api_token: models.APIToken = Depends(verify_api_token)
):
    """Add new channels to existing topic"""
    topic = db.query(models.Topic).select_from(models.Topic).join(
        models.topic_channels
    ).join(
        models.Channel,
        models.topic_channels.c.channel_id == models.Channel.id
    ).filter(
        models.Topic.id == topic_id,
        models.Channel.session_id == api_token.telegram_session_id
    ).first()
    
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    for username in channels.channel_usernames:
        channel = db.query(models.Channel).filter(
            models.Channel.username == username,
            models.Channel.session_id == api_token.telegram_session_id
        ).first()
        
        if not channel:
            channel = models.Channel(
                username=username,
                session_id=api_token.telegram_session_id
            )
            db.add(channel)
            db.flush()
        
        if channel not in topic.channels:
            topic.channels.append(channel)
    
    db.commit()
    db.refresh(topic)
    
    # Добавляем username'ы каналов к топику
    topic.channel_usernames = [channel.username for channel in topic.channels]
    
    return topic

@router.delete("/{topic_id}/channels", response_model=schemas.Topic)
def remove_channels_from_topic(
    topic_id: int,
    channels: schemas.ChannelUsernamesDelete,
    db: Session = Depends(get_db),
    api_token: models.APIToken = Depends(verify_api_token)
):
    """Remove channels from existing topic"""
    topic = db.query(models.Topic).select_from(models.Topic).join(
        models.topic_channels
    ).join(
        models.Channel,
        models.topic_channels.c.channel_id == models.Channel.id
    ).filter(
        models.Topic.id == topic_id,
        models.Channel.session_id == api_token.telegram_session_id
    ).first()
    
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    for username in channels.channel_usernames:
        channel = db.query(models.Channel).filter(
            models.Channel.username == username,
            models.Channel.session_id == api_token.telegram_session_id
        ).first()
        
        if channel and channel in topic.channels:
            topic.channels.remove(channel)
    
    db.commit()
    db.refresh(topic)
    
    # Добавляем username'ы каналов к топику
    topic.channel_usernames = [channel.username for channel in topic.channels]
    
    return topic

@router.delete("/{topic_id}")
def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    api_token: models.APIToken = Depends(verify_api_token)
):
    """Delete a topic"""
    topic = db.query(models.Topic).select_from(models.Topic).join(
        models.topic_channels
    ).join(
        models.Channel,
        models.topic_channels.c.channel_id == models.Channel.id
    ).filter(
        models.Topic.id == topic_id,
        models.Channel.session_id == api_token.telegram_session_id
    ).first()
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    db.delete(topic)
    db.commit()
    return {"message": "Topic deleted successfully"} 
