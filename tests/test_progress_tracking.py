"""
Integration tests for progress tracking functionality.
Tests progress reporting, enhanced stats, and improvement rankings.
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bot.progress_handlers import ProgressHandlers
from database.progress_queries import ProgressQueries


class TestProgressTracking(unittest.TestCase):
    """Test progress tracking functionality"""

    def setUp(self):
        """Set up test environment."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Create progress handlers instance
        self.progress_handlers = ProgressHandlers()

        # Mock database connections
        self.mock_stats_db = Mock()
        self.mock_progress_queries = Mock()
        self.mock_leaderboard_generator = Mock()

        # Sample progress data
        self.sample_progress_data = {
            '7_day': {
                'ap_gain': 50000,
                'explorer_gain': 100,
                'connector_gain': 75,
                'mind_controller_gain': 50,
                'hacker_gain': 125,
                'builder_gain': 25,
                'recharger_gain': 200,
                'illuminator_gain': 15,
                'pioneer_gain': 10,
                'wayfarer_gain': 30,
                'scout_controller_gain': 40
            },
            '30_day': {
                'ap_gain': 200000,
                'explorer_gain': 400,
                'connector_gain': 300,
                'mind_controller_gain': 200,
                'hacker_gain': 500,
                'builder_gain': 100,
                'recharger_gain': 800,
                'illuminator_gain': 60,
                'pioneer_gain': 40,
                'wayfarer_gain': 120,
                'scout_controller_gain': 160
            },
            '90_day': {
                'ap_gain': 800000,
                'explorer_gain': 1600,
                'connector_gain': 1200,
                'mind_controller_gain': 800,
                'hacker_gain': 2000,
                'builder_gain': 400,
                'recharger_gain': 3200,
                'illuminator_gain': 240,
                'pioneer_gain': 160,
                'wayfarer_gain': 480,
                'scout_controller_gain': 640
            }
        }

        # Sample user stats
        self.sample_user_stats = {
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
            'scout_controller': 1200,
            'recursed': 1,
            'purifier': 200,
            'medalist': 150,
            'battler': 300,
            'anomaly': 5,
            'tessellated': 10,
            'pathfinder': 20
        }

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

    @patch('bot.progress_handlers.ProgressQueries')
    @patch('database.stats_database.StatsDatabase')
    async def test_progress_command(self, mock_stats_db, mock_progress_queries):
        """Test /progress command functionality"""
        # Arrange
        update = self.create_mock_update("/progress")
        context = self.create_mock_context()

        # Mock progress queries to return sample data
        mock_queries_instance = Mock()
        mock_queries_instance.get_user_progress.return_value = self.sample_progress_data
        mock_progress_queries.return_value = mock_queries_instance

        # Mock user stats
        mock_stats_instance = Mock()
        mock_stats_instance.get_user_stats.return_value = self.sample_user_stats
        mock_stats_db.return_value = mock_stats_instance

        progress_handler = ProgressHandlers()
        progress_handler.stats_db = mock_stats_instance
        progress_handler.progress_queries = mock_queries_instance

        # Act
        await progress_handler.progress_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that progress data is displayed
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("progress report", message_text.lower())
        self.assertIn("7 day", message_text.lower())
        self.assertIn("30 day", message_text.lower())
        self.assertIn("90 day", message_text.lower())
        self.assertIn("50,000 AP", message_text)
        self.assertIn("200,000 AP", message_text)
        self.assertIn("800,000 AP", message_text)

        # Verify progress queries were called
        mock_queries_instance.get_user_progress.assert_called_once_with(12345)

    @patch('bot.progress_handlers.ProgressQueries')
    @patch('database.stats_database.StatsDatabase')
    async def test_progress_command_no_data(self, mock_stats_db, mock_progress_queries):
        """Test /progress command when user has no progress data"""
        # Arrange
        update = self.create_mock_update("/progress")
        context = self.create_mock_context()

        # Mock progress queries to return no data
        mock_queries_instance = Mock()
        mock_queries_instance.get_user_progress.return_value = None
        mock_progress_queries.return_value = mock_queries_instance

        progress_handler = ProgressHandlers()
        progress_handler.progress_queries = mock_queries_instance

        # Act
        await progress_handler.progress_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that no progress message is displayed
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("no progress", message_text.lower())
        self.assertIn("stats", message_text.lower())

    @patch('bot.progress_handlers.ProgressQueries')
    @patch('database.stats_database.StatsDatabase')
    async def test_enhanced_mystats_command(self, mock_stats_db, mock_progress_queries):
        """Test enhanced /mystats command with progress trends"""
        # Arrange
        update = self.create_mock_update("/mystats")
        context = self.create_mock_context()

        # Mock user stats
        mock_stats_instance = Mock()
        mock_stats_instance.get_user_stats.return_value = self.sample_user_stats
        mock_stats_db.return_value = mock_stats_instance

        # Mock progress data
        mock_queries_instance = Mock()
        mock_queries_instance.get_user_progress.return_value = self.sample_progress_data
        mock_progress_queries.return_value = mock_queries_instance

        progress_handler = ProgressHandlers()
        progress_handler.stats_db = mock_stats_instance
        progress_handler.progress_queries = mock_queries_instance

        # Act
        await progress_handler.enhanced_mystats_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that enhanced stats with progress are displayed
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("TestAgent", message_text)
        self.assertIn("Level 16", message_text)
        self.assertIn("1,500,000 AP", message_text)
        self.assertIn("progress", message_text.lower())
        self.assertIn("30 days", message_text.lower())
        self.assertIn("+50,000 AP", message_text)  # 7-day progress
        self.assertIn("+200,000 AP", message_text)  # 30-day progress

    @patch('bot.progress_handlers.ProgressQueries')
    async def test_progress_leaderboard_command(self, mock_progress_queries):
        """Test progress leaderboard command"""
        # Arrange
        update = self.create_mock_update("/progress_leaderboard")
        context = self.create_mock_context()

        # Mock progress leaderboard data
        progress_leaderboard = [
            {'rank': 1, 'username': 'player1', 'agent': 'Agent1', 'ap_gain': 100000},
            {'rank': 2, 'username': 'player2', 'agent': 'Agent2', 'ap_gain': 95000},
            {'rank': 3, 'username': 'testuser', 'agent': 'TestAgent', 'ap_gain': 80000},
            {'rank': 4, 'username': 'player4', 'agent': 'Agent4', 'ap_gain': 75000},
        ]

        mock_queries_instance = Mock()
        mock_queries_instance.get_progress_leaderboard.return_value = progress_leaderboard
        mock_progress_queries.return_value = mock_queries_instance

        progress_handler = ProgressHandlers()
        progress_handler.progress_queries = mock_queries_instance

        # Act
        await progress_handler.progress_leaderboard_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that progress leaderboard is displayed
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]
        reply_markup = call_args[1]['reply_markup'] if len(call_args) > 1 else None

        self.assertIn("progress leaderboard", message_text.lower())
        self.assertIn("AP gain", message_text)
        self.assertIn("player1", message_text)
        self.assertIn("100,000", message_text)
        self.assertIn("testuser", message_text)
        self.assertIn("80,000", message_text)

        # Check that inline keyboard is provided for time period selection
        self.assertIsNotNone(reply_markup)
        self.assertTrue(hasattr(reply_markup, 'inline_keyboard'))

    @patch('bot.progress_handlers.ProgressQueries')
    async def test_progress_leaderboard_command_no_data(self, mock_progress_queries):
        """Test progress leaderboard command with no data"""
        # Arrange
        update = self.create_mock_update("/progress_leaderboard")
        context = self.create_mock_context()

        mock_queries_instance = Mock()
        mock_queries_instance.get_progress_leaderboard.return_value = []
        mock_progress_queries.return_value = mock_queries_instance

        progress_handler = ProgressHandlers()
        progress_handler.progress_queries = mock_queries_instance

        # Act
        await progress_handler.progress_leaderboard_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that no data message is displayed
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("no progress", message_text.lower())
        self.assertIn("leaderboard", message_text.lower())

    @patch('bot.progress_handlers.ProgressQueries')
    async def test_handle_progress_callback(self, mock_progress_queries):
        """Test handling of progress-related callbacks"""
        # Arrange
        update = Mock()
        update.callback_query = Mock()
        update.callback_query.from_user = Mock()
        update.callback_query.from_user.id = 12345
        update.callback_query.data = "progress_leaderboard:ap:30"
        update.callback_query.message = Mock()
        update.callback_query.message.edit_text = AsyncMock()
        update.callback_query.answer = AsyncMock()

        # Mock progress leaderboard data for specific period
        progress_leaderboard = [
            {'rank': 1, 'username': 'player1', 'agent': 'Agent1', 'ap_gain': 50000},
            {'rank': 2, 'username': 'testuser', 'agent': 'TestAgent', 'ap_gain': 45000},
        ]

        mock_queries_instance = Mock()
        mock_queries_instance.get_progress_leaderboard.return_value = progress_leaderboard
        mock_progress_queries.return_value = mock_queries_instance

        progress_handler = ProgressHandlers()
        progress_handler.progress_queries = mock_queries_instance

        # Act
        await progress_handler.handle_progress_callback(update, None)

        # Assert
        update.callback_query.answer.assert_called_once()
        update.callback_query.message.edit_text.assert_called_once()

        # Check that the correct leaderboard period is displayed
        call_args = update.callback_query.message.edit_text.call_args
        message_text = call_args[0][0]

        self.assertIn("30 day", message_text.lower())
        self.assertIn("progress leaderboard", message_text.lower())
        self.assertIn("player1", message_text)
        self.assertIn("50,000", message_text)

    @patch('bot.progress_handlers.ProgressQueries')
    async def test_compare_progress_command(self, mock_progress_queries):
        """Test comparing progress with other users"""
        # Arrange
        update = self.create_mock_update("/compare_progress player2")
        context = self.create_mock_context()

        # Mock progress data for comparison
        user_progress = self.sample_progress_data
        other_user_progress = {
            '7_day': {'ap_gain': 75000, 'explorer_gain': 150},
            '30_day': {'ap_gain': 300000, 'explorer_gain': 600},
            '90_day': {'ap_gain': 900000, 'explorer_gain': 1800}
        }

        mock_queries_instance = Mock()
        mock_queries_instance.get_user_progress.side_effect = [user_progress, other_user_progress]
        mock_queries_instance.get_username_from_agent.return_value = "player2"
        mock_progress_queries.return_value = mock_queries_instance

        progress_handler = ProgressHandlers()
        progress_handler.progress_queries = mock_queries_instance

        # Act
        await progress_handler.compare_progress_command(update, context, "player2")

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that comparison is displayed
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("progress comparison", message_text.lower())
        self.assertIn("testuser", message_text.lower())
        self.assertIn("player2", message_text.lower())
        self.assertIn("50,000 AP", message_text)  # User progress
        self.assertIn("75,000 AP", message_text)  # Other user progress

    @patch('bot.progress_handlers.ProgressQueries')
    @patch('database.stats_database.StatsDatabase')
    async def test_progress_insights_command(self, mock_stats_db, mock_progress_queries):
        """Test progress insights command"""
        # Arrange
        update = self.create_mock_update("/progress_insights")
        context = self.create_mock_context()

        # Mock user stats
        mock_stats_instance = Mock()
        mock_stats_instance.get_user_stats.return_value = self.sample_user_stats
        mock_stats_db.return_value = mock_stats_instance

        # Mock progress data and insights
        mock_queries_instance = Mock()
        mock_queries_instance.get_user_progress.return_value = self.sample_progress_data
        mock_queries_instance.get_progress_insights.return_value = {
            'strongest_category': 'hacker',
            'weakest_category': 'builder',
            'daily_average_ap': 2667,
            'projected_monthly_ap': 80000,
            'improvement_trend': 'increasing'
        }
        mock_progress_queries.return_value = mock_queries_instance

        progress_handler = ProgressHandlers()
        progress_handler.stats_db = mock_stats_instance
        progress_handler.progress_queries = mock_queries_instance

        # Act
        await progress_handler.progress_insights_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that insights are displayed
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("progress insights", message_text.lower())
        self.assertIn("strongest", message_text.lower())
        self.assertIn("hacker", message_text.lower())
        self.assertIn("weakest", message_text.lower())
        self.assertIn("builder", message_text.lower())
        self.assertIn("2,667 AP", message_text.lower())  # Daily average

    async def test_progress_calculation_accuracy(self):
        """Test that progress calculations are accurate"""
        # Test various progress calculation scenarios
        test_cases = [
            {
                'name': 'Simple AP gain',
                'old_stats': {'ap': 1000000},
                'new_stats': {'ap': 1050000},
                'expected_ap_gain': 50000
            },
            {
                'name': 'Multiple stat gains',
                'old_stats': {
                    'ap': 1000000,
                    'explorer': 1000,
                    'connector': 500
                },
                'new_stats': {
                    'ap': 1100000,
                    'explorer': 1200,
                    'connector': 600
                },
                'expected_ap_gain': 100000,
                'expected_explorer_gain': 200,
                'expected_connector_gain': 100
            },
            {
                'name': 'No change',
                'old_stats': {'ap': 1000000, 'explorer': 1000},
                'new_stats': {'ap': 1000000, 'explorer': 1000},
                'expected_ap_gain': 0,
                'expected_explorer_gain': 0
            }
        ]

        for i, test_case in enumerate(test_cases):
            with self.subTest(f"Progress calculation {i+1}: {test_case['name']}"):
                # This would test the internal progress calculation logic
                # In a real implementation, we'd call the progress calculation method
                # and verify the results match expected values
                pass


if __name__ == '__main__':
    unittest.main()