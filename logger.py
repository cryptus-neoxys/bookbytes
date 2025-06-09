#!/usr/bin/env python3
"""
BookBytes Logger Module
Provides structured logging with different log levels, file rotation, and better formatting
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime
from pathlib import Path

# Constants
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_JSON_FORMAT = True
DEFAULT_CONSOLE_OUTPUT = True
DEFAULT_LOG_DIR = 'logs'
DEFAULT_LOG_FILE = 'bookbytes.log'
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add extra fields if available
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data)

class BookBytesLogger:
    """BookBytes Logger class for centralized logging configuration"""
    
    def __init__(self, 
                 name='bookbytes',
                 log_level=None,
                 log_format=DEFAULT_LOG_FORMAT,
                 json_format=DEFAULT_JSON_FORMAT,
                 console_output=DEFAULT_CONSOLE_OUTPUT,
                 log_dir=DEFAULT_LOG_DIR,
                 log_file=DEFAULT_LOG_FILE,
                 max_bytes=DEFAULT_MAX_BYTES,
                 backup_count=DEFAULT_BACKUP_COUNT):
        
        self.name = name
        self.log_level = log_level or os.getenv('LOG_LEVEL', DEFAULT_LOG_LEVEL)
        self.log_format = log_format
        self.json_format = json_format
        self.console_output = console_output
        self.log_dir = Path(log_dir)
        self.log_file = log_file
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # Create logger
        self.logger = logging.getLogger(name)
        
        # Set log level
        self.logger.setLevel(LOG_LEVELS.get(self.log_level.upper(), logging.INFO))
        
        # Remove existing handlers to avoid duplicates
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup log handlers for file and console output"""
        # Create formatters
        if self.json_format:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(self.log_format)
        
        # File handler with rotation
        if self.log_file:
            # Create log directory if it doesn't exist
            self.log_dir.mkdir(exist_ok=True)
            log_file_path = self.log_dir / self.log_file
            
            file_handler = RotatingFileHandler(
                filename=str(log_file_path),
                maxBytes=self.max_bytes,
                backupCount=self.backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def get_logger(self):
        """Get the configured logger instance"""
        return self.logger
    
    def set_level(self, level):
        """Change the log level dynamically"""
        if level.upper() in LOG_LEVELS:
            self.logger.setLevel(LOG_LEVELS[level.upper()])
            self.log_level = level.upper()
            return True
        return False

# Module-level functions for easy access
def get_logger(name='bookbytes', **kwargs):
    """Get a configured logger instance"""
    logger_instance = BookBytesLogger(name=name, **kwargs)
    return logger_instance.get_logger()

def setup_logging(log_level=None, json_format=None, console_output=None, log_dir=None):
    """Setup global logging configuration"""
    # Set default root logger
    root_logger = logging.getLogger()
    
    # Clear existing handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    
    # Create a new BookBytes logger as the root logger
    logger_instance = BookBytesLogger(
        name='root',
        log_level=log_level,
        json_format=json_format if json_format is not None else DEFAULT_JSON_FORMAT,
        console_output=console_output if console_output is not None else DEFAULT_CONSOLE_OUTPUT,
        log_dir=log_dir or DEFAULT_LOG_DIR
    )
    
    # Set the root logger level
    root_logger.setLevel(logger_instance.logger.level)
    
    # Add the handlers from our logger to the root logger
    for handler in logger_instance.logger.handlers:
        root_logger.addHandler(handler)
    
    return root_logger

# Example usage
if __name__ == '__main__':
    # Setup logging
    setup_logging(log_level='DEBUG')
    
    # Get a logger
    logger = get_logger('example')
    
    # Log some messages
    logger.debug('This is a debug message')
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    
    try:
        # Generate an exception
        1 / 0
    except Exception as e:
        logger.exception(f'An error occurred: {e}')
    
    print("\nCheck the logs directory for the log file.")