import logging
import os

def configure_logging():
    level = os.getenv('LOG_LEVEL', 'DEBUG').upper()
    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )