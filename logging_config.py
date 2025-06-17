# logging_config.py

import logging

LOG_FILE = "chat_errors.log"

def setup_logger(name=__name__):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.ERROR)  # Log only errors to file

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # Info and above to console

        # Formatter
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
