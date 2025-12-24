# infrastructure/logging/structured_logging.py

"""
Structured logging with JSON output

Benefits:
- Machine-parseable logs
- Easy filtering/searching
- Rich context
- Integration with log aggregators (ELK, Datadog, etc.)
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
import traceback


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter
    
    Output example:
    {
        "timestamp": "2025-01-15T10:30:45.123Z",
        "level": "INFO",
        "logger": "engine.core.allocators",
        "message": "Allocated user to variant",
        "experiment_id": "exp_123",
        "variant_id": "variant_a",
        "duration_ms": 12.5
    }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        # Base fields
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': ''.join(traceback.format_exception(*record.exc_info))
            }
        
        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add custom fields
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'lineno', 'module', 'msecs', 'message',
                'pathname', 'process', 'processName', 'relativeCreated',
                'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                'extra_fields'
            ]:
                log_data[key] = value
        
        return json.dumps(log_data)


class ContextLogger(logging.LoggerAdapter):
    """
    Logger with context fields
    
    Example:
        >>> logger = ContextLogger(base_logger, {'experiment_id': 'exp_123'})
        >>> logger.info('Allocated user', variant_id='variant_a', duration_ms=12.5)
    """
    
    def process(self, msg, kwargs):
        """Add context to log record"""
        # Merge context with extra fields
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        
        # Add any keyword arguments as extra fields
        extra_fields = {
            k: v for k, v in kwargs.items()
            if k not in ['extra', 'exc_info', 'stack_info']
        }
        extra['extra_fields'] = extra_fields
        
        kwargs['extra'] = extra
        
        return msg, kwargs


def setup_logging(
    level: str = 'INFO',
    json_output: bool = True,
    log_file: str = None
):
    """
    Configure application logging
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_output: Use JSON formatter if True
        log_file: Optional file path for logs
    """
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if json_output:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
    
    # Silence noisy libraries
    logging.getLogger('asyncpg').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logging.info('Logging configured', level=level, json_output=json_output)


# Usage example
def get_logger(name: str, **context) -> ContextLogger:
    """
    Get logger with context
    
    Example:
        >>> logger = get_logger(__name__, experiment_id='exp_123')
        >>> logger.info('User allocated', variant_id='variant_a')
    """
    base_logger = logging.getLogger(name)
    return ContextLogger(base_logger, context)
