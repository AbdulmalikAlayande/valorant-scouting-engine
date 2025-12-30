"""
Centralized logging configuration for the entire application.

Usage:
    from config.logging import get_logger

    logger = get_logger(__name__)
    logger.info("Processing team data")
    logger.error("Failed to fetch stats", exc_info=True)

The logger writes to both console and a rotating file in logs/ directory.
Configure log level via LOG_LEVEL environment variable (default: INFO).
"""

import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from config.environment import env

# Configuration
LOG_LEVEL = env.str("LOG_LEVEL", default="INFO").upper()
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

# Ensure "logs" directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global flag to prevent duplicate configuration
_configured = False


def configure_root_logger():
    """
    Configure the root logger with console and rotating file handlers.
    Called automatically on first get_logger() invocation. Idempotent.
    """
    global _configured
    if _configured:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Rotating file handler for all logs
    all_logs_file = LOG_DIR / "application.log"
    file_handler = RotatingFileHandler(
        all_logs_file,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _configured = True
    root_logger.info(f"Logging configured: level={LOG_LEVEL}, log_dir={LOG_DIR}")


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a named logger for a module/component. Automatically
    configures root logger on first call. Use __name__ as the name param
    to automatically namespace by module path (e.g., 'ingest.fetch_teams').
    """
    if not _configured:
        configure_root_logger()

    logger = logging.getLogger(name)

    # Optionally add a per-module file handler
    module_log_file = LOG_DIR / f"{name.replace('.', '_')}.log"
    if not any(
        isinstance(h, RotatingFileHandler) and h.baseFilename == str(module_log_file)
        for h in logger.handlers
    ):
        module_handler = RotatingFileHandler(
            module_log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        module_handler.setLevel(logging.DEBUG)
        module_handler.setFormatter(
            logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        )
        logger.addHandler(module_handler)

    return logger


# Convenience: Get a logger for this config module
logger = get_logger(__name__)


if __name__ == "__main__":
    # Test the logging configuration
    test_logger = get_logger("config.logging.test")
    test_logger.debug("Debug message")
    test_logger.info("Info message")
    test_logger.warning("Warning message")
    test_logger.error("Error message")
    test_logger.critical("Critical message")
    print(f"\n✅ Logs written to: {LOG_DIR}")
