import logging

logger = logging.getLogger(__name__)

from app.database import SessionLocal
from app.models import ConflictData

import csv
from sqlalchemy.orm import Session
from typing import Type

def truncate_table(model: Type, db: Session = SessionLocal()) -> None:
    '''
    Delete all rows from the table corresponding to the given SQLAlchemy model.
    Useful function to ensure idempotent loads of sample data
    '''
    db.query(model).delete(synchronize_session=False)
    db.commit()
    logger.info(f'Truncated table {model.__tablename__}')


def select_all(model: Type, db: Session = SessionLocal(), sort_col: str = None) -> None:
    '''
    Print all rows from the model's table, ordered by the first column.
    '''
    if sort_col:
        rows = db.query(model).order_by(sort_col).all()
    else:
        rows = db.query(model).all()
    
    logger.info(f'***\n{model.__tablename__} table rows:')
    for row in rows:
        print('\t', row)


def count_all(model: Type, db: Session = SessionLocal()) -> None:
    '''
    Print the row count for a model's table.
    '''
    count = db.query(model).count()
    logger.info(f'{model.__tablename__} table count: {count}')


def insert_dummies(dummy_path: str, table: Type, sort_keys: dict, db: Session = SessionLocal()) -> None:
    with open(dummy_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        # Sort before import so that IDs are predictable. Allow for mixed string/numeric sorts
        rows_sorted = sorted(rows, key=lambda r: tuple(
            [r[k].lower() for k in sort_keys.get('string', [])] + 
            [r[k] for k in sort_keys.get('numeric', [])]
        ))
        logger.debug(f'Inserting dummy data into table {table.__tablename__} from {dummy_path}')
        if table == ConflictData:
            for row in rows_sorted:
                db.add(
                    ConflictData(
                        country=row['country'],
                        admin1=row['admin1'],
                        population=int(row['population']) if row['population'] else None,
                        events=int(row['events']),
                        risk_score=int(row['risk_score'])
                    )
                )
            # Flush to get new PKs
            logger.debug(f'Inserted {rows_sorted} rows, flushing to get PKs')
            db.flush()
            db.commit()
            db.close()
        else:
            logger.warning(f'Please define insert logic for table {table.__tablename__}')
    logger.info(f'Inserted dummy data into table {table.__tablename__}')
