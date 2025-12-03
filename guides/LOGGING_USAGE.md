# Logging Usage Guide

This guide shows how to use the enhanced logging system in the Ingress Leaderboard Bot.

## Quick Start

The logging system now provides a simple interface while maintaining production safety features.

### Basic Usage (Recommended for most cases)

```python
from src.utils.logger import simple_setup_logger

# Get a configured logger with default settings
logger = simple_setup_logger()
logger.info("Bot started successfully")
logger.error("Something went wrong")
```

### Basic Mode with Environment Variable

Set this in your `.env` file:
```bash
LOG_BASIC_MODE=true
LOG_LEVEL=INFO
LOG_FILE=bot.log
```

Then use it in your code:
```python
from src.utils.logger import simple_setup_logger

logger = simple_setup_logger()
# Uses simplified format: "2024-01-01 12:00:00 - INFO - Bot started successfully"
logger.info("Bot started successfully")
```

## Configuration Options

### Environment Variables

```bash
# Basic logging settings
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=bot.log                 # Log file path
LOG_BASIC_MODE=false             # true = simplified format, false = full format

# Advanced settings (for production)
LOG_MAX_FILE_SIZE_MB=10          # Rotate log file after this size
LOG_BACKUP_COUNT=5               # Number of backup files to keep
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Programmatic Configuration

```python
from src.config.settings import Settings
from src.utils.logger import simple_setup_logger

# Create custom settings
settings = Settings()
settings.logging.basic_mode = True
settings.logging.level = "DEBUG"

# Use custom settings
logger = simple_setup_logger(settings)
logger.debug("This will be logged")
```

## Usage Examples

### 1. Basic Bot Command Handler

```python
from src.utils.logger import get_bot_logger

logger = get_bot_logger()

async def handle_start_command(update, context):
    logger.info(f"Start command received from user {update.effective_user.id}")
    await update.message.reply_text("Welcome to the Ingress Leaderboard Bot!")
    logger.info("Start command response sent successfully")
```

### 2. Error Logging with Context

```python
from src.utils.logger import log_error, get_bot_logger

logger = get_bot_logger()

try:
    # Some operation that might fail
    result = process_user_data(data)
except ValueError as e:
    # Log error with context
    log_error(e, context="Processing user data", user_id=user_id)
    await update.message.reply_text("Sorry, there was an error processing your data.")
```

### 3. Performance Monitoring

```python
from src.utils.logger import monitor_performance

@monitor_performance()
def expensive_calculation(data):
    # Complex calculation here
    return result

# This will automatically log:
# "Performance: src.handlers.expensive_calculation took 0.234s"
```

### 4. Database Query Logging

```python
from src.utils.logger import log_database_query
import time

start_time = time.time()
result = db_session.execute(query)
execution_time = time.time() - start_time

log_database_query(str(query), execution_time, len(result.fetchall()))
```

## Logging Modes

### Basic Mode (`LOG_BASIC_MODE=true`)

**Format:** `2024-01-01 12:00:00 - INFO - Your message`

- Simple, clean format
- Easier to read for development
- Still includes file rotation and safety features
- Recommended for development and simple bots

### Full Mode (`LOG_BASIC_MODE=false` - default)

**Format:** `2024-01-01 12:00:00,123 - src.bot.handlers - INFO - Your message`

- Includes module name
- Includes milliseconds
- Better for debugging complex applications
- Includes all production features

## Production Safety Features

The logging system automatically includes these safety features:

1. **File Rotation**: Prevents disk space issues by rotating log files
2. **Third-party Filtering**: Reduces noise from libraries like telegram and sqlalchemy
3. **Error Context**: Automatically includes stack traces for errors
4. **Performance Monitoring**: Built-in timing for function execution
5. **Character Encoding**: UTF-8 encoding for international characters

## Migration from Simple Logging

If you were using the basic logging pattern you requested:

```python
# Old way (not recommended - lacks file rotation)
import logging
import sys
from src.config.settings import Settings

def setup_logger():
    logging.basicConfig(
        level=getattr(logging, Settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),      # No rotation!
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('IngressLeaderboardBot')
```

**New enhanced way:**
```python
# New way (recommended - includes all safety features)
from src.utils.logger import simple_setup_logger

logger = simple_setup_logger()  # Just one line!
```

## Best Practices

1. **Use `get_bot_logger()`** for consistent logger naming
2. **Log at appropriate levels** - DEBUG for development, INFO for production
3. **Include context in error logs** using `log_error()`
4. **Monitor performance** with the `@monitor_performance` decorator
5. **Use basic mode** during development for cleaner output
6. **Use full mode** in production for detailed debugging

## Troubleshooting

### Logs Not Appearing

Check that the logging level is set correctly:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)  # Show all messages
```

### Log File Not Created

Ensure the log directory exists and is writable:
```bash
# Create logs directory if needed
mkdir -p logs
chmod 755 logs
```

### Too Many Logs from Libraries

The system automatically filters third-party libraries. If you see too much noise, set basic mode:
```bash
LOG_BASIC_MODE=true
```

## Environment Configuration

Create a `.env` file in your project root:

```bash
# Basic logging configuration
LOG_LEVEL=INFO
LOG_FILE=bot.log
LOG_BASIC_MODE=false

# Advanced settings (optional)
LOG_MAX_FILE_SIZE_MB=10
LOG_BACKUP_COUNT=5
```

Then run your bot - the logging system will automatically use these settings.