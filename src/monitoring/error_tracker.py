"""
Error tracking decorator for monitoring system integration.

Provides centralized error handling, logging, and performance tracking
for bot functions and critical operations.
"""

import asyncio
import functools
import logging
import traceback
import time
from typing import Any, Callable, Optional, Dict, Union
from datetime import datetime

logger = logging.getLogger(__name__)


def error_tracking(
    error_type: str = "general",
    component: str = "bot",
    reraise: bool = True,
    default_return: Any = None
):
    """
    Error tracking decorator for monitoring system integration.

    Args:
        error_type: Type of error for categorization (e.g., "command", "database", "parsing")
        component: Component name for monitoring (e.g., "bot_handlers", "parsers", "database")
        reraise: Whether to reraise exceptions after logging
        default_return: Default return value on error (if not reraising)

    Returns:
        Decorated function with error tracking capabilities

    Example:
        @error_tracking(error_type="command", component="bot_handlers")
        async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            # Function implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            function_name = f"{func.__module__}.{func.__name__}"

            # Extract context information if available (for bot functions)
            context_info = _extract_context_info(*args, **kwargs)

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                _record_success_metrics(function_name, component, duration, context_info)
                return result

            except Exception as e:
                duration = time.time() - start_time
                error_context = {
                    'function_name': function_name,
                    'component': component,
                    'error_type': error_type,
                    'duration': duration,
                    'timestamp': datetime.utcnow().isoformat(),
                    'traceback': traceback.format_exc(),
                    'context_info': context_info
                }

                _record_error(error_type, component, str(e), error_context)

                if reraise:
                    raise
                return default_return

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            function_name = f"{func.__module__}.{func.__name__}"

            # Extract context information if available
            context_info = _extract_context_info(*args, **kwargs)

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                _record_success_metrics(function_name, component, duration, context_info)
                return result

            except Exception as e:
                duration = time.time() - start_time
                error_context = {
                    'function_name': function_name,
                    'component': component,
                    'error_type': error_type,
                    'duration': duration,
                    'timestamp': datetime.utcnow().isoformat(),
                    'traceback': traceback.format_exc(),
                    'context_info': context_info
                }

                _record_error(error_type, component, str(e), error_context)

                if reraise:
                    raise
                return default_return

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def _extract_context_info(*args, **kwargs) -> Dict[str, Any]:
    """
    Extract context information from function arguments for better error tracking.

    Args:
        *args: Function positional arguments
        **kwargs: Function keyword arguments

    Returns:
        Dictionary with context information
    """
    context_info = {}

    # Extract Telegram context if available
    for arg in args:
        if hasattr(arg, 'effective_user'):
            # Telegram Update object
            if hasattr(arg, 'effective_user') and arg.effective_user:
                context_info['user_id'] = arg.effective_user.id
                context_info['username'] = arg.effective_user.username
            if hasattr(arg, 'effective_chat') and arg.effective_chat:
                context_info['chat_id'] = arg.effective_chat.id
                context_info['chat_type'] = arg.effective_chat.type
        elif hasattr(arg, 'bot_data'):
            # Telegram Context object - access bot_data as dict
            if hasattr(arg, 'bot_data') and isinstance(arg.bot_data, dict):
                if 'user_id' in arg.bot_data:
                    context_info['user_id'] = arg.bot_data['user_id']
                if 'chat_id' in arg.bot_data:
                    context_info['chat_id'] = arg.bot_data['chat_id']

    # Extract common keyword arguments
    if 'user_id' in kwargs:
        context_info['user_id'] = kwargs['user_id']
    if 'chat_id' in kwargs:
        context_info['chat_id'] = kwargs['chat_id']

    return context_info


def _record_error(error_type: str, component: str, error_message: str, context: Dict[str, Any]) -> None:
    """
    Record error in monitoring system and logging.

    Args:
        error_type: Type of error for categorization
        component: Component name where error occurred
        error_message: Error message
        context: Additional error context information
    """
    try:
        # Create detailed error message for logging
        log_message = f"[{component}] {error_type.upper()}: {error_message}"

        # Log the error with context
        logger.error(
            log_message,
            extra={
                'error_type': error_type,
                'component': component,
                'function_name': context.get('function_name'),
                'duration': context.get('duration'),
                'user_id': context.get('context_info', {}).get('user_id'),
                'chat_id': context.get('context_info', {}).get('chat_id'),
                'traceback': context.get('traceback')
            },
            exc_info=True
        )

        # Try to record in monitoring manager if available
        _record_in_monitoring_manager(error_type, component, context)

    except Exception as e:
        logger.error(f"Failed to record error: {e}")


def _record_success_metrics(function_name: str, component: str, duration: float, context_info: Dict[str, Any]) -> None:
    """
    Record successful function execution metrics.

    Args:
        function_name: Name of the executed function
        component: Component name
        duration: Execution duration in seconds
        context_info: Context information
    """
    try:
        # Log successful execution with performance metrics
        logger.debug(
            f"[{component}] Function {function_name} completed in {duration:.3f}s",
            extra={
                'component': component,
                'function_name': function_name,
                'duration': duration,
                'success': True,
                'user_id': context_info.get('user_id'),
                'chat_id': context_info.get('chat_id')
            }
        )

        # Try to record in monitoring manager if available
        _record_success_in_monitoring_manager(component, function_name, duration, context_info)

    except Exception as e:
        logger.error(f"Failed to record success metrics: {e}")


def _record_in_monitoring_manager(error_type: str, component: str, context: Dict[str, Any]) -> None:
    """
    Record error in MonitoringManager if available.

    This function attempts to find and use the MonitoringManager instance
    to record the error in the metrics system.
    """
    try:
        # Try to get monitoring manager from global context or local imports
        # This is a best-effort approach - if monitoring manager is not available,
        # we still log the error via the regular logging system

        # Import here to avoid circular dependencies
        from .monitoring_manager import MonitoringManager

        # Try to access monitoring manager through various means
        monitoring_manager = None

        # Check if we can find it in the bot_data context
        if 'context_info' in context:
            context_info = context['context_info']
            if hasattr(context_info, 'get'):
                # This would be set if we have access to bot context
                monitoring_manager = context_info.get('monitoring_manager')

        # If we found a monitoring manager, record the error
        if monitoring_manager and hasattr(monitoring_manager, 'record_error'):
            monitoring_manager.record_error(error_type, component)

    except ImportError:
        # MonitoringManager not available, which is fine
        pass
    except Exception as e:
        # Failed to record in monitoring manager, but we already logged it
        logger.debug(f"Could not record error in monitoring manager: {e}")


def _record_success_in_monitoring_manager(component: str, function_name: str, duration: float, context_info: Dict[str, Any]) -> None:
    """
    Record success metrics in MonitoringManager if available.

    Args:
        component: Component name
        function_name: Function name
        duration: Execution duration
        context_info: Context information
    """
    try:
        # Similar to error recording, try to find monitoring manager
        monitoring_manager = None

        if hasattr(context_info, 'get'):
            monitoring_manager = context_info.get('monitoring_manager')

        # If monitoring manager is available, we could record additional metrics
        # For now, the basic logging is sufficient

    except Exception as e:
        logger.debug(f"Could not record success metrics in monitoring manager: {e}")


# Convenience decorators for common use cases
def command_error_tracking(command_name: Optional[str] = None):
    """
    Decorator specifically for Telegram bot command handlers.

    Args:
        command_name: Name of the command (if not provided, will be extracted from function name)

    Example:
        @command_error_tracking("start")
        async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            pass
    """
    def decorator(func: Callable) -> Callable:
        cmd_name = command_name or func.__name__.replace('_command', '').replace('_handler', '')
        return error_tracking(error_type="command", component="bot_handlers")(func)
    return decorator


def database_error_tracking(operation: str = "query"):
    """
    Decorator specifically for database operations.

    Args:
        operation: Type of database operation (query, save, update, delete)

    Example:
        @database_error_tracking("save")
        async def save_agent_stats(self, agent_data: Dict) -> bool:
            pass
    """
    def decorator(func: Callable) -> Callable:
        return error_tracking(error_type=f"database_{operation}", component="database")(func)
    return decorator


def parsing_error_tracking(parser_type: str = "stats"):
    """
    Decorator specifically for parsing operations.

    Args:
        parser_type: Type of parser (stats, message, callback)

    Example:
        @parsing_error_tracking("stats")
        async def parse_stats_message(self, message: str) -> Dict:
            pass
    """
    def decorator(func: Callable) -> Callable:
        return error_tracking(error_type=f"parsing_{parser_type}", component="parsers")(func)
    return decorator