"""
Integration tests for stats submission workflow.
Tests complete stats parsing, validation, and database storage process.
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bot.handlers import BotHandlers
from parsers.stats_parser import StatsParser
from validation.business_rules_validator import BusinessRulesValidator
from database.stats_database import StatsDatabase


class TestStatsWorkflow(unittest.TestCase):
    """Test stats submission workflow as specified in Task 8.2.1"""

    def setUp(self):
        """Set up test environment."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Create bot handlers instance
        self.bot = BotHandlers()

        # Sample valid stats text
        self.valid_stats_text = """
Time Span: All Time
Agent: TestPlayer
Faction: Enlightened ☯
Level: 16

AP: 1,543,210 (3,210)
Explorer: 5,234 (234)
Connector: 3,456 (156)
Mind Controller: 2,789 (89)
Hacker: 4,123 (212)
Builder: 1,234 (45)
Recharger: 6,789 (123)
Illuminator: 567 (12)
Pioneer: 345 (23)
Wayfarer: 890 (34)
Scout Controller: 1,234 (56)
Recursed: 1 (0)
Purifier: 234 (12)
Medalist: 156 (8)
Battler: 345 (19)
Anomaly: 6 (1)
Tessellated: 12 (2)
Pathfinder: 25 (3)
SpecOps: 18 (2)
Mission Day: 4 (1)
NL-1331: 8 (1)
First Saturday: 3 (0)
        """

        # Sample invalid stats text
        self.invalid_stats_text = """
This is not a valid stats submission
Just some random text that doesn't match the format
        """

    def tearDown(self):
        """Clean up test environment."""
        self.loop.close()

    def run_async(self, coro):
        """Run async coroutine in test loop."""
        return self.loop.run_until_complete(coro)

    def create_mock_update(self, message_text):
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

    @patch('bot.handlers.StatsParser')
    @patch('bot.handlers.Database')
    @patch('bot.handlers.BusinessRulesValidator')
    async def test_stats_submission_valid(self, mock_validator, mock_db, mock_parser):
        """Test successful stats submission flow"""
        # Arrange
        update = self.create_mock_update(self.valid_stats_text)
        context = self.create_mock_context()

        # Mock parser to return valid parsed stats
        mock_parser_instance = Mock()
        parsed_stats = {
            'agent': 'TestPlayer',
            'faction': 'enlightened',
            'level': 16,
            'ap': 1543210,
            'explorer': 5234,
            'connector': 3456,
            'mind_controller': 2789,
            'hacker': 4123,
            'builder': 1234,
            'recharger': 6789,
            'illuminator': 567,
            'pioneer': 345,
            'wayfarer': 890,
            'scout_controller': 1234,
            'recursed': 1,
            'purifier': 234,
            'medalist': 156,
            'battler': 345,
            'anomaly': 6,
            'tessellated': 12,
            'pathfinder': 25,
            'spec_ops': 18,
            'mission_day': 4,
            'nl1331': 8,
            'first_saturday': 3
        }
        mock_parser_instance.parse_stats.return_value = parsed_stats
        mock_parser_instance.validate_stats.return_value = True
        mock_parser.return_value = mock_parser_instance

        # Mock validator to pass
        mock_validator_instance = Mock()
        mock_validator_instance.validate_stats.return_value = []
        mock_validator.return_value = mock_validator_instance

        # Mock database operations
        mock_db_instance = Mock()
        mock_db_instance.save_stats = Mock(return_value=True)
        mock_db_instance.get_latest_stats = Mock(return_value=None)  # No previous stats
        mock_db.return_value = mock_db_instance

        # Mock stats database
        mock_stats_db = Mock()
        mock_stats_db.save_stats = AsyncMock(return_value=True)
        mock_stats_db.get_latest_stats = Mock(return_value=None)

        bot_instance = BotHandlers()
        bot_instance.stats_db = mock_stats_db
        bot_instance.stats_parser = mock_parser_instance
        bot_instance.validator = mock_validator_instance

        # Act
        await bot_instance.handle_message(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that success message was sent
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("successfully", message_text.lower())
        self.assertIn("saved", message_text.lower())
        self.assertIn("TestPlayer", message_text)

        # Verify parser was called
        mock_parser_instance.parse_stats.assert_called_once_with(self.valid_stats_text)
        mock_parser_instance.validate_stats.assert_called_once()

        # Verify validator was called
        mock_validator_instance.validate_stats.assert_called_once_with(parsed_stats)

    @patch('bot.handlers.StatsParser')
    @patch('bot.handlers.Database')
    @patch('bot.handlers.BusinessRulesValidator')
    async def test_stats_submission_invalid_format(self, mock_validator, mock_db, mock_parser):
        """Test stats submission with invalid format"""
        # Arrange
        update = self.create_mock_update(self.invalid_stats_text)
        context = self.create_mock_context()

        # Mock parser to return None (invalid format)
        mock_parser_instance = Mock()
        mock_parser_instance.parse_stats.return_value = None
        mock_parser.return_value = mock_parser_instance

        bot_instance = BotHandlers()
        bot_instance.stats_parser = mock_parser_instance

        # Act
        await bot_instance.handle_message(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that error message was sent
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("invalid", message_text.lower())
        self.assertIn("format", message_text.lower())

        # Verify parser was called but validation was not
        mock_parser_instance.parse_stats.assert_called_once_with(self.invalid_stats_text)
        mock_parser_instance.validate_stats.assert_not_called()

    @patch('bot.handlers.StatsParser')
    @patch('bot.handlers.Database')
    @patch('bot.handlers.BusinessRulesValidator')
    async def test_stats_submission_business_rules_violation(self, mock_validator, mock_db, mock_parser):
        """Test stats submission with business rules violations"""
        # Arrange
        update = self.create_mock_update(self.valid_stats_text)
        context = self.create_mock_context()

        # Mock parser to return valid parsed stats
        mock_parser_instance = Mock()
        parsed_stats = {
            'agent': 'TestPlayer',
            'faction': 'enlightened',
            'level': 16,
            'ap': 1543210,
            'explorer': 5234,
            'connector': 3456,
            'mind_controller': 2789,
            'hacker': 4123,
            'builder': 1234,
            'recharger': 6789,
            'illuminator': 567,
            'pioneer': 345,
            'wayfarer': 890,
            'scout_controller': 1234,
            'recursed': 1,
            'purifier': 234,
            'medalist': 156,
            'battler': 345,
            'anomaly': 6,
            'tessellated': 12,
            'pathfinder': 25
        }
        mock_parser_instance.parse_stats.return_value = parsed_stats
        mock_parser_instance.validate_stats.return_value = True
        mock_parser.return_value = mock_parser_instance

        # Mock validator to fail with business rules violations
        mock_validator_instance = Mock()
        violations = [
            "AP decrease detected: Previous AP was higher",
            "Invalid stat progression: Explorer badges inconsistent with level"
        ]
        mock_validator_instance.validate_stats.return_value = violations
        mock_validator.return_value = mock_validator_instance

        bot_instance = BotHandlers()
        bot_instance.stats_parser = mock_parser_instance
        bot_instance.validator = mock_validator_instance

        # Act
        await bot_instance.handle_message(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that validation error message was sent
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("validation", message_text.lower())
        self.assertIn("failed", message_text.lower())
        self.assertIn("AP decrease", message_text)
        self.assertIn("Explorer badges", message_text)

        # Verify parser was called
        mock_parser_instance.parse_stats.assert_called_once()
        mock_parser_instance.validate_stats.assert_called_once()

        # Verify validator was called
        mock_validator_instance.validate_stats.assert_called_once_with(parsed_stats)

    @patch('bot.handlers.StatsParser')
    @patch('bot.handlers.Database')
    @patch('bot.handlers.BusinessRulesValidator')
    async def test_stats_submission_database_error(self, mock_validator, mock_db, mock_parser):
        """Test stats submission with database error"""
        # Arrange
        update = self.create_mock_update(self.valid_stats_text)
        context = self.create_mock_context()

        # Mock parser to return valid parsed stats
        mock_parser_instance = Mock()
        parsed_stats = {
            'agent': 'TestPlayer',
            'faction': 'enlightened',
            'level': 16,
            'ap': 1543210,
            'explorer': 5234,
            'connector': 3456,
            'mind_controller': 2789,
            'hacker': 4123,
            'builder': 1234,
            'recharger': 6789,
            'illuminator': 567,
            'pioneer': 345,
            'wayfarer': 890,
            'scout_controller': 1234,
            'recursed': 1,
            'purifier': 234,
            'medalist': 156,
            'battler': 345,
            'anomaly': 6,
            'tessellated': 12,
            'pathfinder': 25
        }
        mock_parser_instance.parse_stats.return_value = parsed_stats
        mock_parser_instance.validate_stats.return_value = True
        mock_parser.return_value = mock_parser_instance

        # Mock validator to pass
        mock_validator_instance = Mock()
        mock_validator_instance.validate_stats.return_value = []
        mock_validator.return_value = mock_validator_instance

        # Mock database to raise an exception
        mock_stats_db = Mock()
        mock_stats_db.save_stats = AsyncMock(side_effect=Exception("Database connection failed"))

        bot_instance = BotHandlers()
        bot_instance.stats_parser = mock_parser_instance
        bot_instance.validator = mock_validator_instance
        bot_instance.stats_db = mock_stats_db

        # Act
        await bot_instance.handle_message(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that database error message was sent
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("error", message_text.lower())
        self.assertIn("database", message_text.lower())
        self.assertIn("try again", message_text.lower())

    @patch('bot.handlers.StatsParser')
    @patch('bot.handlers.Database')
    @patch('bot.handlers.BusinessRulesValidator')
    async def test_stats_submission_progress_tracking(self, mock_validator, mock_db, mock_parser):
        """Test stats submission with progress tracking integration"""
        # Arrange
        update = self.create_mock_update(self.valid_stats_text)
        context = self.create_mock_context()

        # Mock parser to return valid parsed stats
        mock_parser_instance = Mock()
        parsed_stats = {
            'agent': 'TestPlayer',
            'faction': 'enlightened',
            'level': 16,
            'ap': 1543210,
            'explorer': 5234,
            'connector': 3456,
            'mind_controller': 2789,
            'hacker': 4123,
            'builder': 1234,
            'recharger': 6789,
            'illuminator': 567,
            'pioneer': 345,
            'wayfarer': 890,
            'scout_controller': 1234,
            'recursed': 1,
            'purifier': 234,
            'medalist': 156,
            'battler': 345,
            'anomaly': 6,
            'tessellated': 12,
            'pathfinder': 25
        }
        mock_parser_instance.parse_stats.return_value = parsed_stats
        mock_parser_instance.validate_stats.return_value = True
        mock_parser.return_value = mock_parser_instance

        # Mock validator to pass
        mock_validator_instance = Mock()
        mock_validator_instance.validate_stats.return_value = []
        mock_validator.return_value = mock_validator_instance

        # Mock previous stats for progress calculation
        previous_stats = {
            'ap': 1500000,
            'explorer': 5000,
            'connector': 3300,
            'mind_controller': 2700,
            'hacker': 4000,
            'builder': 1200,
            'recharger': 6700,
            'illuminator': 550,
            'pioneer': 320,
            'wayfarer': 860,
            'scout_controller': 1200,
            'recursed': 1,
            'purifier': 220,
            'medalist': 150,
            'battler': 330,
            'anomaly': 5,
            'tessellated': 10,
            'pathfinder': 22
        }

        # Mock database operations
        mock_stats_db = Mock()
        mock_stats_db.save_stats = AsyncMock(return_value=True)
        mock_stats_db.get_latest_stats = Mock(return_value=previous_stats)
        mock_stats_db.save_progress = AsyncMock(return_value=True)

        bot_instance = BotHandlers()
        bot_instance.stats_parser = mock_parser_instance
        bot_instance.validator = mock_validator_instance
        bot_instance.stats_db = mock_stats_db

        # Act
        await bot_instance.handle_message(update, context)

        # Assert
        update.message.reply_text.assert_called_once()

        # Check that success message was sent
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]

        self.assertIn("successfully", message_text.lower())
        self.assertIn("saved", message_text.lower())

        # Verify progress tracking was triggered
        mock_stats_db.get_latest_stats.assert_called_once()
        mock_stats_db.save_progress.assert_called_once()

        # Verify the progress calculation was based on previous stats
        progress_call_args = mock_stats_db.save_progress.call_args
        progress_data = progress_call_args[0][1]  # Second argument is progress data

        # Should contain calculated progress differences
        self.assertIn('ap_gain', progress_data)
        self.assertIn('explorer_gain', progress_data)
        self.assertEqual(progress_data['ap_gain'], 43210)  # 1543210 - 1500000

    async def test_stats_parsing_edge_cases(self):
        """Test stats parsing with various edge cases"""
        # Test cases with different formatting
        test_cases = [
            # Missing time span
            """
Agent: TestPlayer
Faction: Enlightened ☯
Level: 16
AP: 1,543,210
            """,
            # Different faction format
            """
Time Span: All Time
Agent: TestPlayer
Faction: Resistance ⚡
Level: 15
AP: 1,234,567
            """,
            # With trailing spaces
            """
Time Span: All Time
Agent: TestPlayer
Faction: Enlightened ☯
Level: 16
AP: 1,543,210
            """,
            # Different time span
            """
Time Span: Last 30 Days
Agent: TestPlayer
Faction: Enlightened ☯
Level: 16
AP: 234,567
            """
        ]

        for i, test_case in enumerate(test_cases):
            with self.subTest(f"Edge case {i+1}"):
                # Arrange
                update = self.create_mock_update(test_case)
                context = self.create_mock_context()

                with patch('bot.handlers.StatsParser') as mock_parser:
                    mock_parser_instance = Mock()
                    mock_parser_instance.parse_stats.return_value = None
                    mock_parser.return_value = mock_parser_instance

                    bot_instance = BotHandlers()
                    bot_instance.stats_parser = mock_parser_instance

                    # Act
                    await bot_instance.handle_message(update, context)

                    # Assert - parser should be called with the exact text
                    mock_parser_instance.parse_stats.assert_called_once_with(test_case)


if __name__ == '__main__':
    unittest.main()