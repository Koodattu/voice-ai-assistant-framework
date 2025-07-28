import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Ensure the logs directory exists
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

# Define log file path
LOG_FILE = os.path.join(LOG_DIR, 'system.log')

# Create a custom logger
logger = logging.getLogger('SystemLogger')
logger.setLevel(logging.DEBUG)  # Capture all levels of logs

# Module-level flag to prevent multiple handler additions
if not hasattr(logger, '_handlers_initialized'):
    # Create console handler with UTF-8 encoding
    try:
        # Attempt to set encoding via constructor (supported in Python 3.9+)
        console_handler = logging.StreamHandler(sys.stdout, encoding='utf-8')
    except TypeError:
        # Fallback for older Python versions where encoding isn't supported in constructor
        import io
        console_stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        console_handler = logging.StreamHandler(console_stream)

    console_handler.setLevel(logging.INFO)  # Only show INFO and above in console
    console_handler.setFormatter(logging.Formatter('%(message)s'))

    # Create file handler which logs even debug messages
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Log all details to file
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Mark handlers as initialized
    logger._handlers_initialized = True
