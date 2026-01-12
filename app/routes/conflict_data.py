import logging
logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Response
from fastapi.security import HTTPBearer

from sqlalchemy import func
import math
from typing import List

from app.database import get_db
from app.models import ConflictData, UserFeedback
from app.auth import get_current_user, require_admin
from app.utils.statistical_utils import compute_cache_risk_score_avg

from pydantic import BaseModel, Field

class FeedbackRequest(BaseModel):
    feedback_text: str = Field(
        ..., 
        min_length=10, 
        max_length=500,
        example='This conflict report seems accurate based on local news sources I\'ve reviewed.'
    )

router = APIRouter(prefix='/conflictdata')
security = HTTPBearer()

@router.get('')
def get_conflict_data(
        offset: int = Query(0, ge=0),
        country: List[str] = Query(None),
        page_size: int = Query(20, ge=1, le=100),
        db: dict = Depends(get_db)
    ):
    '''
    Get data from conflict_data
    Use an optional country list to filter by country or just get all data
    All pulls are paginated with offset and page_size parameters
    '''
    logger.debug(f'Getting conflict data with offset {offset}, page_size {page_size}, countries {country}')
    query_ = db.query(ConflictData)
    ## Get count of rows in db. If countries list passed, update queries to match
    row_count = db.query(func.count(ConflictData.id)).scalar()
    if country:
        query_ = query_.filter(func.lower(ConflictData.country).in_([c.lower() for c in country]))
        row_count = db.query(func.count(ConflictData.id))\
            .filter(func.lower(ConflictData.country).in_([c.lower() for c in country]))\
            .scalar()

    if offset >= row_count:
        raise HTTPException(status_code=404, detail=f'Rows returned: {row_count}. Offset parameter exceeds dataset length')
        
    
    ## Get list of country/admin1 data for the requested page. If country list was passed then
    ## dataset is filtered to that list
    query_result = query_\
        .order_by(func.lower(ConflictData.country), func.lower(ConflictData.admin1))\
        .offset(offset)\
        .limit(page_size).all()
    ## Total number of pages in dataset
    total_pages = math.ceil(row_count / page_size)
    logger.debug(f'returning {len(query_result)} \n\n {[item for item in query_result]}')
    return {
        'rows_returned': row_count, 'offset': offset, 'page_size': page_size, 'total_pages': total_pages,
        'items': [
            {
                'id': i.id,
                'country': i.country,
                'admin1': i.admin1,
                'population': i.population,
                'events': i.events,
                'risk_score': i.risk_score
            } for i in query_result
        ]
    }


@router.get('/{country}')
def get_conflict_data_per_country(country: str, db: dict = Depends(get_db)) -> dict:
    '''
    Get all conflict data for all `admin1` values for a single country
    '''
    # Set arbitrary result set limit for now
    max_rows = 1000
    # Get count of rows to return
    row_count = db.query(func.count(ConflictData.id))\
        .filter(func.lower(ConflictData.country)==country.lower())\
        .scalar()
    if row_count == 0:
        raise HTTPException(status_code=404, detail=f'No data found for "{country}"')
    logger.debug(f'Row count for country {country}: {row_count}')
    
    ## Get list of country/admin1 data for the requested page
    countries = db.query(ConflictData)\
        .filter(func.lower(ConflictData.country)==country.lower())\
        .limit(max_rows).all()
    
    response_items = [
            {
                'id': i.id,
                'country': i.country,
                'admin1': i.admin1,
                'population': i.population,
                'events': i.events,
                'risk_score': i.risk_score
            } for i in countries
        ]
    if row_count > max_rows:
        return {
            'warning': f'Result set restricted to {max_rows} rows. Please use paginated endpoint /conflictdata.',
            'items': response_items
        }
    else:
        return {'rows_returned': row_count, 'items': response_items}


risk_score_averages_cache = {}
@router.get('/{country}/riskscore')
def get_risk_score_average(
    country: str,
    background_tasks: BackgroundTasks,
    db: dict = Depends(get_db),
    response: Response = None
):
    '''Get average risk score for a country, averaging over `admin1`s
    If not already computed, compute it and cache it for future calls'''
    logger.debug(f'Locally cached data: {risk_score_averages_cache}')
    # First quickly check whether country is in dataset. If not we should not add to cache
    row_count = db.query(func.count(ConflictData.id))\
            .filter(func.lower(ConflictData.country)==country.lower())\
            .scalar()
    if row_count == 0:
        raise HTTPException(status_code=404, detail=f'No data found for "{country}"')
    
    # If already cached, simply return value
    if country in risk_score_averages_cache:
        return {'country': country, 'average_risk_score': risk_score_averages_cache[country]}
    
    # If not cached kick off background task and return 202
    background_tasks.add_task(compute_cache_risk_score_avg, country, risk_score_averages_cache, db)
    response.status_code = 202
    return {'detail': f'Computing risk score average for {country}'}


@router.post('/{admin1}/userfeedback')
def write_feedback(
    payload: FeedbackRequest,
    admin1: str,
    country: str = Query(None),
    db: dict = Depends(get_db),
    credentials: HTTPBearer = Depends(security),
    user: dict = Depends(get_current_user),
    response: Response = None
):
    '''Take user feedback for a given admin1 region and write to database table
    If auth fails, no action (handled by Depends(get_current_user))
    If admin1 match not found, return 404
    If multiple found, respond with each id and country to allow user choice'''
     # Build query

    query = db.query(ConflictData).filter(func.lower(ConflictData.admin1) == admin1.lower())
    # Add country filter if provided
    if country:
        query = query.filter(func.lower(ConflictData.country) == country.lower())
    matches = query.all()
    
    if len(matches) == 0:
        raise HTTPException(status_code=404, detail=f"No region found matching '{admin1} '" + \
                                                   (f"and country='{country}'" if country else ""))
    elif len(matches) > 1:
        # Multiple matches - return them for user to choose
        raise HTTPException(
            status_code=422,
            detail={
                'message': f"Multiple regions found for '{admin1}'. Specify ?country=<name> to disambiguate.",
                'matches': [
                    {'id': m.id, 'country': m.country, 'admin1': m.admin1}
                    for m in matches
                ]
            }
        )
    
    # Single match - create feedback
    feedback = UserFeedback(
        user_id=user.id,
        conflict_data_id=matches[0].id,
        feedback_text=payload.feedback_text
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    response.status_code = 201
    return {'message': 'Feedback submitted', 'feedback_id': feedback.id}


@router.delete('')
def delete_conflict_data_row(
    admin1: str = Query(...),
    country: str = Query(...),
    db: dict = Depends(get_db),
    credentials: HTTPBearer = Depends(security),
    user: dict = Depends(require_admin)
):
    '''Delete a single row of data from conflict_data based on admin1 and country'''
    logger.info(f'Admin user {user.email} requested deletion of {admin1}, {country}')
    match_count = db.query(func.count(ConflictData.id))\
        .filter(func.lower(ConflictData.admin1) == admin1.lower())\
        .filter(func.lower(ConflictData.country) == country.lower())\
        .scalar()
        # .filter(ConflictData.admin1 == admin1)\
        # .filter(ConflictData.country == country)\
    
    if match_count == 0:
        raise HTTPException(status_code=404, detail=f"No rows found matching admin1='{admin1}' and country='{country}'")
    else:
        # Single match - proceed with deletion
        row = db.query(ConflictData)\
            .filter(func.lower(ConflictData.admin1) == admin1.lower())\
            .filter(func.lower(ConflictData.country) == country.lower())\
            .first()
            # .filter(ConflictData.admin1 == admin1)\
            # .filter(ConflictData.country == country)\
        db.delete(row)
        db.commit()
        logger.info(f'Deleted row id {row.id} for {admin1}, {country}')
        return {'message': f"Deleted conflict data for admin1='{admin1}' in country='{country}'"}
        
    
    
    
