"""
Test suite for Business Rules Validator.

This module tests the enhanced business rules validation functionality
for Ingress Prime statistics.
"""

import unittest
import sys
import os

# Add project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parsers.business_rules_validator import BusinessRulesValidator


class TestBusinessRulesValidator(unittest.TestCase):
    """Test cases for BusinessRulesValidator."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = BusinessRulesValidator()

    def test_ap_consistency_valid(self):
        """Test valid AP consistency (Current AP ≤ Lifetime AP)."""
        parsed_data = {
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '1000000', 'type': 'N'},
            7: {'idx': 7, 'name': 'Current AP', 'value': '500000', 'type': 'N'}
        }

        warnings = self.validator._validate_ap_consistency(parsed_data)
        self.assertEqual(len(warnings), 0)

    def test_ap_consistency_current_exceeds_lifetime(self):
        """Test invalid AP consistency (Current AP > Lifetime AP)."""
        parsed_data = {
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '1000000', 'type': 'N'},
            7: {'idx': 7, 'name': 'Current AP', 'value': '1500000', 'type': 'N'}
        }

        warnings = self.validator._validate_ap_consistency(parsed_data)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'ap_inconsistency')
        self.assertEqual(warnings[0]['severity'], 'error')

    def test_ap_consistency_low_current_ap(self):
        """Test warning for unusually low Current AP."""
        parsed_data = {
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '10000000', 'type': 'N'},
            7: {'idx': 7, 'name': 'Current AP', 'value': '3000000', 'type': 'N'}  # 30% of lifetime, below 80% threshold
        }

        warnings = self.validator._validate_ap_consistency(parsed_data)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'low_current_ap')
        self.assertEqual(warnings[0]['severity'], 'warning')

    def test_level_progression_valid(self):
        """Test valid level progression."""
        parsed_data = {
            5: {'idx': 5, 'name': 'Level', 'value': '10', 'type': 'N'},
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '5000000', 'type': 'N'}
        }

        warnings = self.validator._validate_level_progression(parsed_data)
        self.assertEqual(len(warnings), 0)

    def test_level_progression_insufficient_ap(self):
        """Test level with insufficient AP."""
        parsed_data = {
            5: {'idx': 5, 'name': 'Level', 'value': '10', 'type': 'N'},
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '2000000', 'type': 'N'}  # Below minimum for level 10
        }

        warnings = self.validator._validate_level_progression(parsed_data)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'insufficient_ap_for_level')
        self.assertEqual(warnings[0]['severity'], 'warning')

    def test_level_progression_excessive_ap(self):
        """Test level with excessive AP."""
        parsed_data = {
            5: {'idx': 5, 'name': 'Level', 'value': '8', 'type': 'N'},
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '18000000', 'type': 'N'}  # Way above level 8
        }

        warnings = self.validator._validate_level_progression(parsed_data)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'excessive_ap_for_level')
        self.assertEqual(warnings[0]['severity'], 'info')

    def test_level_progression_invalid_level(self):
        """Test invalid level value."""
        parsed_data = {
            5: {'idx': 5, 'name': 'Level', 'value': '20', 'type': 'N'},  # Invalid level
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '5000000', 'type': 'N'}
        }

        warnings = self.validator._validate_level_progression(parsed_data)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'invalid_level')
        self.assertEqual(warnings[0]['severity'], 'error')

    def test_building_dependencies_valid(self):
        """Test valid building dependencies."""
        parsed_data = {
            14: {'idx': 14, 'name': 'Resonators Deployed', 'value': '10000', 'type': 'N'},
            15: {'idx': 15, 'name': 'Links Created', 'value': '15000', 'type': 'N'},
            16: {'idx': 16, 'name': 'Control Fields Created', 'value': '5000', 'type': 'N'},
            17: {'idx': 17, 'name': 'MU Captured', 'value': '25000000', 'type': 'N'}
        }

        warnings = self.validator._validate_building_dependencies(parsed_data)
        self.assertEqual(len(warnings), 0)

    def test_building_dependencies_unusual_links_ratio(self):
        """Test unusual links to resonators ratio."""
        parsed_data = {
            14: {'idx': 14, 'name': 'Resonators Deployed', 'value': '1000', 'type': 'N'},
            15: {'idx': 15, 'name': 'Links Created', 'value': '5000', 'type': 'N'},  # 5x resonators
        }

        warnings = self.validator._validate_building_dependencies(parsed_data)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'unusual_building_ratio')
        self.assertEqual(warnings[0]['severity'], 'warning')

    def test_building_dependencies_unusual_fields_ratio(self):
        """Test unusual fields to links ratio."""
        parsed_data = {
            15: {'idx': 15, 'name': 'Links Created', 'value': '1000', 'type': 'N'},
            16: {'idx': 16, 'name': 'Control Fields Created', 'value': '5000', 'type': 'N'},  # 5x links
        }

        warnings = self.validator._validate_building_dependencies(parsed_data)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'unusual_field_ratio')
        self.assertEqual(warnings[0]['severity'], 'warning')

    def test_discovery_dependencies_valid(self):
        """Test valid discovery dependencies."""
        parsed_data = {
            8: {'idx': 8, 'name': 'Unique Portals Visited', 'value': '5000', 'type': 'N'},
            13: {'idx': 13, 'name': 'Distance Walked', 'value': '2500', 'type': 'N'},  # 0.5 km per portal
            11: {'idx': 11, 'name': 'XM Collected', 'value': '500000', 'type': 'N'},
            28: {'idx': 28, 'name': 'Hacks', 'value': '5000', 'type': 'N'}  # 100 XM per hack
        }

        warnings = self.validator._validate_discovery_dependencies(parsed_data)
        self.assertEqual(len(warnings), 0)

    def test_discovery_dependencies_low_distance(self):
        """Test unusually low distance for portals visited."""
        parsed_data = {
            8: {'idx': 8, 'name': 'Unique Portals Visited', 'value': '5000', 'type': 'N'},
            13: {'idx': 13, 'name': 'Distance Walked', 'value': '500', 'type': 'N'},  # 0.1 km per portal
        }

        warnings = self.validator._validate_discovery_dependencies(parsed_data)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'low_distance_for_portals')
        self.assertEqual(warnings[0]['severity'], 'info')

    def test_discovery_dependencies_low_xm(self):
        """Test unusually low XM for hacks."""
        parsed_data = {
            11: {'idx': 11, 'name': 'XM Collected', 'value': '20000', 'type': 'N'},
            28: {'idx': 28, 'name': 'Hacks', 'value': '5000', 'type': 'N'},  # 4 XM per hack
        }

        warnings = self.validator._validate_discovery_dependencies(parsed_data)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'low_xm_for_hacks')
        self.assertEqual(warnings[0]['severity'], 'info')

    def test_combat_dependencies_valid(self):
        """Test valid combat dependencies."""
        parsed_data = {
            23: {'idx': 23, 'name': 'Resonators Destroyed', 'value': '2000', 'type': 'N'},
            24: {'idx': 24, 'name': 'Portals Neutralized', 'value': '3000', 'type': 'N'},  # 1.5x resonators
            25: {'idx': 25, 'name': 'Enemy Links Destroyed', 'value': '1000', 'type': 'N'}
        }

        warnings = self.validator._validate_combat_dependencies(parsed_data)
        self.assertEqual(len(warnings), 0)

    def test_combat_dependencies_unusual_portal_ratio(self):
        """Test unusual portals neutralized ratio."""
        parsed_data = {
            23: {'idx': 23, 'name': 'Resonators Destroyed', 'value': '1000', 'type': 'N'},
            24: {'idx': 24, 'name': 'Portals Neutralized', 'value': '10000', 'type': 'N'},  # 10x resonators
        }

        warnings = self.validator._validate_combat_dependencies(parsed_data)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'unusual_combat_ratio')
        self.assertEqual(warnings[0]['severity'], 'warning')

    def test_temporal_consistency_valid(self):
        """Test valid temporal consistency."""
        from datetime import date, timedelta
        today = date.today()
        valid_date = today - timedelta(days=1)

        parsed_data = {
            3: {'idx': 3, 'name': 'Date', 'value': valid_date.strftime('%Y-%m-%d'), 'type': 'S'}
        }

        warnings = self.validator._validate_temporal_consistency(parsed_data)
        self.assertEqual(len(warnings), 0)

    def test_temporal_consistency_future_date(self):
        """Test future date validation."""
        from datetime import date, timedelta
        today = date.today()
        future_date = today + timedelta(days=5)

        parsed_data = {
            3: {'idx': 3, 'name': 'Date', 'value': future_date.strftime('%Y-%m-%d'), 'type': 'S'}
        }

        warnings = self.validator._validate_temporal_consistency(parsed_data)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'future_date')
        self.assertEqual(warnings[0]['severity'], 'error')

    def test_temporal_consistency_old_date(self):
        """Test very old date validation."""
        from datetime import date, timedelta
        today = date.today()
        old_date = today - timedelta(days=800)  # More than 2 years

        parsed_data = {
            3: {'idx': 3, 'name': 'Date', 'value': old_date.strftime('%Y-%m-%d'), 'type': 'S'}
        }

        warnings = self.validator._validate_temporal_consistency(parsed_data)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'very_old_date')
        self.assertEqual(warnings[0]['severity'], 'warning')

    def test_temporal_consistency_invalid_date_format(self):
        """Test invalid date format."""
        parsed_data = {
            3: {'idx': 3, 'name': 'Date', 'value': '2024/01/15', 'type': 'S'}  # Wrong format
        }

        warnings = self.validator._validate_temporal_consistency(parsed_data)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['type'], 'invalid_date_format')
        self.assertEqual(warnings[0]['severity'], 'error')

    def test_get_stat_value_valid(self):
        """Test getting valid stat value."""
        parsed_data = {
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '1000000', 'type': 'N'}
        }

        value = self.validator._get_stat_value(parsed_data, 6)
        self.assertEqual(value, 1000000)

    def test_get_stat_value_missing(self):
        """Test getting missing stat value."""
        parsed_data = {}

        value = self.validator._get_stat_value(parsed_data, 6)
        self.assertIsNone(value)

    def test_get_stat_value_invalid_format(self):
        """Test getting stat value with invalid format."""
        parsed_data = {
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': 'invalid', 'type': 'N'}
        }

        value = self.validator._get_stat_value(parsed_data, 6)
        self.assertIsNone(value)

    def test_business_rules_integration(self):
        """Test complete business rules validation integration."""
        parsed_data = {
            # Required fields
            1: {'idx': 1, 'name': 'Agent Name', 'value': 'TestAgent', 'type': 'S'},
            2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Enlightened', 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': '2024-06-15', 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': '10:30:00', 'type': 'S'},

            # Stats with issues
            5: {'idx': 5, 'name': 'Level', 'value': '10', 'type': 'N'},
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '2000000', 'type': 'N'},  # Too low for level 10
            7: {'idx': 7, 'name': 'Current AP', 'value': '2500000', 'type': 'N'},  # Exceeds lifetime
            14: {'idx': 14, 'name': 'Resonators Deployed', 'value': '1000', 'type': 'N'},
            15: {'idx': 15, 'name': 'Links Created', 'value': '10000', 'type': 'N'},  # Unusual ratio
        }

        warnings = self.validator.validate_business_rules(parsed_data)

        # Should have multiple warnings
        self.assertGreater(len(warnings), 0)

        # Check for expected warning types
        warning_types = [w['type'] for w in warnings]
        self.assertIn('ap_inconsistency', warning_types)
        self.assertIn('insufficient_ap_for_level', warning_types)
        self.assertIn('unusual_building_ratio', warning_types)

    def test_valid_complete_submission(self):
        """Test a complete, valid submission with no business rule violations."""
        parsed_data = {
            # Required fields
            1: {'idx': 1, 'name': 'Agent Name', 'value': 'ValidAgent', 'type': 'S'},
            2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Enlightened', 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': '2024-06-15', 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': '10:30:00', 'type': 'S'},

            # Valid stats
            5: {'idx': 5, 'name': 'Level', 'value': '12', 'type': 'N'},
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '10000000', 'type': 'N'},
            7: {'idx': 7, 'name': 'Current AP', 'value': '8500000', 'type': 'N'},  # 85% of lifetime, above 80% threshold
            8: {'idx': 8, 'name': 'Unique Portals Visited', 'value': '5000', 'type': 'N'},
            11: {'idx': 11, 'name': 'XM Collected', 'value': '10000000', 'type': 'N'},
            13: {'idx': 13, 'name': 'Distance Walked', 'value': '2500', 'type': 'N'},
            14: {'idx': 14, 'name': 'Resonators Deployed', 'value': '10000', 'type': 'N'},
            15: {'idx': 15, 'name': 'Links Created', 'value': '15000', 'type': 'N'},
            16: {'idx': 16, 'name': 'Control Fields Created', 'value': '5000', 'type': 'N'},
            17: {'idx': 17, 'name': 'MU Captured', 'value': '25000000', 'type': 'N'},
            23: {'idx': 23, 'name': 'Resonators Destroyed', 'value': '2000', 'type': 'N'},
            24: {'idx': 24, 'name': 'Portals Neutralized', 'value': '3000', 'type': 'N'},
            25: {'idx': 25, 'name': 'Enemy Links Destroyed', 'value': '1000', 'type': 'N'},
            28: {'idx': 28, 'name': 'Hacks', 'value': '5000', 'type': 'N'},
        }

        warnings = self.validator.validate_business_rules(parsed_data)

        # Should have no warnings for this valid submission
        if len(warnings) > 0:
            print(f"Unexpected warnings for valid submission: {[w['type'] for w in warnings]}")
        self.assertEqual(len(warnings), 0)


if __name__ == '__main__':
    unittest.main()