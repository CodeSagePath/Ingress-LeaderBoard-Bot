#!/usr/bin/env python3
"""
Interactive Test Script for Ingress Prime Leaderboard Bot

Tests bot functionality locally without connecting to Telegram.
"""

import os
import sys
import asyncio
from datetime import datetime

# Setup environment
os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_for_development'
os.environ['DATABASE_URL'] = 'sqlite:///test_bot.db'
os.environ['LOG_LEVEL'] = 'DEBUG'
os.environ['LOG_FILE'] = 'test_results.log'

from src.config.settings import get_settings
from src.database.connection import initialize_database
from src.parsers.stats_parser import StatsParser
from src.parsers.validator import StatsValidator
from src.bot.handlers import BotHandlers
from src.database.models import get_agent_by_telegram_id, get_latest_submission_for_agent
from src.utils.logger import setup_logger


# Mock classes for Telegram Update/Context
class MockUser:
    def __init__(self, user_id=12345):
        self.id = user_id
        self.username = "test_user"
        self.first_name = "Test"
        self.last_name = "User"


class MockChat:
    def __init__(self):
        self.id = 12345
        self.type = "private"


class MockMessage:
    def __init__(self, text=""):
        self.text = text
        self.chat = MockChat()

    async def reply_text(self, text, **kwargs):
        print(f"\n[Bot Response]:")
        print("-" * 50)
        print(text)
        print("-" * 50)


class MockUpdate:
    def __init__(self, text=""):
        self.effective_user = MockUser()
        self.effective_chat = MockChat()
        self.message = MockMessage(text)


class MockContext:
    def __init__(self, db_connection):
        self.bot_data = {'db_connection': db_connection}


# Test functions
async def test_parser():
    """Test the stats parser with sample data."""
    print("\n" + "=" * 60)
    print("TEST 1: Stats Parser")
    print("=" * 60)

    parser = StatsParser()

    # Read sample stats
    with open('sample_ingress_stats.txt', 'r') as f:
        content = f.read()

    # Find and parse tab-separated samples (header + data lines)
    lines = content.split('\n')
    samples = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Check if this is a header line (starts with "Time Span" and has tabs)
        if line.startswith('Time Span\t') and i + 1 < len(lines):
            # Get the data line too
            data_line = lines[i + 1].strip()
            if data_line.startswith('ALL TIME\t'):
                samples.append(line + '\n' + data_line)
                i += 2  # Skip the data line
                continue
        i += 1

    print(f"\nFound {len(samples)} tab-separated sample(s)")

    for i, sample in enumerate(samples[:3], 1):
        print(f"\nSample {i}:")
        result = parser.parse(sample)

        if 'error' in result:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Parsed successfully")
            print(f"  Agent: {result.get(1, {}).get('value', 'N/A')}")
            print(f"  Faction: {result.get(2, {}).get('value', 'N/A')}")
            print(f"  Level: {result.get(5, {}).get('value', 'N/A')}")
            print(f"  Lifetime AP: {result.get(6, {}).get('value', 'N/A')}")
            print(f"  Format: {result.get('format', 'unknown')}")
            print(f"  Stats count: {result.get('stats_count', 0)}")


async def test_database():
    """Test database operations."""
    print("\n" + "=" * 60)
    print("TEST 2: Database Operations")
    print("=" * 60)

    # Initialize database
    db = initialize_database('sqlite:///test_bot.db', create_tables=True)
    print("Database initialized")

    # Test connection
    if db.test_connection():
        print("Database connection test: PASSED")
    else:
        print("Database connection test: FAILED")

    return db


async def test_stats_submission(db, parser):
    """Test parsing and validating stats."""
    print("\n" + "=" * 60)
    print("TEST 3: Stats Parsing and Validation")
    print("=" * 60)

    # Read and parse sample stats
    with open('sample_ingress_stats.txt', 'r') as f:
        content = f.read()

    # Find first tab-separated sample (header + data)
    lines = content.split('\n')
    sample = None
    for i, line in enumerate(lines):
        if line.strip().startswith('Time Span\t') and i + 1 < len(lines):
            data_line = lines[i + 1].strip()
            if data_line.startswith('ALL TIME\t'):
                sample = line.strip() + '\n' + data_line
                break

    if not sample:
        print("Error: No valid sample found in file")
        return

    parsed = parser.parse(sample)

    if 'error' not in parsed:
        print("Stats parsed successfully")

        # Validate parsed stats
        validator = StatsValidator()
        is_valid, warnings = validator.validate_parsed_stats(parsed)

        if is_valid:
            print("Validation: PASSED")
        else:
            print(f"Validation: FAILED")
            for warning in warnings:
                print(f"  - {warning.get('message', 'Unknown warning')}")

        # Display key stats
        summary = parser.get_stat_summary(parsed)
        print(f"\nSummary:")
        print(f"  Agent: {summary.get('agent_name', 'N/A')}")
        print(f"  Faction: {summary.get('faction', 'N/A')}")
        print(f"  Level: {summary.get('level', 'N/A')}")
        print(f"  Lifetime AP: {summary.get('lifetime_ap', 'N/A')}")
        print(f"  Valid numeric stats: {summary.get('valid_numeric_stats', 0)}")
    else:
        print(f"Parse error: {parsed['error']}")


async def test_bot_commands(db):
    """Test bot command handlers."""
    print("\n" + "=" * 60)
    print("TEST 4: Bot Commands")
    print("=" * 60)

    handlers = BotHandlers(db)
    mock_context = MockContext(db)

    # Test /start command
    print("\nTesting /start command:")
    update = MockUpdate("/start")
    await handlers.start_command(update, mock_context)

    # Test /help command
    print("\nTesting /help command:")
    update = MockUpdate("/help")
    await handlers.help_command(update, mock_context)

    # Test /leaderboard command
    print("\nTesting /leaderboard command:")
    update = MockUpdate("/leaderboard")
    await handlers.leaderboard_command(update, mock_context)


async def test_stats_format_variations(parser):
    """Test different stat format variations."""
    print("\n" + "=" * 60)
    print("TEST 5: Format Variations")
    print("=" * 60)

    with open('sample_ingress_stats.txt', 'r') as f:
        content = f.read()

    # Test tab-separated format
    print("\n1. Tab-separated format:")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('Time Span\t') and i + 1 < len(lines):
            data_line = lines[i + 1].strip()
            if data_line.startswith('ALL TIME\t'):
                sample = line.strip() + '\n' + data_line
                result = parser.parse(sample)
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                else:
                    print(f"   PASSED - Agent: {result.get(1, {}).get('value', 'N/A')}")
                break

    # Test space-separated format
    print("\n2. Space-separated format (Telegram):")
    data_start = False
    for i, line in enumerate(lines):
        if data_start and line.strip().startswith('Time Span '):
            if i + 1 < len(lines) and lines[i + 1].strip().startswith('ALL TIME '):
                sample = line.strip() + '\n' + lines[i + 1].strip()
                result = parser.parse(sample)
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                else:
                    print(f"   PASSED - Agent: {result.get(1, {}).get('value', 'N/A')}")
                break
        if 'SPACE-SEPARATED' in line:
            data_start = True


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 20 + "BOT TEST SUITE" + " " * 24 + "║")
    print("╚" + "═" * 58 + "╝")

    # Configure logging
    setup_logger(level='DEBUG', log_file='test_results.log')
    print("Logging configured (test_results.log)")

    # Run tests
    try:
        await test_parser()
        db = await test_database()
        await test_stats_submission(db, StatsParser())
        await test_bot_commands(db)
        await test_stats_format_variations(StatsParser())

        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("All tests completed")
        print("Results logged to: test_results.log")
        print("Database created at: test_bot.db")
        print("\nTo monitor logs while testing:")
        print("  tail -f test_results.log")

    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if 'db' in locals():
            db.close()
        # Optionally remove test database
        # if os.path.exists('test_bot.db'):
        #     os.remove('test_bot.db')


if __name__ == '__main__':
    asyncio.run(main())
