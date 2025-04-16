import os
import logging.config
import sys

import logging

def configure_logging():
    logging.config.fileConfig(
        os.path.join(os.path.dirname(__file__), "logging.ini"),
        defaults={'sys': sys},
        disable_existing_loggers=False,
    )
    logger = logging.getLogger(__name__)
    return logger

logger = configure_logging()