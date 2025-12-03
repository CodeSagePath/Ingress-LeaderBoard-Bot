"""
Logger configuration for Ingress Prime leaderboard bot.

This module sets up comprehensive logging with file rotation,
different log levels, and structured logging.
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional
from pathlib import Path


def setup_logger(level: str = "INFO",
                log_file: str = "bot.log",
                max_file_size_mb: int = 10,
                backup_count: int = 5,
                format_string: Optional[str] = None) -> logging.Logger:
    """
    Set up application logger with file rotation.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_file_size_mb: Maximum log file size in MB
        backup_count: Number of backup files to keep
        format_string: Custom log format string

    Returns:
        Configured logger instance
    """
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Default format if not provided
    if not format_string:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create formatter
    formatter = logging.Formatter(format_string)

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,  # Convert MB to bytes
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Configure specific loggers
    _configure_specific_loggers(root_logger, numeric_level, formatter)

    return root_logger


def _configure_specific_loggers(root_logger: logging.Logger,
                              level: int,
                              formatter: logging.Formatter) -> None:
    """
    Configure loggers for specific components with appropriate levels.

    Args:
        root_logger: Root logger to add handlers to
        level: Base logging level
        formatter: Log formatter to use
    """
    # Telegram bot logging (can be very verbose)
    telegram_logger = logging.getLogger('telegram')
    telegram_logger.setLevel(max(level, logging.WARNING))  # Never below WARNING

    # SQLAlchemy logging (very verbose in DEBUG mode)
    sqlalchemy_logger = logging.getLogger('sqlalchemy')
    sqlalchemy_logger.setLevel(max(level, logging.WARNING))  # Never below WARNING

    # Application components
    app_components = [
        'src.bot',
        'src.parsers',
        'src.database',
        'src.leaderboard',
        'src.config'
    ]

    for component in app_components:
        component_logger = logging.getLogger(component)
        component_logger.setLevel(level)

    # Third-party libraries
    third_party = [
        'httpx',
        'aiohttp',
        'asyncio',
        'psycopg2'
    ]

    for lib in third_party:
        lib_logger = logging.getLogger(lib)
        lib_logger.setLevel(max(level, logging.WARNING))


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_function_call(func_name: str, level: int = logging.DEBUG) -> None:
    """
    Log function call entry and exit.

    Args:
        func_name: Name of the function being logged
        level: Logging level to use
    """
    logger = logging.getLogger(__name__)
    logger.log(level, f"Entering {func_name}")

    # This would typically be used with a decorator
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.log(level, f"Calling {func_name} with args: {args}, kwargs: {kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.log(level, f"Completed {func_name} successfully")
                return result
            except Exception as e:
                logger.error(f"Error in {func_name}: {e}", exc_info=True)
                raise

        return wrapper

    return decorator


def log_performance(func_name: str, execution_time: float) -> None:
    """
    Log performance information.

    Args:
        func_name: Name of the function or operation
        execution_time: Time taken in seconds
    """
    logger = logging.getLogger(__name__)

    if execution_time < 0.1:
        level = logging.DEBUG
    elif execution_time < 1.0:
        level = logging.INFO
    elif execution_time < 5.0:
        level = logging.WARNING
    else:
        level = logging.ERROR

    logger.log(level, f"Performance: {func_name} took {execution_time:.3f}s")


def log_database_query(query: str, execution_time: float,
                     result_count: Optional[int] = None) -> None:
    """
    Log database query performance.

    Args:
        query: SQL query (truncated for readability)
        execution_time: Query execution time in seconds
        result_count: Number of results returned
    """
    logger = logging.getLogger('src.database')

    # Truncate long queries for readability
    truncated_query = query[:100] + "..." if len(query) > 100 else query

    if execution_time > 1.0:  # Slow queries
        logger.warning(
            f"Slow query ({execution_time:.3f}s): {truncated_query}"
        )
    else:
        logger.debug(
            f"Query ({execution_time:.3f}s): {truncated_query}"
        )

    if result_count is not None:
        logger.debug(f"Query returned {result_count} rows")


def log_bot_event(event_type: str, user_id: Optional[int] = None,
                  chat_id: Optional[int] = None, details: Optional[str] = None) -> None:
    """
    Log significant bot events.

    Args:
        event_type: Type of event (command, message, error, etc.)
        user_id: Telegram user ID
        chat_id: Telegram chat ID
        details: Additional event details
    """
    logger = logging.getLogger('src.bot')

    log_message = f"Event: {event_type}"
    if user_id:
        log_message += f" | User: {user_id}"
    if chat_id:
        log_message += f" | Chat: {chat_id}"
    if details:
        log_message += f" | Details: {details}"

    logger.info(log_message)


def log_error(error: Exception, context: Optional[str] = None,
               user_id: Optional[int] = None) -> None:
    """
    Log error with context information.

    Args:
        error: Exception that occurred
        context: Context where error occurred
        user_id: Associated user ID if applicable
    """
    logger = logging.getLogger(__name__)

    error_message = f"Error: {type(error).__name__}: {error}"
    if context:
        error_message += f" | Context: {context}"
    if user_id:
        error_message += f" | User: {user_id}"

    logger.error(error_message, exc_info=True)


def log_warning(message: str, context: Optional[str] = None) -> None:
    """
    Log warning with context.

    Args:
        message: Warning message
        context: Additional context
    """
    logger = logging.getLogger(__name__)

    if context:
        message = f"{message} | Context: {context}"

    logger.warning(message)


def create_rotating_handler(log_file: str, max_bytes: int,
                          backup_count: int) -> logging.handlers.RotatingFileHandler:
    """
    Create a rotating file handler with specified parameters.

    Args:
        log_file: Path to log file
        max_bytes: Maximum size in bytes before rotation
        backup_count: Number of backup files

    Returns:
        Configured rotating file handler
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    return logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8',
        delay=False
    )


def set_logger_level(logger_name: str, level: str) -> None:
    """
    Dynamically change logging level for a specific logger.

    Args:
        logger_name: Name of the logger to modify
        level: New logging level
    """
    try:
        logger = logging.getLogger(logger_name)
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)

        get_logger(__name__).info(f"Set {logger_name} level to {level.upper()}")
    except Exception as e:
        get_logger(__name__).error(f"Failed to set logger level: {e}")


def configure_third_party_loggers(level: str = "WARNING") -> None:
    """
    Configure logging levels for common third-party libraries.

    Args:
        level: Maximum log level for third-party loggers
    """
    numeric_level = getattr(logging, level.upper(), logging.WARNING)

    third_party_loggers = [
        'telegram',
        'telegram.ext',
        'telegram.bot',
        'httpx',
        'aiohttp',
        'asyncio',
        'urllib3',
        'requests'
    ]

    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).setLevel(numeric_level)


# Performance monitoring decorator
def monitor_performance(level: str = "INFO"):
    """
    Decorator to monitor function performance.

    Args:
        level: Logging level for performance messages
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                log_performance(f"{func.__module__}.{func.__name__}", execution_time)

        return wrapper
    return decorator


def simple_setup_logger(settings: Optional[object] = None) -> logging.Logger:
    """
    Simple logger setup function that provides an easy interface while maintaining
    production safety features like file rotation.

    This function addresses the common logging setup pattern while preserving
    the robust features of the existing system.

    Args:
        settings: Optional settings object. If not provided, will use Settings()

    Returns:
        Configured logger instance for the IngressLeaderboardBot

    Example:
        # Simple usage - just get a configured logger
        from src.utils.logger import simple_setup_logger
        logger = simple_setup_logger()
        logger.info("Bot started successfully")

        # With custom settings
        from src.config.settings import Settings
        custom_settings = Settings()
        custom_settings.logging.basic_mode = True
        logger = simple_setup_logger(custom_settings)
    """
    # Import settings here to avoid circular imports
    if settings is None:
        from src.config.settings import get_settings
        settings = get_settings()

    # Determine if we should use basic mode
    is_basic_mode = getattr(settings.logging, 'basic_mode', False)

    if is_basic_mode:
        # Basic mode: simplified configuration but still with file rotation
        return setup_logger(
            level=settings.logging.level,
            log_file=settings.logging.log_file,
            max_file_size_mb=settings.logging.max_file_size_mb,
            backup_count=settings.logging.backup_count,
            format_string="%(asctime)s - %(levelname)s - %(message)s"  # Simpler format
        )
    else:
        # Full mode: use the comprehensive existing setup
        return setup_logger(
            level=settings.logging.level,
            log_file=settings.logging.log_file,
            max_file_size_mb=settings.logging.max_file_size_mb,
            backup_count=settings.logging.backup_count,
            format_string=settings.logging.format
        )


def get_bot_logger() -> logging.Logger:
    """
    Get the main bot logger instance.

    Returns:
        Logger instance configured for the IngressLeaderboardBot

    Example:
        from src.utils.logger import get_bot_logger
        logger = get_bot_logger()
        logger.info("Processing command from user")
    """
    return logging.getLogger('IngressLeaderboardBot')