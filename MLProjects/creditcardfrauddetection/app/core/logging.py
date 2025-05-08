"""
Logging configuration for the fraud detection system.
"""

import logging
import sys
import os
from pathlib import Path
import json
from datetime import datetime

from app.core.config import settings

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging formatters
class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "path": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }
        
        # Add exception info if available
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if available
        if hasattr(record, "extra"):
            log_record.update(record.extra)
        
        return json.dumps(log_record)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",   # Green
        "WARNING": "\033[33m", # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m", # Red background
    }
    RESET = "\033[0m"
    
    def format(self, record):
        """Format log record with colors."""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format)
        message = formatter.format(record)
        
        if record.levelname in self.COLORS:
            message = f"{self.COLORS[record.levelname]}{message}{self.RESET}"
            
        return message

def setup_logging():
    """Set up logging configuration."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler (JSON)
    log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(file_handler)
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Return configured logger
    return root_logger

# Initialize logger
logger = setup_logging()