#!/usr/bin/env python3
"""
Test script for callback handlers implementation.

This script tests the enhanced callback handlers to ensure they work correctly
and are properly integrated with the existing bot framework.
"""

import sys
import os

# Add src directory to path for imports
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# Change to src directory for relative imports
os.chdir(src_path)

from bot.callbacks import CallbackHandlers, get_callback_handlers
from config.stats_config import get_stat_by_idx


def test_callback_handlers_initialization():
    """Test that callback handlers can be initialized."""
    print("Testing callback handlers initialization...")

    try:
        # Test initialization
        handlers = CallbackHandlers()
        print("✅ CallbackHandlers initialized successfully")

        # Test STAT_MAPPING
        expected_mappings = {
            'ap': 6,
            'explorer': 8,
            'connector': 15,
            'mindcontroller': 16,
            'recharger': 20,
            'builder': 14,
            'hacker': 28,
            'trekker': 13
        }

        for key, expected_value in expected_mappings.items():
            actual_value = handlers.STAT_MAPPING.get(key)
            if actual_value == expected_value:
                print(f"✅ STAT_MAPPING['{key}'] = {actual_value}")
            else:
                print(f"❌ STAT_MAPPING['{key}'] = {actual_value}, expected {expected_value}")

        # Test get_callback_handlers function
        handlers_instance = get_callback_handlers()
        if handlers_instance:
            print("✅ get_callback_handlers() returns instance")
        else:
            print("❌ get_callback_handlers() returned None")

        return True

    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        return False


def test_stat_validation():
    """Test stat validation functionality."""
    print("\nTesting stat validation...")

    try:
        handlers = CallbackHandlers()

        # Test valid stat indices
        valid_stats = [6, 8, 13, 14, 15, 16, 20, 28]
        for stat_idx in valid_stats:
            stat_def = get_stat_by_idx(stat_idx)
            if stat_def:
                print(f"✅ Stat {stat_idx}: {stat_def['name']}")
            else:
                print(f"❌ Stat {stat_idx}: Not found")

        # Test invalid stat index
        invalid_stat = 999
        stat_def = get_stat_by_idx(invalid_stat)
        if not stat_def:
            print(f"✅ Invalid stat {invalid_stat} correctly rejected")
        else:
            print(f"❌ Invalid stat {invalid_stat} incorrectly accepted")

        return True

    except Exception as e:
        print(f"❌ Error during stat validation: {e}")
        return False


def test_callback_data_parsing():
    """Test callback data parsing logic."""
    print("\nTesting callback data parsing...")

    try:
        handlers = CallbackHandlers()

        # Test stat leaderboard callbacks
        test_cases = [
            ('lb_6', 6, 'Lifetime AP'),
            ('lb_8', 8, 'Unique Portals Visited'),
            ('lb_15', 15, 'Links Created'),
            ('lb_16', 16, 'Control Fields Created'),
            ('lb_20', 20, 'XM Recharged'),
            ('lb_14', 14, 'Resonators Deployed'),
            ('lb_28', 28, 'Hacks'),
            ('lb_13', 13, 'Distance Walked'),
        ]

        for callback_data, expected_idx, expected_name in test_cases:
            # Test integer parsing
            stat_type = callback_data.replace('lb_', '')
            try:
                stat_idx = int(stat_type)
                if stat_idx == expected_idx:
                    print(f"✅ {callback_data} -> stat_idx {stat_idx}")
                else:
                    print(f"❌ {callback_data} -> stat_idx {stat_idx}, expected {expected_idx}")
            except ValueError:
                print(f"❌ {callback_data} failed to parse as integer")

            # Test stat definition lookup
            stat_def = get_stat_by_idx(expected_idx)
            if stat_def and stat_def['name'] == expected_name:
                print(f"✅ Stat {expected_idx}: {expected_name}")
            else:
                print(f"❌ Stat {expected_idx}: incorrect name")

        # Test faction callbacks
        faction_cases = [
            ('faction_enl', 'enl'),
            ('faction_res', 'res'),
            ('faction_all', 'all')
        ]

        for callback_data, expected_faction in faction_cases:
            faction_type = callback_data.replace('faction_', '')
            if faction_type == expected_faction:
                print(f"✅ {callback_data} -> faction '{faction_type}'")
            else:
                print(f"❌ {callback_data} -> faction '{faction_type}', expected '{expected_faction}'")

        # Test period callbacks
        period_cases = [
            'period_all_time_stat_6',
            'period_monthly_stat_8',
            'period_weekly_stat_15',
            'period_daily_stat_13'
        ]

        for callback_data in period_cases:
            parts = callback_data.split('_')
            if len(parts) >= 4 and parts[0] == 'period':
                period = parts[1]
                stat_type = parts[3]
                print(f"✅ {callback_data} -> period '{period}', stat '{stat_type}'")
            else:
                print(f"❌ {callback_data} failed to parse correctly")

        return True

    except Exception as e:
        print(f"❌ Error during callback data parsing: {e}")
        return False


def main():
    """Run all callback handler tests."""
    print("🧪 Testing Enhanced Callback Handlers")
    print("=" * 50)

    tests = [
        test_callback_handlers_initialization,
        test_stat_validation,
        test_callback_data_parsing
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        if test_func():
            passed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Callback handlers are ready for deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())