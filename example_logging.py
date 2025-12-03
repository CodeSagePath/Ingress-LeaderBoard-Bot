#!/usr/bin/env python3
"""
Example script demonstrating the enhanced logging system.

This script shows how to use the new simple_setup_logger function
and the different logging modes available.
"""

import os
import sys

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def example_basic_usage():
    """Example of basic logging usage."""
    print("=== Basic Logging Example ===")

    from src.utils.logger import simple_setup_logger

    # Simple setup - just one line!
    logger = simple_setup_logger()

    logger.info("Bot started successfully")
    logger.debug("Debug information")
    logger.warning("This is a warning")
    logger.error("Something went wrong")

    print("Basic logging example completed.\n")

def example_basic_mode():
    """Example of logging in basic mode."""
    print("=== Basic Mode Example ===")

    from src.config.settings import Settings
    from src.utils.logger import simple_setup_logger

    # Create settings with basic mode enabled
    settings = Settings()
    settings.logging.basic_mode = True
    settings.logging.level = "INFO"

    logger = simple_setup_logger(settings)

    logger.info("This message uses simplified format")
    logger.warning("Basic mode makes logs easier to read")

    print("Basic mode example completed.\n")

def example_advanced_features():
    """Example of advanced logging features."""
    print("=== Advanced Features Example ===")

    from src.utils.logger import (
        get_bot_logger,
        log_error,
        log_performance,
        monitor_performance
    )

    logger = get_bot_logger()

    # Use the monitor_performance decorator
    @monitor_performance()
    def slow_function():
        import time
        time.sleep(0.1)  # Simulate slow operation
        return "Operation completed"

    # Test the performance monitoring
    result = slow_function()
    logger.info(result)

    # Test error logging with context
    try:
        # Simulate an error
        raise ValueError("Invalid data received")
    except Exception as e:
        log_error(e, context="Processing user input", user_id=12345)

    # Manual performance logging
    log_performance("custom_operation", 0.05)

    print("Advanced features example completed.\n")

def example_environment_config():
    """Example of using environment configuration."""
    print("=== Environment Configuration Example ===")

    # Set environment variables
    os.environ['LOG_BASIC_MODE'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'

    from src.utils.logger import simple_setup_logger

    # This will use the environment variables
    logger = simple_setup_logger()

    logger.debug("Debug message (visible in DEBUG level)")
    logger.info("This uses environment configuration")

    print("Environment configuration example completed.\n")

def example_comparison():
    """Compare basic mode vs full mode output."""
    print("=== Mode Comparison Example ===")

    from src.config.settings import Settings
    from src.utils.logger import simple_setup_logger

    print("1. Full Mode (Default):")
    settings_full = Settings()
    settings_full.logging.basic_mode = False
    logger_full = simple_setup_logger(settings_full)
    logger_full.info("Full mode includes module name and detailed format")

    print("\n2. Basic Mode:")
    settings_basic = Settings()
    settings_basic.basic_mode = True
    logger_basic = simple_setup_logger(settings_basic)
    logger_basic.info("Basic mode has a cleaner, simpler format")

    print("Mode comparison completed.\n")

def main():
    """Run all examples."""
    print("Ingress Leaderboard Bot - Enhanced Logging System Examples")
    print("=" * 60)

    try:
        example_basic_usage()
        example_basic_mode()
        example_advanced_features()
        example_environment_config()
        example_comparison()

        print("All examples completed successfully!")
        print("\nCheck the bot.log file for the logged output.")

    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()