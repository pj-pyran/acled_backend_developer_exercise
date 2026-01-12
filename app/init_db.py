import logging
logger = logging.getLogger(__name__)
logger.info('message')

from app.database import engine
from app.models import Base

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    init_db()
