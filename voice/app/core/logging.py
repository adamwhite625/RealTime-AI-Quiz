import logging
import os
import sys
from app.core.settings import settings


def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger
    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root.addHandler(console_handler)

    # File handler (if LOG_DIR exists or can be created)
    try:
        os.makedirs(settings.LOG_DIR, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(settings.LOG_DIR, "voice_app.log"), encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root.addHandler(file_handler)
    except Exception as exc:
        logging.warning("Could not initialize file logging: %s", exc)

    # Configure uvicorn loggers
    for name in ("uvicorn", "uvicorn.error"):
        u_logger = logging.getLogger(name)
        u_logger.handlers.clear()
        u_logger.propagate = True

    logging.getLogger("uvicorn.access").disabled = False
