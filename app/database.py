import logging
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Database URL from env or default to local SQLite file
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data.db')

# Use SQLite-specific connection args when appropriate
connect_args = {'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=os.getenv('DEBUG', 'False') == 'True')

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    '''Yield a database session (dependency for FastAPI).'''
    db = SessionLocal()
    # Try/finally ensures session close even if errors
    try:
        yield db
    finally:
        db.close()
