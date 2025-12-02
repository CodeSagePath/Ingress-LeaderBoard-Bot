#!/usr/bin/env python3
"""
Demonstration of the enhanced validation system for Ingress Leaderboard Bot.

This script shows the new business rules validation in action.
"""

import sys
sys.path.insert(0, 'src')

from parsers.validator import StatsValidator


def demo_validation():
    """Demonstrate the enhanced validation system."""

    validator = StatsValidator()

    print("🔍 Ingress Leaderboard Enhanced Validation System Demo")
    print("=" * 60)

    # Demo 1: Valid submission
    print("\n1️⃣ VALID SUBMISSION:")
    valid_data = {
        # Required fields
        1: {'idx': 1, 'name': 'Agent Name', 'value': 'ValidPlayer', 'type': 'S'},
        2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Enlightened', 'type': 'S'},
        3: {'idx': 3, 'name': 'Date', 'value': '2024-06-15', 'type': 'S'},
        4: {'idx': 4, 'name': 'Time', 'value': '14:30:00', 'type': 'S'},

        # Valid stats
        5: {'idx': 5, 'name': 'Level', 'value': '12', 'type': 'N'},
        6: {'idx': 6, 'name': 'Lifetime AP', 'value': '10000000', 'type': 'N'},
        7: {'idx': 7, 'name': 'Current AP', 'value': '8500000', 'type': 'N'},
        8: {'idx': 8, 'name': 'Unique Portals Visited', 'value': '5000', 'type': 'N'},
        14: {'idx': 14, 'name': 'Resonators Deployed', 'value': '10000', 'type': 'N'},
        15: {'idx': 15, 'name': 'Links Created', 'value': '15000', 'type': 'N'},
    }

    is_valid, warnings = validator.validate_parsed_stats(valid_data)
    print(f"   ✅ Valid: {is_valid}")
    print(f"   ⚠️  Warnings: {len(warnings)}")

    # Demo 2: AP inconsistency
    print("\n2️⃣ AP INCONSISTENCY:")
    ap_issue_data = valid_data.copy()
    ap_issue_data[6]['value'] = '5000000'  # Lifetime AP
    ap_issue_data[7]['value'] = '6000000'  # Current AP exceeds lifetime

    is_valid, warnings = validator.validate_parsed_stats(ap_issue_data)
    print(f"   ✅ Valid: {is_valid}")
    print(f"   ⚠️  Warnings: {len(warnings)}")
    for warning in warnings:
        if warning['type'] == 'ap_inconsistency':
            print(f"   ❌ {warning['message']}")

    # Demo 3: Level mismatch
    print("\n3️⃣ LEVEL PROGRESSION ISSUE:")
    level_issue_data = valid_data.copy()
    level_issue_data[5]['value'] = '15'  # High level
    level_issue_data[6]['value'] = '5000000'  # Too low AP for level 15

    is_valid, warnings = validator.validate_parsed_stats(level_issue_data)
    print(f"   ✅ Valid: {is_valid}")
    print(f"   ⚠️  Warnings: {len(warnings)}")
    for warning in warnings:
        if warning['type'] == 'insufficient_ap_for_level':
            print(f"   ⚠️  {warning['message']}")

    # Demo 4: Unusual stat ratios
    print("\n4️⃣ UNUSUAL BUILDING RATIOS:")
    ratio_issue_data = valid_data.copy()
    ratio_issue_data[14]['value'] = '1000'    # Low resonators
    ratio_issue_data[15]['value'] = '10000'   # Very high links (10x ratio)

    is_valid, warnings = validator.validate_parsed_stats(ratio_issue_data)
    print(f"   ✅ Valid: {is_valid}")
    print(f"   ⚠️  Warnings: {len(warnings)}")
    for warning in warnings:
        if warning['type'] == 'unusual_building_ratio':
            print(f"   ⚠️  {warning['message']}")

    # Demo 5: Future date
    print("\n5️⃣ FUTURE DATE:")
    date_issue_data = valid_data.copy()
    from datetime import date, timedelta
    future_date = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
    date_issue_data[3]['value'] = future_date

    is_valid, warnings = validator.validate_parsed_stats(date_issue_data)
    print(f"   ✅ Valid: {is_valid}")
    print(f"   ⚠️  Warnings: {len(warnings)}")
    for warning in warnings:
        if warning['type'] == 'future_date':
            print(f"   ❌ {warning['message']}")

    print("\n" + "=" * 60)
    print("🎯 Enhanced Validation Features:")
    print("   • AP Consistency: Current AP ≤ Lifetime AP")
    print("   • Level Progression: AP matches expected ranges for level")
    print("   • Cross-Stat Dependencies: Logical relationships between stats")
    print("   • Temporal Consistency: Reasonable dates and times")
    print("   • Building Dependencies: Valid ratios between building stats")
    print("   • Discovery Dependencies: Correlation between exploration stats")
    print("   • Combat Dependencies: Logical combat stat relationships")
    print("\n✨ The enhanced validation system provides:")
    print("   • Detailed error messages with context")
    print("   • Severity levels (error, warning, info)")
    print("   • Early detection of data entry errors")
    print("   • Improved data quality and user experience")


if __name__ == '__main__':
    demo_validation()