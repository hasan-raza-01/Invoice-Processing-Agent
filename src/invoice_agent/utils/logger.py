"""Logging configuration"""
import logging
import os
from datetime import datetime
from pathlib import Path

# Create logs directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Create log filename with timestamp
log_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath = log_dir / log_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_filepath),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("invoice_agent")
