"""
Test data generator for validation testing.

This module generates realistic and edge-case test data
for testing the enhanced validation system.
"""

import random
from datetime import date, timedelta


class TestDataGenerator:
    """Generates test data for validation testing."""

    def __init__(self):
        # Realistic stat ranges based on active players
        self.stat_ranges = {
            5: (1, 16),      # Level
            6: (10000, 50000000),  # Lifetime AP
            7: (0, 10000000),      # Current AP
            8: (100, 50000),       # Unique Portals Visited
            11: (50000, 100000000), # XM Collected
            13: (50, 10000),       # Distance Walked (km)
            14: (500, 500000),     # Resonators Deployed
            15: (200, 100000),     # Links Created
            16: (50, 50000),       # Control Fields Created
            17: (10000, 1000000000), # MU Captured
            23: (100, 100000),     # Resonators Destroyed
            24: (100, 50000),      # Portals Neutralized
            25: (50, 20000),       # Enemy Links Destroyed
            28: (1000, 100000),    # Hacks
        }

    def generate_valid_submission(self, agent_name=None, faction=None):
        """Generate a completely valid stats submission."""
        if agent_name is None:
            agent_name = f"TestAgent{random.randint(1000, 9999)}"

        if faction is None:
            faction = random.choice(['Enlightened', 'Resistance'])

        # Generate level and AP consistently
        level = random.randint(5, 15)
        lifetime_ap = self._generate_ap_for_level(level, high_end=True)
        current_ap = random.randint(lifetime_ap // 3, lifetime_ap)

        # Generate other stats based on level and play style
        base_activity = level * random.randint(100, 500)

        return {
            # Required fields
            1: {'idx': 1, 'name': 'Agent Name', 'value': agent_name, 'type': 'S'},
            2: {'idx': 2, 'name': 'Agent Faction', 'value': faction, 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': self._generate_recent_date(), 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': self._generate_random_time(), 'type': 'S'},

            # Main stats with consistent relationships
            5: {'idx': 5, 'name': 'Level', 'value': str(level), 'type': 'N'},
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': str(lifetime_ap), 'type': 'N'},
            7: {'idx': 7, 'name': 'Current AP', 'value': str(current_ap), 'type': 'N'},

            # Discovery stats
            8: {'idx': 8, 'name': 'Unique Portals Visited', 'value': str(base_activity * 2), 'type': 'N'},
            9: {'idx': 9, 'name': 'Portals Discovered', 'value': str(int(base_activity * 2.1)), 'type': 'N'},
            11: {'idx': 11, 'name': 'XM Collected', 'value': str(base_activity * 20), 'type': 'N'},
            13: {'idx': 13, 'name': 'Distance Walked', 'value': str(int(base_activity * 0.8)), 'type': 'N'},

            # Building stats
            14: {'idx': 14, 'name': 'Resonators Deployed', 'value': str(base_activity * 8), 'type': 'N'},
            15: {'idx': 15, 'name': 'Links Created', 'value': str(base_activity * 3), 'type': 'N'},
            16: {'idx': 16, 'name': 'Control Fields Created', 'value': str(base_activity), 'type': 'N'},
            17: {'idx': 17, 'name': 'MU Captured', 'value': str(base_activity * 10000), 'type': 'N'},
            18: {'idx': 18, 'name': 'Mods Deployed', 'value': str(base_activity // 2), 'type': 'N'},

            # Combat stats
            23: {'idx': 23, 'name': 'Resonators Destroyed', 'value': str(base_activity * 2), 'type': 'N'},
            24: {'idx': 24, 'name': 'Portals Neutralized', 'value': str(int(base_activity * 1.5)), 'type': 'N'},
            25: {'idx': 25, 'name': 'Enemy Links Destroyed', 'value': str(base_activity), 'type': 'N'},
            26: {'idx': 26, 'name': 'Enemy Control Fields Destroyed', 'value': str(base_activity // 2), 'type': 'N'},
            27: {'idx': 27, 'name': 'XM Collected by Enemy', 'value': str(base_activity * 15), 'type': 'N'},

            # Other stats
            10: {'idx': 10, 'name': 'Drone Hacks', 'value': str(base_activity // 10), 'type': 'N'},
            12: {'idx': 12, 'name': 'Keys Hacked', 'value': str(base_activity * 4), 'type': 'N'},
            19: {'idx': 19, 'name': 'Unique Missions Completed', 'value': str(base_activity // 5), 'type': 'N'},
            20: {'idx': 20, 'name': 'XM Recharged', 'value': str(base_activity * 18), 'type': 'N'},
            21: {'idx': 21, 'name': 'Portals Captured', 'value': str(int(base_activity * 1.2)), 'type': 'N'},
            22: {'idx': 22, 'name': 'Max Times Hacked', 'value': str(random.randint(8, 50)), 'type': 'N'},
            28: {'idx': 28, 'name': 'Hacks', 'value': str(base_activity * 10), 'type': 'N'},
            29: {'idx': 29, 'name': 'Max Link Length', 'value': f"{random.uniform(1, 20):.1f}", 'type': 'N'},
            30: {'idx': 30, 'name': 'Max Time Portal Held', 'value': str(random.randint(1, 90)), 'type': 'N'},
            31: {'idx': 31, 'name': 'Max Time Field Held', 'value': str(random.randint(1, 30)), 'type': 'N'},
            32: {'idx': 32, 'name': 'Longest Link', 'value': f"{random.uniform(1, 25):.1f}", 'type': 'N'},
            33: {'idx': 33, 'name': 'Largest Field', 'value': str(random.randint(1000, 50000)), 'type': 'N'},
        }

    def generate_submission_with_ap_inconsistency(self):
        """Generate submission with Current AP > Lifetime AP."""
        data = self.generate_valid_submission()
        data[6]['value'] = '10000000'  # Lifetime AP
        data[7]['value'] = '15000000'  # Current AP exceeds lifetime
        return data

    def generate_submission_with_level_mismatch(self):
        """Generate submission with level that doesn't match AP."""
        data = self.generate_valid_submission()
        data[5]['value'] = '15'       # High level
        data[6]['value'] = '2000000'   # Low AP for level 15
        return data

    def generate_submission_with_unusual_ratios(self):
        """Generate submission with unusual stat ratios."""
        data = self.generate_valid_submission()
        data[14]['value'] = '1000'     # Low resonators
        data[15]['value'] = '10000'    # Very high links (10x ratio)
        return data

    def generate_submission_with_future_date(self):
        """Generate submission with future date."""
        data = self.generate_valid_submission()
        future_date = date.today() + timedelta(days=5)
        data[3]['value'] = future_date.strftime('%Y-%m-%d')
        return data

    def generate_submission_with_invalid_format(self):
        """Generate submission with invalid data formats."""
        data = self.generate_valid_submission()
        data[6]['value'] = 'not_a_number'  # Invalid AP format
        data[7]['value'] = 'also_not_a_number'  # Invalid current AP
        return data

    def generate_submission_with_missing_fields(self):
        """Generate submission with missing required fields."""
        data = self.generate_valid_submission()
        # Remove critical required field
        del data[1]  # Remove Agent Name
        return data

    def generate_submission_with_insufficient_stats(self):
        """Generate submission with too few stats."""
        return {
            1: {'idx': 1, 'name': 'Agent Name', 'value': 'MinimalAgent', 'type': 'S'},
            2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Enlightened', 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': '2024-01-15', 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': '10:30:00', 'type': 'S'},
            # Only 4 stats, below minimum of 12
        }

    def generate_edge_case_submissions(self):
        """Generate various edge case submissions."""
        edge_cases = []

        # Maximum values
        edge_cases.append(self._generate_max_values_submission())

        # Minimum values
        edge_cases.append(self._generate_min_values_submission())

        # New player (level 1)
        edge_cases.append(self._generate_new_player_submission())

        # Very experienced player (level 16)
        edge_cases.append(self._generate_experienced_player_submission())

        # Mixed anomalies
        edge_cases.append(self.generate_submission_with_ap_inconsistency())
        edge_cases.append(self.generate_submission_with_level_mismatch())
        edge_cases.append(self.generate_submission_with_unusual_ratios())
        edge_cases.append(self.generate_submission_with_future_date())

        return edge_cases

    def _generate_ap_for_level(self, level, high_end=False):
        """Generate realistic AP for a given level."""
        # AP thresholds for each level (minimum expected)
        level_thresholds = {
            1: 0, 2: 10000, 3: 30000, 4: 70000, 5: 150000,
            6: 300000, 7: 600000, 8: 1200000, 9: 2500000,
            10: 4000000, 11: 6000000, 12: 8400000, 13: 12000000,
            14: 17000000, 15: 24000000, 16: 40000000
        }

        base_ap = level_thresholds.get(level, 0)

        if high_end:
            # Generate AP near next level threshold or well into current level
            if level < 16:
                next_threshold = level_thresholds.get(level + 1, float('inf'))
                return random.randint(int(base_ap * 1.1), int(next_threshold * 0.8))
            else:
                return random.randint(base_ap, base_ap * 2)
        else:
            # Generate AP just above minimum for level
            return random.randint(base_ap, int(base_ap * 1.3))

    def _generate_recent_date(self):
        """Generate a recent date within last 30 days."""
        days_ago = random.randint(0, 30)
        return (date.today() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

    def _generate_random_time(self):
        """Generate a random time."""
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        return f"{hour:02d}:{minute:02d}:{second:02d}"

    def _generate_max_values_submission(self):
        """Generate submission with maximum realistic values."""
        return {
            1: {'idx': 1, 'name': 'Agent Name', 'value': 'MaxPlayer', 'type': 'S'},
            2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Enlightened', 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': self._generate_recent_date(), 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': self._generate_random_time(), 'type': 'S'},
            5: {'idx': 5, 'name': 'Level', 'value': '16', 'type': 'N'},
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '160000000', 'type': 'N'},
            7: {'idx': 7, 'name': 'Current AP', 'value': '1000000', 'type': 'N'},
            8: {'idx': 8, 'name': 'Unique Portals Visited', 'value': '100000', 'type': 'N'},
            11: {'idx': 11, 'name': 'XM Collected', 'value': '200000000', 'type': 'N'},
            13: {'idx': 13, 'name': 'Distance Walked', 'value': '25000', 'type': 'N'},
            14: {'idx': 14, 'name': 'Resonators Deployed', 'value': '1000000', 'type': 'N'},
            15: {'idx': 15, 'name': 'Links Created', 'value': '200000', 'type': 'N'},
            16: {'idx': 16, 'name': 'Control Fields Created', 'value': '100000', 'type': 'N'},
            17: {'idx': 17, 'name': 'MU Captured', 'value': '1000000000', 'type': 'N'},
        }

    def _generate_min_values_submission(self):
        """Generate submission with minimum realistic values."""
        return {
            1: {'idx': 1, 'name': 'Agent Name', 'value': 'MinPlayer', 'type': 'S'},
            2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Resistance', 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': self._generate_recent_date(), 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': self._generate_random_time(), 'type': 'S'},
            5: {'idx': 5, 'name': 'Level', 'value': '1', 'type': 'N'},
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '5000', 'type': 'N'},
            7: {'idx': 7, 'name': 'Current AP', 'value': '2000', 'type': 'N'},
            8: {'idx': 8, 'name': 'Unique Portals Visited', 'value': '50', 'type': 'N'},
            11: {'idx': 11, 'name': 'XM Collected', 'value': '10000', 'type': 'N'},
            13: {'idx': 13, 'name': 'Distance Walked', 'value': '20', 'type': 'N'},
            14: {'idx': 14, 'name': 'Resonators Deployed', 'value': '200', 'type': 'N'},
            15: {'idx': 15, 'name': 'Links Created', 'value': '50', 'type': 'N'},
            16: {'idx': 16, 'name': 'Control Fields Created', 'value': '10', 'type': 'N'},
            17: {'idx': 17, 'name': 'MU Captured', 'value': '10000', 'type': 'N'},
        }

    def _generate_new_player_submission(self):
        """Generate submission for a new player (level 1-3)."""
        return {
            1: {'idx': 1, 'name': 'Agent Name', 'value': 'NewPlayer123', 'type': 'S'},
            2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Enlightened', 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': self._generate_recent_date(), 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': self._generate_random_time(), 'type': 'S'},
            5: {'idx': 5, 'name': 'Level', 'value': '2', 'type': 'N'},
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '25000', 'type': 'N'},
            7: {'idx': 7, 'name': 'Current AP', 'value': '15000', 'type': 'N'},
            8: {'idx': 8, 'name': 'Unique Portals Visited', 'value': '150', 'type': 'N'},
            11: {'idx': 11, 'name': 'XM Collected', 'value': '50000', 'type': 'N'},
            13: {'idx': 13, 'name': 'Distance Walked', 'value': '75', 'type': 'N'},
            14: {'idx': 14, 'name': 'Resonators Deployed', 'value': '300', 'type': 'N'},
            15: {'idx': 15, 'name': 'Links Created', 'value': '100', 'type': 'N'},
            16: {'idx': 16, 'name': 'Control Fields Created', 'value': '25', 'type': 'N'},
            17: {'idx': 17, 'name': 'MU Captured', 'value': '50000', 'type': 'N'},
        }

    def _generate_experienced_player_submission(self):
        """Generate submission for an experienced player (level 14-16)."""
        return {
            1: {'idx': 1, 'name': 'Agent Name', 'value': 'VeteranAgent', 'type': 'S'},
            2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Resistance', 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': self._generate_recent_date(), 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': self._generate_random_time(), 'type': 'S'},
            5: {'idx': 5, 'name': 'Level', 'value': '15', 'type': 'N'},
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '80000000', 'type': 'N'},
            7: {'idx': 7, 'name': 'Current AP', 'value': '5000000', 'type': 'N'},
            8: {'idx': 8, 'name': 'Unique Portals Visited', 'value': '50000', 'type': 'N'},
            11: {'idx': 11, 'name': 'XM Collected', 'value': '150000000', 'type': 'N'},
            13: {'idx': 13, 'name': 'Distance Walked', 'value': '15000', 'type': 'N'},
            14: {'idx': 14, 'name': 'Resonators Deployed', 'value': '500000', 'type': 'N'},
            15: {'idx': 15, 'name': 'Links Created', 'value': '75000', 'type': 'N'},
            16: {'idx': 16, 'name': 'Control Fields Created', 'value': '25000', 'type': 'N'},
            17: {'idx': 17, 'name': 'MU Captured', 'value': '500000000', 'type': 'N'},
        }

    def generate_test_suite_data(self):
        """Generate a complete test suite data set."""
        test_data = []

        # Add valid submissions
        for i in range(5):
            test_data.append({
                'name': f'Valid Submission {i+1}',
                'data': self.generate_valid_submission(),
                'expected_valid': True,
                'description': 'Completely valid submission with no issues'
            })

        # Add submissions with specific issues
        test_data.extend([
            {
                'name': 'AP Inconsistency',
                'data': self.generate_submission_with_ap_inconsistency(),
                'expected_valid': True,  # Should be valid but with warnings
                'expected_warnings': ['ap_inconsistency'],
                'description': 'Current AP exceeds Lifetime AP'
            },
            {
                'name': 'Level Mismatch',
                'data': self.generate_submission_with_level_mismatch(),
                'expected_valid': True,  # Should be valid but with warnings
                'expected_warnings': ['insufficient_ap_for_level'],
                'description': 'Level too high for Lifetime AP'
            },
            {
                'name': 'Future Date',
                'data': self.generate_submission_with_future_date(),
                'expected_valid': True,  # Should be valid but with warnings
                'expected_warnings': ['future_date'],
                'description': 'Stats submission date is in the future'
            },
            {
                'name': 'Missing Required Fields',
                'data': self.generate_submission_with_missing_fields(),
                'expected_valid': False,
                'expected_errors': ['missing_required'],
                'description': 'Missing required agent name field'
            },
            {
                'name': 'Insufficient Stats Count',
                'data': self.generate_submission_with_insufficient_stats(),
                'expected_valid': False,
                'expected_errors': ['insufficient_stats'],
                'description': 'Not enough statistics provided'
            },
            {
                'name': 'Invalid Format',
                'data': self.generate_submission_with_invalid_format(),
                'expected_valid': True,  # Should be valid but with warnings
                'expected_warnings': ['invalid_numeric'],
                'description': 'Non-numeric values for numeric stats'
            },
            {
                'name': 'Unusual Ratios',
                'data': self.generate_submission_with_unusual_ratios(),
                'expected_valid': True,  # Should be valid but with warnings
                'expected_warnings': ['unusual_building_ratio'],
                'description': 'Unusual ratios between building stats'
            }
        ])

        # Add edge cases
        edge_cases = self.generate_edge_case_submissions()
        for i, case_data in enumerate(edge_cases):
            test_data.append({
                'name': f'Edge Case {i+1}',
                'data': case_data,
                'expected_valid': True,  # Most edge cases should be valid
                'description': f'Edge case: {case_data.get(5, {}).get("value", "unknown")}'
            })

        return test_data

    def export_test_data(self, filename='test_validation_data.py'):
        """Export generated test data to a Python file."""
        test_data = self.generate_test_suite_data()

        with open(filename, 'w') as f:
            f.write('"""')
            f.write('# Auto-generated test data for validation testing\\n')
            f.write('\\n')
            f.write('VALIDATION_TEST_DATA = [\\n')

            for test_case in test_data:
                f.write('    {\\n')
                f.write(f'        "name": "{test_case["name"]}",\\n')
                f.write(f'        "description": "{test_case["description"]}",\\n')
                f.write(f'        "expected_valid": {test_case["expected_valid"]},\\n')
                if 'expected_warnings' in test_case:
                    f.write(f'        "expected_warnings": {test_case["expected_warnings"]},\\n')
                if 'expected_errors' in test_case:
                    f.write(f'        "expected_errors": {test_case["expected_errors"]},\\n')
                f.write(f'        "data": {test_case["data"]},\\n')
                f.write('    },\\n')

            f.write(']\\n')
            f.write('"""')

        print(f"Test data exported to {filename}")


if __name__ == '__main__':
    generator = TestDataGenerator()
    generator.export_test_data()