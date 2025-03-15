"""Logging utilities for pod-tenuki."""
import logging
import sys
from pathlib import Path

def setup_logger(name: str = "pod_tenuki", level: int = logging.INFO) -> logging.Logger:
    """
    Set up and configure a logger.

    Args:
        name: Name of the logger.
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

def add_file_handler(
    logger: logging.Logger,
    log_file: str,
    level: int = logging.DEBUG
) -> logging.Logger:
    """
    Add a file handler to an existing logger.

    Args:
        logger: Logger instance.
        log_file: Path to the log file.
        level: Logging level for the file handler.

    Returns:
        Logger with file handler added.
    """
    # Create directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger
