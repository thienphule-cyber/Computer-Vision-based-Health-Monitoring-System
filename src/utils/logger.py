import logging
import os
from logging.handlers import RotatingFileHandler

from config import settings

def setup_logging():
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    file_handler = RotatingFileHandler(
        settings.LOG_FILE_PATH,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    logging.getLogger("paho").setLevel(logging.WARNING)
    logging.getLogger(__name__).info(
        f"Logging initialized. Level={settings.LOG_LEVEL}, File={settings.LOG_FILE_PATH}"
    )

if __name__ == "__main__":
    setup_logging()

    logger = logging.getLogger("test_logger")
    logger.debug("This is a DEBUG message (may not show depending on LOG_LEVEL).")
    logger.info("This is an INFO message.")
    logger.warning("This is a WARNING message.")
    logger.error("This is an ERROR message.")

    print(f"\nCheck log file at: {settings.LOG_FILE_PATH}")
