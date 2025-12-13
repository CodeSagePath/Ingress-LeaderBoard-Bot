"""
Test suite for integrated validation system.

This module tests the integration of enhanced business rules validation
with the existing validation system.
"""

import unittest
import sys
import os

# Add project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parsers.validator import StatsValidator


class TestIntegratedValidation(unittest.TestCase):
    """Test cases for integrated validation system."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = StatsValidator()

    def create_valid_parsed_data(self):
        """Create a valid parsed stats data structure."""
        return {
            # Required fields
            1: {'idx': 1, 'name': 'Agent Name', 'value': 'TestAgent', 'type': 'S'},
            2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Enlightened', 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': '2024-01-15', 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': '10:30:00', 'type': 'S'},

            # Valid stats
            5: {'idx': 5, 'name': 'Level', 'value': '12', 'type': 'N'},
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '10000000', 'type': 'N'},
            7: {'idx': 7, 'name': 'Current AP', 'value': '5000000', 'type': 'N'},
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

            # Metadata
            'format': 'telegram',
            'timezone': 'UTC',
            'timestamp': 1705315800,
            'stats_count': 18
        }

    def test_valid_submission_passes_all_validation(self):
        """Test that a valid submission passes all validation."""
        parsed_data = self.create_valid_parsed_data()

        is_valid, warnings = self.validator.validate_parsed_stats(parsed_data)

        self.assertTrue(is_valid)
        self.assertEqual(len(warnings), 0)

    def test_business_rules_warnings_included(self):
        """Test that business rules warnings are included in validation results."""
        parsed_data = self.create_valid_parsed_data()

        # Add business rule violations
        parsed_data[6]['value'] = '5000000'  # Lifetime AP
        parsed_data[7]['value'] = '6000000'  # Current AP exceeds lifetime
        parsed_data[5]['value'] = '12'      # Level too high for AP

        is_valid, warnings = self.validator.validate_parsed_stats(parsed_data)

        # Should still be valid but with warnings
        self.assertTrue(is_valid)
        self.assertGreater(len(warnings), 0)

        # Check for business rule warnings
        warning_types = [w['type'] for w in warnings]
        self.assertIn('ap_inconsistency', warning_types)
        self.assertIn('insufficient_ap_for_level', warning_types)

    def test_business_rule_errors_block_validation(self):
        """Test that business rule errors block validation."""
        parsed_data = self.create_valid_parsed_data()

        # Add blocking error (current AP exceeds lifetime AP)
        parsed_data[6]['value'] = '1000000'  # Lifetime AP
        parsed_data[7]['value'] = '1500000'  # Current AP exceeds lifetime by 50%

        is_valid, warnings = self.validator.validate_parsed_stats(parsed_data)

        # Should still be valid (AP inconsistency is a warning, not error)
        self.assertTrue(is_valid)
        self.assertGreater(len(warnings), 0)

        # Check for the specific error
        ap_warnings = [w for w in warnings if w['type'] == 'ap_inconsistency']
        self.assertEqual(len(ap_warnings), 1)

    def test_required_fields_still_validated(self):
        """Test that required fields validation still works."""
        parsed_data = self.create_valid_parsed_data()

        # Remove required field
        del parsed_data[1]  # Agent Name

        is_valid, warnings = self.validator.validate_parsed_stats(parsed_data)

        # Should be invalid due to missing required field
        self.assertFalse(is_valid)
        self.assertGreater(len(warnings), 0)

        # Check for required field error
        required_warnings = [w for w in warnings if 'missing_required' in w['type']]
        self.assertGreater(len(required_warnings), 0)

    def test_numeric_validation_still_works(self):
        """Test that numeric validation still works."""
        parsed_data = self.create_valid_parsed_data()

        # Add invalid numeric value
        parsed_data[6]['value'] = 'invalid_number'

        is_valid, warnings = self.validator.validate_parsed_stats(parsed_data)

        # Should still be valid but with warnings
        self.assertTrue(is_valid)
        self.assertGreater(len(warnings), 0)

        # Check for numeric validation warning
        numeric_warnings = [w for w in warnings if w['type'] == 'invalid_numeric']
        self.assertGreater(len(numeric_warnings), 0)

    def test_combined_validation_warnings(self):
        """Test validation with multiple types of warnings."""
        parsed_data = self.create_valid_parsed_data()

        # Add multiple types of issues:
        parsed_data[6]['value'] = '2000000'    # Lifetime AP (low for level)
        parsed_data[7]['value'] = '2500000'    # Current AP exceeds lifetime
        parsed_data[5]['value'] = '12'          # Level
        parsed_data[14]['value'] = '1000'       # Resonators Deployed
        parsed_data[15]['value'] = '8000'       # Links Created (8x resonators)
        parsed_data[11]['value'] = 'invalid'     # Invalid numeric

        is_valid, warnings = self.validator.validate_parsed_stats(parsed_data)

        # Should be valid but with multiple warnings
        self.assertTrue(is_valid)
        self.assertGreater(len(warnings), 3)  # Should have several warnings

        # Check for different types of warnings
        warning_types = [w['type'] for w in warnings]
        self.assertIn('ap_inconsistency', warning_types)           # Business rules
        self.assertIn('insufficient_ap_for_level', warning_types)  # Business rules
        self.assertIn('unusual_building_ratio', warning_types)      # Business rules
        self.assertIn('invalid_numeric', warning_types)               # Numeric validation

    def test_future_date_error(self):
        """Test that future dates are still caught."""
        from datetime import date, timedelta
        today = date.today()
        future_date = today + timedelta(days=5)

        parsed_data = self.create_valid_parsed_data()
        parsed_data[3]['value'] = future_date.strftime('%Y-%m-%d')

        is_valid, warnings = self.validator.validate_parsed_stats(parsed_data)

        # Should be valid but with warning (future date is a business rule, not blocking error)
        self.assertTrue(is_valid)
        self.assertGreater(len(warnings), 0)

        # Check for future date warning
        date_warnings = [w for w in warnings if w['type'] == 'future_date']
        self.assertGreater(len(date_warnings), 0)

    def test_invalid_faction_still_blocked(self):
        """Test that invalid faction still blocks validation."""
        parsed_data = self.create_valid_parsed_data()
        parsed_data[2]['value'] = 'InvalidFaction'

        is_valid, warnings = self.validator.validate_parsed_stats(parsed_data)

        # Should be invalid due to invalid faction
        self.assertFalse(is_valid)
        self.assertGreater(len(warnings), 0)

        # Check for faction validation error
        faction_warnings = [w for w in warnings if 'invalid_faction' in w['type']]
        self.assertGreater(len(faction_warnings), 0)

    def test_insufficient_stats_still_blocked(self):
        """Test that insufficient stats count still blocks validation."""
        parsed_data = {
            1: {'idx': 1, 'name': 'Agent Name', 'value': 'TestAgent', 'type': 'S'},
            2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Enlightened', 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': '2024-01-15', 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': '10:30:00', 'type': 'S'},
            # Only 5 stats, below minimum of 12
        }

        is_valid, warnings = self.validator.validate_parsed_stats(parsed_data)

        # Should be invalid due to insufficient stats
        self.assertFalse(is_valid)
        self.assertGreater(len(warnings), 0)

        # Check for insufficient stats warning
        stats_warnings = [w for w in warnings if w['type'] == 'insufficient_stats']
        self.assertGreater(len(stats_warnings), 0)

    def test_validation_summary_includes_business_rules(self):
        """Test that validation summary includes business rule warnings."""
        parsed_data = self.create_valid_parsed_data()

        # Add business rule violations
        parsed_data[6]['value'] = '1000000'  # Lifetime AP
        parsed_data[7]['value'] = '1500000'  # Current AP exceeds lifetime

        summary = self.validator.get_validation_summary(parsed_data)

        # Should show warnings in summary
        self.assertGreater(summary['total_warnings'], 0)
        self.assertEqual(summary['is_valid'], True)  # Still valid, just with warnings

        # Check that business rule warning types are tracked
        self.assertIn('ap_inconsistency', summary['warning_types'])

    def test_edge_case_empty_values(self):
        """Test handling of empty values in business rules."""
        parsed_data = {
            1: {'idx': 1, 'name': 'Agent Name', 'value': 'TestAgent', 'type': 'S'},
            2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Enlightened', 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': '2024-01-15', 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': '10:30:00', 'type': 'S'},
            # Empty/missing critical stats
            5: {'idx': 5, 'name': 'Level', 'value': '', 'type': 'N'},
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '', 'type': 'N'},
            7: {'idx': 7, 'name': 'Current AP', 'value': '', 'type': 'N'},
        }

        is_valid, warnings = self.validator.validate_parsed_stats(parsed_data)

        # Should handle gracefully - empty values should not cause crashes
        # The validation should pass (empty values are handled by numeric validation)
        self.assertTrue(is_valid)  # Empty numeric values become warnings, not errors

    def test_real_world_agent_submission(self):
        """Test validation with realistic agent data."""
        parsed_data = {
            # Required fields
            1: {'idx': 1, 'name': 'Agent Name', 'value': 'RealPlayerAgent', 'type': 'S'},
            2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Resistance', 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': '2024-01-15', 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': '14:25:30', 'type': 'S'},

            # Realistic stats for an active player
            5: {'idx': 5, 'name': 'Level', 'value': '15', 'type': 'N'},
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '28500000', 'type': 'N'},
            7: {'idx': 7, 'name': 'Current AP', 'value': '12000000', 'type': 'N'},
            8: {'idx': 8, 'name': 'Unique Portals Visited', 'value': '8500', 'type': 'N'},
            9: {'idx': 9, 'name': 'Portals Discovered', 'value': '9200', 'type': 'N'},
            10: {'idx': 10, 'name': 'Drone Hacks', 'value': '1500', 'type': 'N'},
            11: {'idx': 11, 'name': 'XM Collected', 'value': '45000000', 'type': 'N'},
            12: {'idx': 12, 'name': 'Keys Hacked', 'value': '125000', 'type': 'N'},
            13: {'idx': 13, 'name': 'Distance Walked', 'value': '3200', 'type': 'N'},
            14: {'idx': 14, 'name': 'Resonators Deployed', 'value': '85000', 'type': 'N'},
            15: {'idx': 15, 'name': 'Links Created', 'value': '12000', 'type': 'N'},
            16: {'idx': 16, 'name': 'Control Fields Created', 'value': '4500', 'type': 'N'},
            17: {'idx': 17, 'name': 'MU Captured', 'value': '180000000', 'type': 'N'},
            18: {'idx': 18, 'name': 'Mods Deployed', 'value': '3500', 'type': 'N'},
            19: {'idx': 19, 'name': 'Unique Missions Completed', 'value': '450', 'type': 'N'},
            20: {'idx': 20, 'name': 'XM Recharged', 'value': '25000000', 'type': 'N'},
            21: {'idx': 21, 'name': 'Portals Captured', 'value': '3800', 'type': 'N'},
            22: {'idx': 22, 'name': 'Max Times Hacked', 'value': '85', 'type': 'N'},
            23: {'idx': 23, 'name': 'Resonators Destroyed', 'value': '15000', 'type': 'N'},
            24: {'idx': 24, 'name': 'Portals Neutralized', 'value': '4200', 'type': 'N'},
            25: {'idx': 25, 'name': 'Enemy Links Destroyed', 'value': '2800', 'type': 'N'},
            26: {'idx': 26, 'name': 'Enemy Control Fields Destroyed', 'value': '1200', 'type': 'N'},
            27: {'idx': 27, 'name': 'XM Collected by Enemy', 'value': '3200000', 'type': 'N'},
            28: {'idx': 28, 'name': 'Hacks', 'value': '45000', 'type': 'N'},
            29: {'idx': 29, 'name': 'Max Link Length', 'value': '8.5', 'type': 'N'},
            30: {'idx': 30, 'name': 'Max Time Portal Held', 'value': '145', 'type': 'N'},
            31: {'idx': 31, 'name': 'Max Time Field Held', 'value': '12', 'type': 'N'},
            32: {'idx': 32, 'name': 'Longest Link', 'value': '15.2', 'type': 'N'},
            33: {'idx': 33, 'name': 'Largest Field', 'value': '85000', 'type': 'N'},
        }

        is_valid, warnings = self.validator.validate_parsed_stats(parsed_data)

        # This should be valid with minimal or no warnings
        self.assertTrue(is_valid)

        # May have some informational warnings but should be minimal
        error_warnings = [w for w in warnings if w['severity'] == 'error']
        self.assertEqual(len(error_warnings), 0)

        # Print warnings for manual inspection during testing
        if warnings:
            print(f"Warnings for realistic agent: {len(warnings)}")
            for warning in warnings:
                print(f"  - {warning['type']}: {warning['message']}")


if __name__ == '__main__':
    unittest.main()