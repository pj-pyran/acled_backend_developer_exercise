import logging
logger = logging.getLogger(__name__)

'''Minimal conflict data and feedback routes'''
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Union, List

from app.database import get_db
from app.models import ConflictData, UserFeedback


# Add this after your compute_risk_score_average function
def compute_cache_risk_score_avg(country: str, cache: dict, db: Session):
    '''Background task: compute average and store in cache dict.'''
    try:
        result = db.query(func.avg(ConflictData.risk_score))\
            .filter(func.lower(ConflictData.country) == country.lower())\
            .scalar()
        
        cache[country] = result
        logger.info(f'Cached risk score for {country}: {result}')
    except Exception as e:
        logger.error(f"Error computing cached risk score for '{country}': {e}")