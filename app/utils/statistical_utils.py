import logging
logger = logging.getLogger(__name__)

from app.models import ConflictData

from sqlalchemy import func
from sqlalchemy.orm import Session

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