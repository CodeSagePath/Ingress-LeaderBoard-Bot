"""
Business Rules Validator for Ingress Prime statistics.

This module validates logical relationships and business rules
between different statistics to ensure data integrity.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date

from ..config.stats_config import get_stat_by_idx

logger = logging.getLogger(__name__)


class BusinessRulesValidator:
    """Validates business rules and logical relationships between stats."""

    def __init__(self):
        # AP thresholds for level validation (minimum AP expected for each level)
        self.level_ap_thresholds = {
            1: 0,
            2: 10000,
            3: 30000,
            4: 70000,
            5: 150000,
            6: 300000,
            7: 600000,
            8: 1200000,
            9: 2500000,
            10: 4000000,
            11: 6000000,
            12: 8400000,
            13: 12000000,
            14: 17000000,
            15: 24000000,
            16: 40000000
        }

    def validate_business_rules(self, parsed_data: Dict) -> List[Dict]:
        """
        Validate all business rules for parsed stats data.

        Args:
            parsed_data: Dictionary containing parsed stats

        Returns:
            List of business rule validation warnings
        """
        warnings = []

        # AP Consistency: Current AP should not exceed Lifetime AP
        ap_warnings = self._validate_ap_consistency(parsed_data)
        warnings.extend(ap_warnings)

        # Level Progression: Level should match expected AP ranges
        level_warnings = self._validate_level_progression(parsed_data)
        warnings.extend(level_warnings)

        # Cross-stat dependencies: Logical relationships between different stats
        dependency_warnings = self._validate_stat_dependencies(parsed_data)
        warnings.extend(dependency_warnings)

        # Temporal consistency: Check for logical temporal relationships
        temporal_warnings = self._validate_temporal_consistency(parsed_data)
        warnings.extend(temporal_warnings)

        return warnings

    def _validate_ap_consistency(self, parsed_data: Dict) -> List[Dict]:
        """
        Validate AP consistency between Current AP and Lifetime AP.

        Args:
            parsed_data: Parsed stats dictionary

        Returns:
            List of AP consistency warnings
        """
        warnings = []

        # Get AP stats
        current_ap_stat = parsed_data.get(7)  # Current AP
        lifetime_ap_stat = parsed_data.get(6)  # Lifetime AP

        if current_ap_stat and lifetime_ap_stat:
            try:
                current_ap = int(current_ap_stat.get('value', 0))
                lifetime_ap = int(lifetime_ap_stat.get('value', 0))

                # Current AP should not exceed Lifetime AP
                if current_ap > lifetime_ap:
                    warnings.append({
                        'type': 'ap_inconsistency',
                        'message': f"Current AP ({current_ap:,}) exceeds Lifetime AP ({lifetime_ap:,})",
                        'stat_name': 'AP Consistency',
                        'current_ap': current_ap,
                        'lifetime_ap': lifetime_ap,
                        'severity': 'error'
                    })

                # Current AP should be reasonably close to Lifetime AP (within 20% for active players)
                elif lifetime_ap > 5000000 and current_ap < lifetime_ap * 0.8:
                    warnings.append({
                        'type': 'low_current_ap',
                        'message': f"Current AP is unusually low compared to Lifetime AP. Current: {current_ap:,}, Lifetime: {lifetime_ap:,}",
                        'stat_name': 'AP Consistency',
                        'current_ap': current_ap,
                        'lifetime_ap': lifetime_ap,
                        'severity': 'warning'
                    })

            except ValueError:
                warnings.append({
                    'type': 'invalid_ap_format',
                    'message': f"Invalid AP format: Current='{current_ap_stat.get('value')}', Lifetime='{lifetime_ap_stat.get('value')}'",
                    'stat_name': 'AP Consistency',
                    'severity': 'error'
                })

        return warnings

    def _validate_level_progression(self, parsed_data: Dict) -> List[Dict]:
        """
        Validate that level matches expected AP ranges.

        Args:
            parsed_data: Parsed stats dictionary

        Returns:
            List of level progression warnings
        """
        warnings = []

        # Get level and lifetime AP stats
        level_stat = parsed_data.get(5)  # Level
        lifetime_ap_stat = parsed_data.get(6)  # Lifetime AP

        if level_stat and lifetime_ap_stat:
            try:
                level = int(level_stat.get('value', 0))
                lifetime_ap = int(lifetime_ap_stat.get('value', 0))

                # Validate level is within expected range
                if level < 1 or level > 16:
                    warnings.append({
                        'type': 'invalid_level',
                        'message': f"Invalid level: {level}. Valid range is 1-16",
                        'stat_name': 'Level',
                        'level': level,
                        'severity': 'error'
                    })
                else:
                    # Check if AP matches expected range for this level
                    expected_min_ap = self.level_ap_thresholds.get(level, 0)
                    max_level_ap = max(self.level_ap_thresholds.values()) if level == 16 else self.level_ap_thresholds.get(level + 1, float('inf'))

                    if lifetime_ap < expected_min_ap:
                        warnings.append({
                            'type': 'insufficient_ap_for_level',
                            'message': f"Level {level} typically requires at least {expected_min_ap:,} AP, but you show {lifetime_ap:,}",
                            'stat_name': 'Level Progression',
                            'level': level,
                            'expected_ap': expected_min_ap,
                            'actual_ap': lifetime_ap,
                            'severity': 'warning'
                        })

                    # Check if AP is unusually high for the level (suggesting missed level ups)
                    elif level < 16 and lifetime_ap > max_level_ap * 1.5:  # 50% above next level threshold
                        warnings.append({
                            'type': 'excessive_ap_for_level',
                            'message': f"AP ({lifetime_ap:,}) is unusually high for level {level}. Consider leveling up!",
                            'stat_name': 'Level Progression',
                            'level': level,
                            'expected_max': max_level_ap,
                            'actual_ap': lifetime_ap,
                            'severity': 'info'
                        })

            except ValueError:
                warnings.append({
                    'type': 'invalid_level_format',
                    'message': f"Invalid level format: '{level_stat.get('value')}'",
                    'stat_name': 'Level Progression',
                    'severity': 'error'
                })

        return warnings

    def _validate_stat_dependencies(self, parsed_data: Dict) -> List[Dict]:
        """
        Validate logical dependencies between different statistics.

        Args:
            parsed_data: Parsed stats dictionary

        Returns:
            List of stat dependency warnings
        """
        warnings = []

        # Building dependencies
        building_warnings = self._validate_building_dependencies(parsed_data)
        warnings.extend(building_warnings)

        # Discovery dependencies
        discovery_warnings = self._validate_discovery_dependencies(parsed_data)
        warnings.extend(discovery_warnings)

        # Combat dependencies
        combat_warnings = self._validate_combat_dependencies(parsed_data)
        warnings.extend(combat_warnings)

        return warnings

    def _validate_building_dependencies(self, parsed_data: Dict) -> List[Dict]:
        """Validate logical relationships between building stats."""
        warnings = []

        resonators_deployed = self._get_stat_value(parsed_data, 14)  # Resonators Deployed
        links_created = self._get_stat_value(parsed_data, 15)  # Links Created
        control_fields = self._get_stat_value(parsed_data, 16)  # Control Fields Created
        mu_captured = self._get_stat_value(parsed_data, 17)  # MU Captured

        # Links should not be significantly higher than resonators deployed
        if (resonators_deployed is not None and links_created is not None and
            resonators_deployed > 0 and links_created > resonators_deployed * 2):
            warnings.append({
                'type': 'unusual_building_ratio',
                'message': f"Links created ({links_created:,}) is unusually high compared to resonators deployed ({resonators_deployed:,})",
                'stat_name': 'Building Dependencies',
                'resonators': resonators_deployed,
                'links': links_created,
                'severity': 'warning'
            })

        # Control fields should not exceed links created by too much
        if (links_created is not None and control_fields is not None and
            links_created > 0 and control_fields > links_created * 3):
            warnings.append({
                'type': 'unusual_field_ratio',
                'message': f"Control fields ({control_fields:,}) is unusually high compared to links created ({links_created:,})",
                'stat_name': 'Building Dependencies',
                'links': links_created,
                'fields': control_fields,
                'severity': 'warning'
            })

        # MU captured should correlate with control fields (rough baseline: average 5000 MU per field)
        if (control_fields is not None and mu_captured is not None and
            control_fields > 100 and mu_captured < control_fields * 1000):
            warnings.append({
                'type': 'low_mu_per_field',
                'message': f"MU captured ({mu_captured:,}) seems low for {control_fields:,} control fields created",
                'stat_name': 'Building Dependencies',
                'fields': control_fields,
                'mu': mu_captured,
                'severity': 'info'
            })

        return warnings

    def _validate_discovery_dependencies(self, parsed_data: Dict) -> List[Dict]:
        """Validate logical relationships between discovery stats."""
        warnings = []

        unique_portals = self._get_stat_value(parsed_data, 8)  # Unique Portals Visited
        xm_collected = self._get_stat_value(parsed_data, 11)  # XM Collected
        distance_walked = self._get_stat_value(parsed_data, 13)  # Distance Walked
        hacks = self._get_stat_value(parsed_data, 28)  # Hacks

        # Distance walked should correlate with unique portals (rough baseline: 0.5 km per unique portal)
        if (unique_portals is not None and distance_walked is not None and
            unique_portals > 100 and distance_walked < unique_portals * 0.3):
            warnings.append({
                'type': 'low_distance_for_portals',
                'message': f"Distance walked ({distance_walked:,} km) seems low for {unique_portals:,} unique portals visited",
                'stat_name': 'Discovery Dependencies',
                'portals': unique_portals,
                'distance': distance_walked,
                'severity': 'info'
            })

        # XM collected should correlate with hacks (rough baseline: 100 XM per hack)
        if (hacks is not None and xm_collected is not None and
            hacks > 1000 and xm_collected < hacks * 50):
            warnings.append({
                'type': 'low_xm_for_hacks',
                'message': f"XM collected ({xm_collected:,}) seems low for {hacks:,} total hacks",
                'stat_name': 'Discovery Dependencies',
                'hacks': hacks,
                'xm': xm_collected,
                'severity': 'info'
            })

        return warnings

    def _validate_combat_dependencies(self, parsed_data: Dict) -> List[Dict]:
        """Validate logical relationships between combat stats."""
        warnings = []

        resonators_destroyed = self._get_stat_value(parsed_data, 23)  # Resonators Destroyed
        portals_neutralized = self._get_stat_value(parsed_data, 24)  # Portals Neutralized
        links_destroyed = self._get_stat_value(parsed_data, 25)  # Enemy Links Destroyed

        # Portals neutralized should correlate with resonators destroyed
        if (resonators_destroyed is not None and portals_neutralized is not None and
            resonators_destroyed > 0 and portals_neutralized > resonators_destroyed * 4):
            warnings.append({
                'type': 'unusual_combat_ratio',
                'message': f"Portals neutralized ({portals_neutralized:,}) is unusually high compared to resonators destroyed ({resonators_destroyed:,})",
                'stat_name': 'Combat Dependencies',
                'resonators_destroyed': resonators_destroyed,
                'portals_neutralized': portals_neutralized,
                'severity': 'warning'
            })

        return warnings

    def _validate_temporal_consistency(self, parsed_data: Dict) -> List[Dict]:
        """
        Validate temporal consistency of the stats submission.

        Args:
            parsed_data: Parsed stats dictionary

        Returns:
            List of temporal consistency warnings
        """
        warnings = []

        # Check if stats date is reasonable (not too far in past or future)
        date_stat = parsed_data.get(3)  # Date
        if date_stat:
            try:
                stats_date = datetime.strptime(date_stat.get('value', ''), '%Y-%m-%d').date()
                today = date.today()

                # Future date check
                if stats_date > today:
                    days_future = (stats_date - today).days
                    warnings.append({
                        'type': 'future_date',
                        'message': f"Stats date is {days_future} days in future: {stats_date}",
                        'stat_name': 'Temporal Consistency',
                        'stats_date': str(stats_date),
                        'days_future': days_future,
                        'severity': 'error'
                    })

                # Very old date check (more than 2 years)
                elif (today - stats_date).days > 730:
                    days_old = (today - stats_date).days
                    warnings.append({
                        'type': 'very_old_date',
                        'message': f"Stats date is very old ({days_old} days ago): {stats_date}",
                        'stat_name': 'Temporal Consistency',
                        'stats_date': str(stats_date),
                        'days_old': days_old,
                        'severity': 'warning'
                    })

            except ValueError:
                warnings.append({
                    'type': 'invalid_date_format',
                    'message': f"Invalid date format: {date_stat.get('value')}",
                    'stat_name': 'Temporal Consistency',
                    'severity': 'error'
                })

        return warnings

    def _get_stat_value(self, parsed_data: Dict, stat_idx: int) -> Optional[int]:
        """
        Helper method to safely extract integer value from parsed stats.

        Args:
            parsed_data: Parsed stats dictionary
            stat_idx: Index of stat to extract

        Returns:
            Integer value or None if invalid/missing
        """
        stat = parsed_data.get(stat_idx)
        if not stat:
            return None

        try:
            return int(stat.get('value', 0))
        except (ValueError, TypeError):
            return None