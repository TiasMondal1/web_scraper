"""
Centralized logging configuration
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(name: str, log_file: str = None, level=logging.INFO):
    """
    Set up a logger with both console and file handlers
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level
    
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger


# Create default loggers
app_logger = setup_logger('app', 'logs/app.log')
api_logger = setup_logger('api', 'logs/api.log')
scraper_logger = setup_logger('scraper', 'logs/scraper.log')
celery_logger = setup_logger('celery', 'logs/celery.log')
