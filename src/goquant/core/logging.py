import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Rotating log file: 5mb max with 5 backups
log_file = os.path.join(LOG_DIR, "app.log")
handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=5)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(), handler],
)

logger = logging.getLogger(__name__)
