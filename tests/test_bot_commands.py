"""
Integration tests for bot commands as specified in the roadmap.
Tests basic bot functionality: /start, /help, /mystats, /leaderboard commands.
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.bot.handlers import BotHandlers
from src.bot.progress_handlers import ProgressHandlers


class TestBotCommands(unittest.TestCase):
    """Test bot commands as specified in Task 8.2.1"""

    def setUp(self):
        """Set up test environment."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Create bot handlers instance
        self.bot = BotHandlers()

        # Mock database connections
        self.mock_db = Mock()
        self.mock_db.execute = Mock(return_value=Mock())
        self.mock_db.commit = Mock()
        self.mock_db.fetchone = Mock(return_value=None)
        self.mock_db.fetchall = Mock(return_value=[])

        # Patch the database connection
        self.db_patcher = patch('bot.handlers.Database')
        self.mock_database_class = self.db_patcher.start()
        self.mock_database_class.return_value = self.mock_db

        # Mock leaderboard generator
        self.mock_leaderboard_generator = Mock()
        self.mock_leaderboard_generator.get_categories = Mock(return_value=[
            'ap', 'explorer', 'connector', 'mind_controller', 'hacker'
        ])
        self.mock_leaderboard_generator.get_leaderboard = Mock(return_value=[])

        # Mock progress handlers
        self.mock_progress_handlers = Mock()
        self.mock_progress_handlers.get_user_stats = Mock(return_value={})

    def tearDown(self):
        """Clean up test environment."""
        self.loop.close()
        self.db_patcher.stop()

    def run_async(self, coro):
        """Run async coroutine in test loop."""
        return self.loop.run_until_complete(coro)

    def create_mock_update(self, message_text="/start"):
        """Create a mock Telegram update object."""
        update = Mock()
        update.message = Mock()
        update.message.from_user = Mock()
        update.message.from_user.id = 12345
        update.message.from_user.username = "testuser"
        update.message.from_user.first_name = "Test"
        update.message.chat_id = 67890
        update.message.text = message_text
        update.message.reply_text = AsyncMock()
        return update

    def create_mock_context(self):
        """Create a mock Telegram context object."""
        context = Mock()
        context.bot = Mock()
        context.bot.send_message = AsyncMock()
        return context

    @patch('bot.handlers.BotHandlers')
    async def test_start_command(self, mock_bot_handler):
        """Test /start command functionality"""
        # Arrange
        update = self.create_mock_update("/start")
        context = self.create_mock_context()

        bot_instance = BotHandlers()

        # Act
        await bot_instance.start_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that the welcome message contains expected elements
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("Welcome", message_text)
        self.assertIn("Ingress", message_text)
        self.assertIn("Leaderboard", message_text)
        self.assertIn("/help", message_text)

    @patch('bot.handlers.BotHandlers')
    async def test_help_command(self, mock_bot_handler):
        """Test /help command functionality"""
        # Arrange
        update = self.create_mock_update("/help")
        context = self.create_mock_context()

        bot_instance = BotHandlers()

        # Act
        await bot_instance.help_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that help message contains expected commands
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        expected_commands = ['/start', '/help', '/mystats', '/leaderboard', '/progress']
        for command in expected_commands:
            self.assertIn(command, message_text)

    @patch('bot.handlers.BotHandlers')
    @patch('database.stats_database.StatsDatabase')
    async def test_mystats_command_with_stats(self, mock_stats_db, mock_bot_handler):
        """Test /mystats command when user has stats"""
        # Arrange
        update = self.create_mock_update("/mystats")
        context = self.create_mock_context()

        # Mock user stats data
        mock_user_stats = Mock()
        mock_user_stats.__dict__ = {
            'username': 'testuser',
            'agent': 'TestAgent',
            'faction': 'enlightened',
            'level': 16,
            'ap': 1500000,
            'explorer': 5000,
            'connector': 3000,
            'mind_controller': 2000,
            'hacker': 4000,
            'builder': 1000,
            'recharger': 6000,
            'illuminator': 500,
            'pioneer': 300,
            'wayfarer': 800,
            'scout': 1200
        }

        # Mock database to return user stats
        mock_db_instance = Mock()
        mock_db_instance.get_user_stats = Mock(return_value=mock_user_stats)
        mock_stats_db.return_value = mock_db_instance

        bot_instance = BotHandlers()
        bot_instance.stats_db = mock_db_instance

        # Act
        await bot_instance.mystats_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that stats are displayed correctly
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("testuser", message_text)
        self.assertIn("TestAgent", message_text)
        self.assertIn("Level 16", message_text)
        self.assertIn("1,500,000", message_text)  # AP formatted

    @patch('bot.handlers.BotHandlers')
    @patch('database.stats_database.StatsDatabase')
    async def test_mystats_command_no_stats(self, mock_stats_db, mock_bot_handler):
        """Test /mystats command when user has no stats"""
        # Arrange
        update = self.create_mock_update("/mystats")
        context = self.create_mock_context()

        # Mock database to return no stats
        mock_db_instance = Mock()
        mock_db_instance.get_user_stats = Mock(return_value=None)
        mock_stats_db.return_value = mock_db_instance

        bot_instance = BotHandlers()
        bot_instance.stats_db = mock_db_instance

        # Act
        await bot_instance.mystats_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that no stats message is displayed
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("no stats", message_text.lower())
        self.assertIn("submit", message_text.lower())

    @patch('bot.handlers.BotHandlers')
    @patch('leaderboard.generator.LeaderboardGenerator')
    async def test_leaderboard_command(self, mock_leaderboard_gen, mock_bot_handler):
        """Test /leaderboard command functionality"""
        # Arrange
        update = self.create_mock_update("/leaderboard")
        context = self.create_mock_context()

        # Mock leaderboard generator
        mock_generator_instance = Mock()
        mock_generator_instance.get_categories = Mock(return_value=[
            'ap', 'explorer', 'connector', 'mind_controller', 'hacker',
            'builder', 'recharger', 'illuminator', 'pioneer', 'wayfarer', 'scout'
        ])
        mock_leaderboard_gen.return_value = mock_generator_instance

        bot_instance = BotHandlers()
        bot_instance.leaderboard_generator = mock_generator_instance

        # Act
        await bot_instance.leaderboard_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that leaderboard categories are shown
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]
        reply_markup = call_args[1]['reply_markup'] if len(call_args) > 1 else None

        self.assertIn("leaderboard", message_text.lower())
        self.assertIn("category", message_text.lower())

        # Check that inline keyboard is provided
        self.assertIsNotNone(reply_markup)
        self.assertTrue(hasattr(reply_markup, 'inline_keyboard'))

    @patch('bot.handlers.BotHandlers')
    @patch('leaderboard.generator.LeaderboardGenerator')
    async def test_faction_leaderboard_command(self, mock_leaderboard_gen, mock_bot_handler):
        """Test faction-specific leaderboard command"""
        # Arrange
        update = self.create_mock_update("/leaderboard enlightened")
        context = self.create_mock_context()

        # Mock leaderboard data
        mock_leaderboard_data = [
            {'rank': 1, 'username': 'player1', 'agent': 'Agent1', 'value': 1000000, 'faction': 'enlightened'},
            {'rank': 2, 'username': 'player2', 'agent': 'Agent2', 'value': 950000, 'faction': 'enlightened'},
            {'rank': 3, 'username': 'player3', 'agent': 'Agent3', 'value': 900000, 'faction': 'enlightened'}
        ]

        mock_generator_instance = Mock()
        mock_generator_instance.get_leaderboard = Mock(return_value=mock_leaderboard_data)
        mock_leaderboard_gen.return_value = mock_generator_instance

        bot_instance = BotHandlers()
        bot_instance.leaderboard_generator = mock_generator_instance

        # Act
        await bot_instance.faction_leaderboard_command(update, context, 'ap', 'enlightened')

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that leaderboard is displayed
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("leaderboard", message_text.lower())
        self.assertIn("enlightened", message_text.lower())
        self.assertIn("player1", message_text)
        self.assertIn("1,000,000", message_text)  # Formatted AP

    async def test_stats_submission_invalid_format(self):
        """Test stats submission with invalid format"""
        # Arrange
        update = self.create_mock_update("This is not a valid stats format")
        context = self.create_mock_context()

        # Act
        await self.bot.handle_message(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that error message is displayed
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("invalid", message_text.lower())
        self.assertIn("format", message_text.lower())

    async def test_unknown_command(self):
        """Test handling of unknown commands"""
        # Arrange
        update = self.create_mock_update("/unknowncommand")
        context = self.create_mock_context()

        # Act
        await self.bot.handle_message(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that help is suggested
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("don't understand", message_text.lower())
        self.assertIn("/help", message_text)


class TestProgressCommands(unittest.TestCase):
    """Test progress tracking commands"""

    def setUp(self):
        """Set up test environment."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Mock dependencies
        self.mock_stats_db = Mock()
        self.mock_leaderboard_generator = Mock()

    def tearDown(self):
        """Clean up test environment."""
        self.loop.close()

    def run_async(self, coro):
        """Run async coroutine in test loop."""
        return self.loop.run_until_complete(coro)

    def create_mock_update(self, message_text="/progress"):
        """Create a mock Telegram update object."""
        update = Mock()
        update.message = Mock()
        update.message.from_user = Mock()
        update.message.from_user.id = 12345
        update.message.from_user.username = "testuser"
        update.message.chat_id = 67890
        update.message.text = message_text
        update.message.reply_text = AsyncMock()
        return update

    def create_mock_context(self):
        """Create a mock Telegram context object."""
        context = Mock()
        context.bot = Mock()
        context.bot.send_message = AsyncMock()
        return context

    @patch('bot.progress_handlers.ProgressHandlers')
    async def test_progress_command(self, mock_progress_handlers):
        """Test /progress command functionality"""
        # Arrange
        update = self.create_mock_update("/progress")
        context = self.create_mock_context()

        # Mock progress data
        mock_progress_data = {
            '7_day': {'ap_change': 50000, 'rank_change': 2},
            '30_day': {'ap_change': 200000, 'rank_change': 5},
            '90_day': {'ap_change': 800000, 'rank_change': 15}
        }

        mock_progress_instance = Mock()
        mock_progress_instance.get_progress_report = Mock(return_value=mock_progress_data)
        mock_progress_handlers.return_value = mock_progress_instance

        progress_handler = ProgressHandlers()
        progress_handler.stats_db = self.mock_stats_db
        progress_handler.leaderboard_generator = self.mock_leaderboard_generator

        # Act
        await progress_handler.progress_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that progress data is displayed
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("progress", message_text.lower())
        self.assertIn("7 day", message_text.lower())
        self.assertIn("30 day", message_text.lower())
        self.assertIn("90 day", message_text.lower())


if __name__ == '__main__':
    unittest.main()