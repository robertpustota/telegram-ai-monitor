from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import re

from app.core.database import get_db
from app.core.auth import verify_api_token
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/filters", tags=["Filters"])


def validate_pattern(pattern: str) -> bool:
    """Проверяет, является ли строка валидным регулярным выражением"""
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False


@router.post("/", response_model=schemas.Filter)
def create_filter(
    filter: schemas.FilterCreate,
    db: Session = Depends(get_db),
    api_token: models.APIToken = Depends(verify_api_token)
):
    """Create a new filter"""
    # Валидация паттерна, если он указан
    if filter.pattern and not validate_pattern(filter.pattern):
        raise HTTPException(
            status_code=400,
            detail="Invalid pattern: not a valid regular expression"
        )
    
    filter_data = {
        "name": filter.name,
        "prompt": filter.prompt,
        "pattern": filter.pattern,
        "include_sources": filter.include_sources,
        "exclude_sources": filter.exclude_sources,
        "session_id": api_token.telegram_session_id
    }
    
    db_filter = models.Filter(**filter_data)
    db.add(db_filter)
    db.commit()
    db.refresh(db_filter)
    return db_filter


@router.get("/", response_model=List[schemas.Filter])
def read_filters(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    api_token: models.APIToken = Depends(verify_api_token)
):
    """Get all filters"""
    filters = db.query(models.Filter).offset(skip).limit(limit).all()
    return filters


@router.get("/{filter_id}", response_model=schemas.Filter)
def read_filter(
    filter_id: int,
    db: Session = Depends(get_db),
    api_token: models.APIToken = Depends(verify_api_token)
):
    """Get a specific filter by ID"""
    filter = db.query(models.Filter).filter(
        models.Filter.id == filter_id
    ).first()
    
    if filter is None:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    return filter


@router.put("/{filter_id}/sources", response_model=schemas.Filter)
def update_filter_sources(
    filter_id: int,
    sources: schemas.SourceUsernames,
    db: Session = Depends(get_db),
    api_token: models.APIToken = Depends(verify_api_token)
):
    """Update filter sources with new set of sources"""
    filter = db.query(models.Filter).filter(
        models.Filter.id == filter_id
    ).first()
    
    if filter is None:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    # Update include_sources with new usernames
    filter.include_sources = sources.source_usernames
    
    db.commit()
    db.refresh(filter)
    return filter


@router.delete("/{filter_id}/sources", response_model=schemas.Filter)
def remove_sources_from_filter(
    filter_id: int,
    sources: schemas.SourceUsernamesDelete,
    db: Session = Depends(get_db),
    api_token: models.APIToken = Depends(verify_api_token)
):
    """Remove sources from existing filter"""
    filter = db.query(models.Filter).select_from(models.Filter).join(
        models.filter_sources
    ).join(
        models.Source,
        models.filter_sources.c.source_id == models.Source.id
    ).filter(
        models.Filter.id == filter_id,
        models.Source.session_id == api_token.telegram_session_id
    ).first()
    
    if filter is None:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    for username in sources.source_usernames:
        source = db.query(models.Source).filter(
            models.Source.username == username,
            models.Source.session_id == api_token.telegram_session_id
        ).first()
        
        if source and source in filter.sources:
            filter.sources.remove(source)
    
    db.commit()
    db.refresh(filter)
    return filter


@router.delete("/{filter_id}")
def delete_filter(
    filter_id: int,
    db: Session = Depends(get_db),
    api_token: models.APIToken = Depends(verify_api_token)
):
    """Delete a filter"""
    filter = db.query(models.Filter).filter(
        models.Filter.id == filter_id
    ).first()
    
    if filter is None:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    db.delete(filter)
    db.commit()
    return {"message": "Filter deleted successfully"} 
