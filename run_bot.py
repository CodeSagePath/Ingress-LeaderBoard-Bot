#!/usr/bin/env python3
"""
Simple runner for Ingress Prime Leaderboard Bot.
Uses Application.run_polling() which handles all async setup.
"""

import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import __version__ as telegram_version
from telegram.ext import Application, Defaults

from src.config.settings import get_settings
from src.database.connection import initialize_database
from src.bot.handlers import register_handlers

# Set up basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the bot."""
    print("Ingress Prime Leaderboard Bot")
    print(f"Python-telegram-bot version: {telegram_version}")
    print("=" * 50)
    
    # Load settings
    settings = get_settings()
    
    # Initialize database
    logger.info("Initializing database...")
    database = initialize_database(
        database_url=settings.database.url,
        create_tables=True  # Create tables directly without migrations
    )
    
    if not database.test_connection():
        logger.error("Database connection failed!")
        sys.exit(1)
    
    logger.info("Database initialized successfully")
    
    # Build the application
    logger.info("Building Telegram application...")
    defaults = Defaults(parse_mode='HTML')
    
    application = Application.builder()\
        .token(settings.bot.token)\
        .defaults(defaults)\
        .read_timeout(30)\
        .write_timeout(30)\
        .connect_timeout(10)\
        .build()
    
    # Store database reference
    application.bot_data['db_connection'] = database
    application.bot_data['settings'] = settings
    
    # Register handlers
    logger.info("Registering handlers...")
    register_handlers(application)
    
    # Run the bot with polling (this blocks until stopped)
    logger.info("Starting bot with polling mode...")
    logger.info("Press Ctrl+C to stop the bot.")
    
    application.run_polling(drop_pending_updates=True)
    
    logger.info("Bot stopped.")

if __name__ == '__main__':
    main()
