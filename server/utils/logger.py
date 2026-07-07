import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Log levels
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

# Global logger instance
_logger: Optional[logging.Logger] = None

def setup_logger(
    name: str = "apollo_tyres",
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure a logger
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        format_string: Optional custom format string
    
    Returns:
        Configured logger instance
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
    
    # Default format
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to create file handler: {e}")
    
    _logger = logger
    return logger

def get_logger(name: str = "apollo_tyres") -> logging.Logger:
    """
    Get the configured logger instance
    
    Args:
        name: Logger name (ignored if logger already configured)
    
    Returns:
        Logger instance
    """
    global _logger
    if _logger is None:
        return setup_logger(name)
    return _logger

class LoggerContext:
    """Context manager for temporarily changing log level"""
    
    def __init__(self, logger: logging.Logger, level: str):
        self.logger = logger
        self.level = LOG_LEVELS.get(level.upper(), logging.INFO)
        self.previous_level = None
    
    def __enter__(self):
        self.previous_level = self.logger.level
        self.logger.setLevel(self.level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_level is not None:
            self.logger.setLevel(self.previous_level)

def log_exception(logger: logging.Logger, e: Exception, message: Optional[str] = None):
    """
    Log an exception with full traceback
    
    Args:
        logger: Logger instance
        e: Exception instance
        message: Optional custom message
    """
    import traceback
    msg = message or "Exception occurred"
    logger.error(f"{msg}: {str(e)}")
    logger.debug(traceback.format_exc())

# Convenience functions
def debug(msg: str, *args, **kwargs):
    get_logger().debug(msg, *args, **kwargs)

def info(msg: str, *args, **kwargs):
    get_logger().info(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs):
    get_logger().warning(msg, *args, **kwargs)

def error(msg: str, *args, **kwargs):
    get_logger().error(msg, *args, **kwargs)

def critical(msg: str, *args, **kwargs):
    get_logger().critical(msg, *args, **kwargs)