"""
Simplified Telegram Bot Framework for Ingress Prime Leaderboard

This module provides a clean, simplified interface for the Telegram bot
while maintaining all the robust backend functionality of the existing system.
"""

import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class IngressLeaderboardBot:
    """
    Simplified Telegram Bot Framework for Ingress Prime Leaderboard

    Provides a clean, easy-to-use interface that matches the user's requested
    framework structure while leveraging all existing production-ready functionality.
    """

    def __init__(self):
        """Initialize the simplified bot framework."""
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        # Initialize the Telegram application
        self.app = Application.builder().token(self.token).build()

        # Backend infrastructure (initialized later)
        self._db_connection = None
        self._settings = None
        self._initialized = False

        # Setup handlers using the simplified structure
        self.setup_handlers()

    def setup_handlers(self):
        """Register all command and message handlers using existing handlers."""
        # Import here to avoid circular imports
        try:
            from .handlers import register_simple_handlers
            register_simple_handlers(self.app)
        except ImportError as e:
            logger.warning(f"Could not import handlers: {e}")
            print("Please ensure the handlers module is properly set up")

    async def _initialize_backend(self):
        """Initialize the robust backend infrastructure."""
        if not self._initialized:
            try:
                # Import database connection and settings
                from ..database.connection import initialize_database
                from ..config.settings import get_settings

                # Load settings
                self._settings = get_settings()

                # Initialize database connection
                logger.info("Initializing database connection...")
                self._db_connection = initialize_database(
                    database_url=self._settings.database.url,
                    create_tables=True
                )

                # Test database connection
                if not self._db_connection.test_connection():
                    logger.warning("Database connection test failed, but continuing...")

                # Share backend data with simple framework
                self.app.bot_data.update({
                    'db_connection': self._db_connection,
                    'settings': self._settings
                })

                self._initialized = True
                print("✅ Backend infrastructure initialized successfully")
                logger.info("Backend infrastructure initialized successfully")

            except Exception as e:
                logger.error(f"Backend initialization failed: {e}")
                print(f"⚠️ Backend initialization failed: {e}")
                print("Bot will run with limited functionality")
                # Continue without backend - basic handlers will still work

    async def run(self):
        """Start the bot with full backend support."""
        print("🚀 Starting Ingress Prime Leaderboard Bot (Simple Framework)")
        print(f"📱 Bot token configured: {'✅' if self.token else '❌'}")

        # Initialize backend infrastructure
        await self._initialize_backend()

        # Start the bot
        print("🔄 Starting polling...")
        try:
            await self.app.run_polling()
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        except Exception as e:
            print(f"❌ Bot error: {e}")
            raise


async def submit_command(update: Update, context):
    """Handle /submit command - provide stats submission help."""
    from telegram.constants import ParseMode

    submit_text = """
📊 <b>Stats Submission Help</b>

To submit your Ingress Prime stats:

1. Open Ingress Prime on your device
2. Go to your Agent Profile
3. Tap on "ALL TIME" stats
4. Copy the entire stats text (starts with "Time Span")
5. Paste it directly in this chat

<b>Requirements:</b>
• Only ALL TIME stats are accepted
• Text must start with "Time Span"
• Include all stats lines
• Agent name must match exactly

<b>Pro Tips:</b>
• Submit regularly for accurate leaderboards
• Check your progress with /mystats
• View leaderboards with /leaderboard

Ready? Just paste your stats here!
    """

    await update.message.reply_text(
        submit_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )