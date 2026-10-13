import logging
import os
from datetime import datetime

# Logs directory setup
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Fixed daily log file name taaki baar-baar nayi files na banein
LOG_FILE = f"pxe_portal_{datetime.now().strftime('%Y_%m_%d')}.log"
LOG_FILE_PATH = os.path.join(LOG_DIR, LOG_FILE)

# Advanced Logging Configuration (File + Console Handlers)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Prevent duplicate handlers if re-initialized
if not logger.handlers:
    # File Handler
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter("[ %(asctime)s ] %(lineno)d %(levelname)s - %(name)s - %(message)s")
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    # Console Handler (Terminal Output)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter("[ %(asctime)s ] %(levelname)s - %(message)s")
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)