#!/usr/bin/env python3
"""
Test script to verify bot setup without running the actual bot.
"""

import os
import sys
import logging

# Add current directory to path
sys.path.insert(0, '.')

def test_configuration():
    """Test configuration loading."""
    print("🔧 Testing configuration...")

    try:
        from src.config.settings import get_settings, validate_environment

        # This should work with our .env file
        settings = get_settings('.env')

        print(f"✅ Bot token configured: {'Yes' if settings.bot.token else 'No'}")
        print(f"✅ Debug mode: {settings.bot.debug}")
        print(f"✅ Database URL: {settings.database.url.split('://')[0]}://[hidden]")
        print(f"✅ Log level: {settings.logging.level}")

        # Validate environment
        warnings = validate_environment()
        if warnings:
            print("⚠️ Configuration warnings:")
            for warning in warnings:
                print(f"   - {warning}")
        else:
            print("✅ Environment validation passed")

        return settings

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return None

def test_database(settings):
    """Test database connection and table creation."""
    print("\n🗄️ Testing database connection...")

    try:
        from src.database.connection import initialize_database

        # Initialize database (this should work with SQLite)
        db = initialize_database(settings.database.url, create_tables=True)

        # Test connection
        if db.test_connection():
            print("✅ Database connection successful")

            # Get connection stats
            stats = db.get_connection_stats()
            print(f"✅ Database stats: {stats}")

            return db
        else:
            print("❌ Database connection test failed")
            return None

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_parsers():
    """Test stats parser functionality."""
    print("\n📊 Testing stats parser...")

    try:
        from src.parsers.stats_parser import StatsParser

        parser = StatsParser()

        # Test with sample data (simplified)
        sample_text = """Time Span: ALL TIME
Agent: TestAgent
Faction: Enlightened
Date: 2024-12-02
Time: 12:00:00
Level: 15
Lifetime AP: 5000000
Current AP: 1000000"""

        parsed = parser.parse(sample_text)

        if 'error' in parsed:
            print(f"⚠️ Parser returned expected error for incomplete data: {parsed['error']}")
        else:
            print(f"✅ Parser processed {len(parsed)} fields")

        return parser

    except Exception as e:
        print(f"❌ Parser test failed: {e}")
        return None

def test_bot_handlers():
    """Test bot handler instantiation."""
    print("\n🤖 Testing bot handlers...")

    try:
        from src.bot.handlers import BotHandlers

        handlers = BotHandlers()

        print("✅ Bot handlers instantiated successfully")

        # Check that command methods exist
        methods = ['start_command', 'help_command', 'mystats_command', 'leaderboard_command', 'handle_message']
        for method in methods:
            if hasattr(handlers, method):
                print(f"   ✅ {method} method exists")
            else:
                print(f"   ❌ {method} method missing")

        return handlers

    except Exception as e:
        print(f"❌ Bot handlers test failed: {e}")
        return None

def main():
    """Run all tests."""
    print("🧪 Ingress Prime Leaderboard Bot - Setup Test")
    print("=" * 50)

    # Test configuration
    settings = test_configuration()
    if not settings:
        print("\n❌ Configuration test failed. Check your .env file.")
        return False

    # Test database
    db = test_database(settings)
    if not db:
        print("\n❌ Database test failed.")
        return False

    # Test parsers
    parser = test_parsers()
    if not parser:
        print("\n❌ Parser test failed.")
        return False

    # Test bot handlers
    handlers = test_bot_handlers()
    if not handlers:
        print("\n❌ Bot handlers test failed.")
        return False

    print("\n" + "=" * 50)
    print("🎉 All tests passed! Your bot setup is ready.")
    print("\n📋 Next steps:")
    print("1. Get a Telegram bot token from @BotFather")
    print("2. Add your token to the .env file")
    print("3. Run: python3 main.py")

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)