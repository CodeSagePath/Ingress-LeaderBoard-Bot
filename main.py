"""
Main entry point for Ingress Prime Leaderboard Bot.

This module initializes the Telegram bot, sets up handlers,
and manages the application lifecycle.
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Optional

from telegram import __version__ as telegram_version
from telegram.ext import (
    Application, Defaults, CallbackQueryHandler, CommandHandler,
    MessageHandler, filters, PicklePersistence
)

from src.config.settings import get_settings, print_environment_info, validate_environment
from src.database.connection import initialize_database
from src.utils.logger import setup_logger
from src.bot.handlers import register_handlers


# Set up logger
logger = logging.getLogger(__name__)


class IngressLeaderboardBot:
    """Main bot application class."""

    def __init__(self):
        """Initialize the bot application."""
        self.settings = None
        self.application = None
        self.database = None
        self.running = False

    async def initialize(self) -> None:
        """Initialize all bot components."""
        try:
            # Load and validate settings
            self.settings = get_settings()
            print_environment_info(self.settings)

            # Validate environment
            warnings = validate_environment()
            if warnings:
                for warning in warnings:
                    logger.warning(warning)

            # Initialize database
            logger.info("Initializing database connection...")
            self.database = initialize_database(
                database_url=self.settings.database.url,
                create_tables=True
            )

            # Test database connection
            if not self.database.test_connection():
                raise RuntimeError("Database connection test failed")

            # Initialize Telegram application
            logger.info("Initializing Telegram bot...")
            await self._setup_telegram_application()

            # Register handlers
            logger.info("Registering bot handlers...")
            register_handlers(self.application)

            # Store database reference for handlers
            self.application.bot_data['db_connection'] = self.database
            self.application.bot_data['settings'] = self.settings

            logger.info("Bot initialization completed successfully")

        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise

    async def _setup_telegram_application(self) -> None:
        """Set up the Telegram application with proper configuration."""
        # Configure application defaults
        defaults = Defaults(
            parse_mode='HTML',
            request_timeout=self.settings.telegram.request_timeout,
            read_timeout=self.settings.telegram.read_timeout,
            write_timeout=self.settings.telegram.write_timeout,
            connect_timeout=self.settings.telegram.connect_timeout,
            pool_size=self.settings.telegram.connection_pool_size
        )

        # Create application
        self.application = Application.builder()\
            .token(self.settings.bot.token)\
            .defaults(defaults)\
            .arbitrary_callback_data(True)\
            .build()

        # Set up persistence if needed (for webhook mode)
        if self.settings.bot.webhook_url:
            persistence = PicklePersistence(filepath='bot_data.pickle')
            self.application.persistence = persistence

        # Configure rate limiting
        self.application.updater.rate_limiter = True

    async def start(self) -> None:
        """Start the bot application."""
        if not self.application:
            raise RuntimeError("Bot not initialized. Call initialize() first.")

        if self.running:
            logger.warning("Bot is already running")
            return

        try:
            logger.info("Starting Ingress Prime Leaderboard Bot...")

            # Choose start method based on configuration
            if self.settings.bot.webhook_url:
                await self._start_with_webhook()
            else:
                await self._start_with_polling()

            self.running = True
            logger.info("Bot started successfully")

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise

    async def _start_with_polling(self) -> None:
        """Start bot using long polling."""
        logger.info("Starting bot with polling mode...")

        # Start polling
        await self.application.initialize()
        await self.application.start()

        # Keep bot running
        logger.info("Bot is running with polling. Press Ctrl+C to stop.")
        await self.application.updater.start_polling(
            drop_pending_updates=self.settings.bot.debug
        )

    async def _start_with_webhook(self) -> None:
        """Start bot using webhook."""
        logger.info(f"Starting bot with webhook: {self.settings.bot.webhook_url}")

        # Set up webhook
        await self.application.initialize()
        await self.application.start()
        await self.application.bot.set_webhook(
            url=self.settings.bot.webhook_url,
            port=self.settings.bot.webhook_port,
            drop_pending_updates=self.settings.bot.debug
        )

        logger.info(f"Webhook set up on port {self.settings.bot.webhook_port}")

    async def stop(self) -> None:
        """Stop the bot application gracefully."""
        if not self.running:
            logger.info("Bot is not running")
            return

        try:
            logger.info("Stopping bot...")
            self.running = False

            if self.application:
                await self.application.stop()
                await self.application.shutdown()

            if self.database:
                self.database.close()

            logger.info("Bot stopped successfully")

        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}")

    def setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def run_bot(env_file: Optional[str] = None) -> None:
    """
    Run the bot application.

    Args:
        env_file: Optional path to .env file
    """
    bot = IngressLeaderboardBot()
    bot.setup_signal_handlers()

    try:
        # Initialize bot
        await bot.initialize()

        # Start bot
        await bot.start()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await bot.stop()


def main_simple() -> None:
    """Main entry point for simplified framework mode."""
    # Set up logging first
    try:
        settings = get_settings()
        setup_logger(
            level=settings.logging.level,
            log_file=settings.logging.log_file,
            max_file_size_mb=settings.logging.max_file_size_mb,
            backup_count=settings.logging.backup_count
        )
    except Exception as e:
        print(f"Failed to set up logging: {e}")
        print("Continuing with default logging...")
        logging.basicConfig(level=logging.INFO)

    # Print startup information
    print("Ingress Prime Leaderboard Bot (Simple Framework Mode)")
    print(f"Python-telegram-bot version: {telegram_version}")
    print("=" * 50)

    # Run the simple bot
    try:
        # Import here to avoid circular imports
        from src.bot.bot_framework import IngressLeaderboardBot as SimpleBot

        bot = SimpleBot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Bot failed to start: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the application."""
    # Check which mode to use
    simple_mode = os.getenv('SIMPLE_FRAMEWORK', 'false').lower() == 'true'

    if simple_mode:
        return main_simple()

    # Set up logging first
    try:
        settings = get_settings()
        setup_logger(
            level=settings.logging.level,
            log_file=settings.logging.log_file,
            max_file_size_mb=settings.logging.max_file_size_mb,
            backup_count=settings.logging.backup_count
        )
    except Exception as e:
        print(f"Failed to set up logging: {e}")
        print("Continuing with default logging...")
        logging.basicConfig(level=logging.INFO)

    # Print startup information
    print("Ingress Prime Leaderboard Bot")
    print(f"Python-telegram-bot version: {telegram_version}")
    print("=" * 50)

    # Run the bot
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Bot failed to start: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()