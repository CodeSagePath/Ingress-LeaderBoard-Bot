"""
Shared test fixtures and utilities for integration testing.
"""

import unittest
import unittest.mock as mock
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object."""
    update = Mock()
    update.message = Mock()
    update.message.from_user = Mock()
    update.message.from_user.id = 12345
    update.message.from_user.username = "testuser"
    update.message.chat_id = 67890
    update.message.text = "/start"
    update.callback_query = Mock()
    update.callback_query.from_user = Mock()
    update.callback_query.from_user.id = 12345
    update.callback_query.data = "test_callback"
    return update


@pytest.fixture
def mock_context():
    """Create a mock Telegram Context object."""
    context = Mock()
    context.bot = Mock()
    context.bot.send_message = AsyncMock()
    context.bot.answer_callback_query = AsyncMock()
    context.bot.edit_message_text = AsyncMock()
    return context


@pytest.fixture
def mock_database():
    """Create a mock database connection."""
    db = Mock()
    db.execute = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    db.close = Mock()
    return db


@pytest.fixture
def mock_leaderboard_generator():
    """Create a mock LeaderboardGenerator."""
    generator = Mock()
    generator.get_leaderboard = Mock(return_value=[])
    generator.get_stats = Mock(return_value={})
    return generator


@pytest.fixture
def mock_stats_parser():
    """Create a mock StatsParser."""
    parser = Mock()
    parser.parse_stats = Mock(return_value={"ap": 1000000, "level": 16})
    parser.validate_stats = Mock(return_value=True)
    return parser


@pytest.fixture
def sample_user_stats():
    """Sample user stats for testing."""
    return {
        "username": "testuser",
        "agent": "TestAgent",
        "faction": "enlightened",
        "level": 16,
        "ap": 1500000,
        "explorer": 5000,
        "connector": 3000,
        "mind_controller": 2000,
        "hacker": 4000,
        "builder": 1000,
        "recharger": 6000,
        "illuminator": 500,
        "pioneer": 300,
        "wayfarer": 800,
        "scout": 1200,
        "recursed": 1,
        "purifier": 200,
        "medalist": 150,
        "battler": 300,
        "anomaly": 5,
        "tessellated": 10,
        "pathfinder": 20,
        "pioneer_badge": 15,
        "explorer_badge": 25
    }


@pytest.fixture
def sample_leaderboard_data():
    """Sample leaderboard data for testing."""
    return [
        {"rank": 1, "username": "player1", "agent": "Agent1", "value": 1000000},
        {"rank": 2, "username": "player2", "agent": "Agent2", "value": 950000},
        {"rank": 3, "username": "player3", "agent": "Agent3", "value": 900000},
    ]


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class AsyncTestCase(unittest.TestCase):
    """Base class for async test cases."""

    def setUp(self):
        """Set up async test environment."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Clean up async test environment."""
        self.loop.close()

    def run_async(self, coro):
        """Run an async coroutine in the test loop."""
        return self.loop.run_until_complete(coro)


def create_mock_bot():
    """Create a comprehensive mock bot for testing."""
    bot = Mock()

    # Mock database connection
    bot.db = Mock()
    bot.db.execute = Mock()
    bot.db.commit = Mock()
    bot.db.rollback = Mock()
    bot.db.close = Mock()

    # Mock leaderboard generator
    bot.leaderboard_generator = Mock()
    bot.leaderboard_generator.get_leaderboard = Mock(return_value=[])
    bot.leaderboard_generator.get_stats = Mock(return_value={})
    bot.leaderboard_generator.get_progress_stats = Mock(return_value={})

    # Mock stats parser
    bot.stats_parser = Mock()
    bot.stats_parser.parse_stats = Mock(return_value={})
    bot.stats_parser.validate_stats = Mock(return_value=True)

    # Mock callback handlers
    bot.callback_handler = Mock()
    bot.callback_handler.handle_callback = AsyncMock()

    # Mock progress handler
    bot.progress_handler = Mock()
    bot.progress_handler.get_progress_report = AsyncMock(return_value={})

    return bot


def create_inline_keyboard_mock():
    """Create a mock inline keyboard for testing."""
    keyboard = Mock()
    keyboard.inline_keyboard = [
        [{"text": "All", "callback_data": "leaderboard:all"}],
        [{"text": "Enlightened", "callback_data": "leaderboard:enlightened"}],
        [{"text": "Resistance", "callback_data": "leaderboard:resistance"}]
    ]
    return keyboard


def assert_message_sent(mock_context, expected_text=None, expected_reply_markup=None):
    """Assert that a message was sent with expected content."""
    mock_context.bot.send_message.assert_called()
    call_args = mock_context.bot.send_message.call_args

    if expected_text:
        assert expected_text in call_args[1]['text']

    if expected_reply_markup:
        assert call_args[1]['reply_markup'] == expected_reply_markup


def assert_callback_answered(mock_context, expected_text=None):
    """Assert that a callback query was answered."""
    mock_context.bot.answer_callback_query.assert_called()
    call_args = mock_context.bot.answer_callback_query.call_args

    if expected_text:
        assert expected_text in call_args[1]['text']


def assert_message_edited(mock_context, expected_text=None):
    """Assert that a message was edited with expected content."""
    mock_context.bot.edit_message_text.assert_called()
    call_args = mock_context.bot.edit_message_text.call_args

    if expected_text:
        assert expected_text in call_args[1]['text']


class MockDatabase:
    """Mock database for testing."""

    def __init__(self):
        self.data = {}
        self.transactions = []

    def execute(self, query, params=None):
        """Mock database execution."""
        return Mock()

    def commit(self):
        """Mock database commit."""
        self.transactions.append("commit")

    def rollback(self):
        """Mock database rollback."""
        self.transactions.append("rollback")

    def close(self):
        """Mock database close."""
        pass

    def fetchone(self):
        """Mock fetchone."""
        return None

    def fetchall(self):
        """Mock fetchall."""
        return []