"""
Validator for parsed Ingress Prime statistics.

This module validates parsed stats data for completeness, correctness,
and consistency.
"""

import logging
from typing import Dict, List, Tuple, Any
from datetime import datetime, date, time

from ..config.stats_config import get_stat_by_idx, get_badge_level
from .business_rules_validator import BusinessRulesValidator


logger = logging.getLogger(__name__)


class StatsValidator:
    """Validator for Ingress Prime statistics data."""

    def __init__(self):
        self.minimum_stats_count = 12
        self.required_indices = [1, 2, 3, 4]  # agent name, faction, date, time
        self.business_rules_validator = BusinessRulesValidator()

    def validate_parsed_stats(self, parsed_data: Dict) -> Tuple[bool, List[Dict]]:
        """
        Validate parsed stats data comprehensively.

        Args:
            parsed_data: Dictionary containing parsed stats

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []

        # Check for errors in parsed data
        if 'error' in parsed_data:
            return False, [{'type': 'parse_error', 'message': parsed_data['error']}]

        # Validate stats count
        count_warnings = self._validate_stats_count(parsed_data)
        warnings.extend(count_warnings)

        # Validate required fields
        required_warnings = self._validate_required_fields(parsed_data)
        if required_warnings:
            return False, required_warnings

        # **NEW: Enhanced business rules validation**
        business_warnings = self.business_rules_validator.validate_business_rules(parsed_data)
        warnings.extend(business_warnings)

        # Validate numeric values
        numeric_warnings = self._validate_numeric_values(parsed_data)
        warnings.extend(numeric_warnings)

        # Validate dates and times
        datetime_warnings = self._validate_datetime(parsed_data)
        warnings.extend(datetime_warnings)

        # Validate agent data
        agent_warnings = self._validate_agent_data(parsed_data)
        if agent_warnings:
            return False, agent_warnings

        # Validate faction consistency
        faction_warnings = self._validate_faction(parsed_data)
        warnings.extend(faction_warnings)

        # Check for unknown stats
        unknown_warnings = self._check_unknown_stats(parsed_data)
        warnings.extend(unknown_warnings)

        # Validate badge levels
        badge_warnings = self._validate_badge_levels(parsed_data)
        warnings.extend(badge_warnings)

        return True, warnings

    def _validate_stats_count(self, parsed_data: Dict) -> List[Dict]:
        """
        Validate minimum stats count.

        Args:
            parsed_data: Parsed stats dictionary

        Returns:
            List of warnings about stats count
        """
        warnings = []

        # Count actual stats
        stats_count = 0
        for key, value in parsed_data.items():
            if isinstance(key, int) or key.startswith('unknown_'):
                stats_count += 1

        if stats_count < self.minimum_stats_count:
            warnings.append({
                'type': 'insufficient_stats',
                'message': f'Only {stats_count} stats found, minimum {self.minimum_stats_count} required',
                'severity': 'error'
            })

        return warnings

    def _validate_required_fields(self, parsed_data: Dict) -> List[Dict]:
        """
        Validate required agent fields are present.

        Args:
            parsed_data: Parsed stats dictionary

        Returns:
            List of warnings about missing fields
        """
        warnings = []

        # Check required indices
        for idx in self.required_indices:
            if idx not in parsed_data:
                stat_name = self._get_stat_name(idx)
                warnings.append({
                    'type': 'missing_required',
                    'message': f'Missing required field: {stat_name} (index {idx})',
                    'severity': 'error',
                    'field': stat_name,
                    'index': idx
                })

        return warnings

    def _validate_numeric_values(self, parsed_data: Dict) -> List[Dict]:
        """
        Validate numeric stat values.

        Args:
            parsed_data: Parsed stats dictionary

        Returns:
            List of warnings about invalid numeric values
        """
        warnings = []

        for key, stat in parsed_data.items():
            if not isinstance(key, int):
                continue

            stat_type = stat.get('type', 'N')
            if stat_type != 'N':
                continue

            value_str = stat.get('value', '')
            try:
                value = int(value_str)

                # Check for negative values where inappropriate
                if value < 0 and not self._allow_negative(key):
                    warnings.append({
                        'type': 'negative_value',
                        'message': f'Negative value for {stat.get("name", "Unknown")}: {value}',
                        'stat_name': stat.get('name', 'Unknown'),
                        'stat_idx': key,
                        'value': value
                    })

                # Check for unreasonably large values
                if value > self._get_max_reasonable(key):
                    warnings.append({
                        'type': 'unreasonable_value',
                        'message': f'Unreasonably large value for {stat.get("name", "Unknown")}: {value:,}',
                        'stat_name': stat.get('name', 'Unknown'),
                        'stat_idx': key,
                        'value': value,
                        'severity': 'warning'
                    })

            except ValueError:
                warnings.append({
                    'type': 'invalid_numeric',
                    'message': f'Invalid numeric value for {stat.get("name", "Unknown")}: "{value_str}"',
                    'stat_name': stat.get('name', 'Unknown'),
                    'stat_idx': key,
                    'value': value_str,
                    'severity': 'error'
                })

        return warnings

    def _validate_datetime(self, parsed_data: Dict) -> List[Dict]:
        """
        Validate date and time fields.

        Args:
            parsed_data: Parsed stats dictionary

        Returns:
            List of warnings about date/time issues
        """
        warnings = []

        # Validate date (index 3)
        if 3 in parsed_data:
            date_str = parsed_data[3].get('value', '')
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                # Check if date is in future
                if parsed_date > date.today():
                    warnings.append({
                        'type': 'future_date',
                        'message': f'Date is in future: {date_str}',
                        'date': date_str,
                        'severity': 'warning'
                    })

                # Check if date is very old
                days_old = (date.today() - parsed_date).days
                if days_old > 365:
                    warnings.append({
                        'type': 'old_date',
                        'message': f'Date is very old ({days_old} days): {date_str}',
                        'date': date_str,
                        'days_old': days_old,
                        'severity': 'warning'
                    })

            except ValueError:
                warnings.append({
                    'type': 'invalid_date_format',
                    'message': f'Invalid date format: {date_str} (expected YYYY-MM-DD)',
                    'date': date_str,
                    'severity': 'error'
                })

        # Validate time (index 4)
        if 4 in parsed_data:
            time_str = parsed_data[4].get('value', '')
            try:
                datetime.strptime(time_str, '%H:%M:%S').time()
            except ValueError:
                warnings.append({
                    'type': 'invalid_time_format',
                    'message': f'Invalid time format: {time_str} (expected HH:MM:SS)',
                    'time': time_str,
                    'severity': 'error'
                })

        return warnings

    def _validate_agent_data(self, parsed_data: Dict) -> List[Dict]:
        """
        Validate agent name and faction.

        Args:
            parsed_data: Parsed stats dictionary

        Returns:
            List of warnings about agent data issues
        """
        warnings = []

        # Validate agent name (index 1)
        if 1 in parsed_data:
            agent_name = parsed_data[1].get('value', '').strip()
            if not agent_name:
                warnings.append({
                    'type': 'empty_agent_name',
                    'message': 'Agent name is empty',
                    'severity': 'error'
                })
            elif len(agent_name) > 64:
                warnings.append({
                    'type': 'long_agent_name',
                    'message': f'Agent name is very long: {len(agent_name)} characters',
                    'agent_name': agent_name,
                    'severity': 'warning'
                })

        # Validate faction (index 2)
        if 2 in parsed_data:
            faction = parsed_data[2].get('value', '').strip()
            valid_factions = ['Enlightened', 'Resistance']
            if faction not in valid_factions:
                warnings.append({
                    'type': 'invalid_faction',
                    'message': f'Invalid faction: {faction}',
                    'faction': faction,
                    'severity': 'error'
                })

        return warnings

    def _validate_faction(self, parsed_data: Dict) -> List[Dict]:
        """
        Validate faction consistency and check for issues.

        Args:
            parsed_data: Parsed stats dictionary

        Returns:
            List of warnings about faction issues
        """
        warnings = []

        if 2 in parsed_data:
            faction = parsed_data[2].get('value', '').strip()
            if faction:
                # Check for common typos
                typo_corrections = {
                    'Enlightened': 'Enlightened',
                    'Enlightened': 'Enlightened',
                    'Resistance': 'Resistance',
                    'Resistance': 'Resistance'
                }

                if faction in typo_corrections and faction != typo_corrections[faction]:
                    warnings.append({
                        'type': 'faction_typo',
                        'message': f'Faction typo detected: {faction} -> {typo_corrections[faction]}',
                        'original': faction,
                        'corrected': typo_corrections[faction],
                        'severity': 'warning'
                    })

        return warnings

    def _check_unknown_stats(self, parsed_data: Dict) -> List[Dict]:
        """
        Check for unknown stats that couldn't be matched.

        Args:
            parsed_data: Parsed stats dictionary

        Returns:
            List of warnings about unknown stats
        """
        warnings = []

        unknown_count = 0
        for key, stat in parsed_data.items():
            if isinstance(key, str) and key.startswith('unknown_') and isinstance(stat, dict):
                unknown_count += 1
                warnings.append({
                    'type': 'unknown_stat',
                    'message': f'Unknown stat: {stat.get("name", "Unknown")}',
                    'stat_name': stat.get('name', 'Unknown'),
                    'value': stat.get('value', ''),
                    'original_pos': stat.get('original_pos', -1)
                })

        if unknown_count > 5:
            warnings.append({
                'type': 'many_unknown_stats',
                'message': f'Many unknown stats found ({unknown_count}), format may be incorrect',
                'count': unknown_count,
                'severity': 'warning'
            })

        return warnings

    def _validate_badge_levels(self, parsed_data: Dict) -> List[Dict]:
        """
        Validate badge levels for stats that have them.

        Args:
            parsed_data: Parsed stats dictionary

        Returns:
            List of warnings about badge levels
        """
        warnings = []

        for key, stat in parsed_data.items():
            if not isinstance(key, int):
                continue

            try:
                value = int(stat.get('value', 0))
                badge_level, next_level = get_badge_level(key, value)

                if badge_level:
                    # Check if close to next badge level
                    if next_level and value > next_level * 0.9:
                        warnings.append({
                            'type': 'near_next_badge',
                            'message': f'Close to next {stat.get("name", "Unknown")} badge level!',
                            'stat_name': stat.get('name', 'Unknown'),
                            'current_level': badge_level,
                            'next_level': next_level,
                            'current_value': value,
                            'severity': 'info'
                        })
            except (ValueError, TypeError):
                pass  # Skip if value can't be converted

        return warnings

    def _get_stat_name(self, idx: int) -> str:
        """
        Get stat name by index.

        Args:
            idx: Stat index

        Returns:
            Stat name or index as string if not found
        """
        stat = get_stat_by_idx(idx)
        return stat['name'] if stat else f'Index {idx}'

    def _allow_negative(self, stat_idx: int) -> bool:
        """
        Check if negative values are allowed for this stat.

        Args:
            stat_idx: Stat index

        Returns:
            True if negative values are allowed
        """
        # Generally, Ingress stats shouldn't be negative
        # This could be extended if there are specific cases
        return False

    def _get_max_reasonable(self, stat_idx: int) -> int:
        """
        Get maximum reasonable value for a stat to detect data entry errors.

        Args:
            stat_idx: Stat index

        Returns:
            Maximum reasonable value for the stat
        """
        # Set reasonable upper bounds for different stat types
        max_reasonable = {
            6: 10_000_000_000,  # Lifetime AP (10 billion is insane high)
            8: 1_000_000,        # Unique Portals Visited
            11: 1_000_000_000,   # XM Collected
            13: 100_000,          # Distance Walked (km)
            14: 10_000_000,       # Resonators Deployed
            15: 1_000_000,        # Links Created
            16: 500_000,          # Control Fields Created
            17: 100_000_000_000,  # MU Captured
        }

        return max_reasonable.get(stat_idx, 1_000_000_000)

    def get_validation_summary(self, parsed_data: Dict) -> Dict:
        """
        Get a summary of validation results.

        Args:
            parsed_data: Parsed stats dictionary

        Returns:
            Validation summary dictionary
        """
        is_valid, warnings = self.validate_parsed_stats(parsed_data)

        summary = {
            'is_valid': is_valid,
            'total_warnings': len(warnings),
            'error_count': len([w for w in warnings if w.get('severity') == 'error']),
            'warning_count': len([w for w in warnings if w.get('severity') == 'warning']),
            'info_count': len([w for w in warnings if w.get('severity') == 'info']),
            'warnings': warnings
        }

        # Categorize warnings by type
        warning_types = {}
        for warning in warnings:
            warning_type = warning.get('type', 'unknown')
            warning_types[warning_type] = warning_types.get(warning_type, 0) + 1

        summary['warning_types'] = warning_types

        return summary