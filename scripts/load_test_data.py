import logging
logger = logging.getLogger(__name__)

from app.database import SessionLocal
from app.models import User, ConflictData
from app.auth import hash_password
from app.utils.sql_utils import truncate_table

import csv

def load_sample_data():
    db = SessionLocal()
    try:
        with open('sample_data.csv') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # Sort before import so that IDs are predictable. Lowercase as eSwatini was sorted to bottom
            rows_sorted = sorted(rows, key=lambda r: (r['country'].lower(), r['admin1'].lower()))
            for row in rows_sorted:
                db.add(
                    ConflictData(
                        country=row['country'],
                        admin1=row['admin1'],
                        population=int(row['population']) if row['population'] else None,
                        events=int(row['events']),
                        risk_score=int(row['score'])
                    )
                )
        db.commit()
    finally:
        db.close()
        logger.info('DB session closed')


def load_test_users():
    '''Create test users for demo purposes'''
    db = SessionLocal()
    try:        
        # Create regular user
        user1 = User(
            email='user1@test.com',
            hashed_password=hash_password('password123'),
            is_admin=False
        )
        
        # Create admin user
        admin = User(
            email='user2@test.com',
            hashed_password=hash_password('password123'),
            is_admin=True
        )
        
        db.add_all([user1, admin])
        db.commit()
        logger.info('Created test users: user1@test.com, user2@test.com')
    finally:
        db.close()


if __name__ == '__main__':
    # Truncate table first, else upload is likely to fail on unique constraints
    truncate_table(ConflictData)
    logger.info('Loading sample conflict data...')
    load_sample_data()
    
    truncate_table(User)
    logger.info('Creating test users...')
    load_test_users()
    
    logger.info('Test data load complete')