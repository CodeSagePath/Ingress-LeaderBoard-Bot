"""
Stats parser for Ingress Prime statistics.

This module handles parsing of stats from both tab-separated and space-separated formats
that Ingress Prime provides when copying player statistics.
"""

import re
import time
from typing import Dict, List, Optional, Union, Tuple

from ..config.stats_config import STATS_DEFINITIONS, get_stat_by_idx, validate_faction


class StatsParser:
    """Parser for Ingress Prime statistics from Telegram messages."""

    def __init__(self):
        self.stats_definitions = STATS_DEFINITIONS
        self.minimum_stats_count = 12

    def parse(self, stats_text: str) -> Dict:
        """
        Main parsing entry point.

        Args:
            stats_text: Raw stats text from Ingress Prime

        Returns:
            Dictionary containing parsed stats or error information
        """
        try:
            # Clean and normalize input
            stats_text = self.clean_input(stats_text)

            # Validate that this looks like stats
            if not self.is_valid_stats(stats_text):
                return {'error': 'Invalid stats format', 'error_code': 1}

            # Detect format and parse accordingly
            if '\t' in stats_text:
                return self.parse_tabulated(stats_text)
            else:
                return self.parse_telegram(stats_text)

        except Exception as e:
            return {'error': f'Parsing error: {str(e)}', 'error_code': 99}

    def clean_input(self, text: str) -> str:
        """
        Clean up input text.

        Args:
            text: Raw input text

        Returns:
            Cleaned and normalized text
        """
        # Remove surrounding quotes
        text = text.strip('"\'')

        # Normalize multiple spaces to single spaces
        text = re.sub(r' {2,}', ' ', text)

        # Normalize multiple newlines to single newline
        text = re.sub(r'\n{2,}', '\n', text)

        # Trim whitespace
        text = text.strip()

        return text

    def is_valid_stats(self, text: str) -> bool:
        """
        Check if text starts with valid stats header.

        Args:
            text: Text to validate

        Returns:
            True if valid stats format, False otherwise
        """
        # Check for both tab-separated and space-separated headers
        headers = [
            'Time Span\tAgent Name\tAgent Faction\tDate',
            'Time Span Agent Name Agent Faction Date',
            'Time Span Agent Name Agent Faction'
        ]

        return any(text.startswith(header) for header in headers)

    def parse_tabulated(self, stats_text: str) -> Dict:
        """
        Parse tab-separated stats format.

        Args:
            stats_text: Tab-separated stats text

        Returns:
            Dictionary containing parsed stats
        """
        lines = stats_text.strip().split('\n')
        if len(lines) < 2:
            return {'error': 'Insufficient data lines', 'error_code': 2}

        header_line = lines[0]
        values_line = lines[1]

        # Split by tabs
        headers = header_line.split('\t')
        values = values_line.split('\t')

        # Validate basic structure
        if len(headers) < 5 or len(values) < 5:
            return {'error': 'Invalid tabulated format', 'error_code': 3}

        # Check for ALL TIME stats
        if values[0] != 'ALL TIME':
            return {'error': 'Not ALL TIME stats', 'error_code': 4}

        result = {
            'format': 'tabulated',
            'timezone': 'UTC',
            'timestamp': int(time.time()),
            'stats_count': len(headers)
        }

        # Parse each header/value pair
        for i, (header, value) in enumerate(zip(headers, values)):
            if not header.strip():
                continue

            # Try to find matching stat definition
            stat_def = self._find_stat_by_name(header.strip())
            if stat_def:
                result[stat_def['idx']] = {
                    'idx': stat_def['idx'],
                    'value': value.strip(),
                    'name': stat_def['name'],
                    'type': stat_def['type'],
                    'original_pos': i
                }
            else:
                # Store unknown stat
                result[f'unknown_{i}'] = {
                    'idx': -1,
                    'value': value.strip(),
                    'name': header.strip(),
                    'type': 'U',
                    'original_pos': i
                }

        # Validate required fields
        validation_result = self._validate_required_fields(result)
        if validation_result:
            return validation_result

        return result

    def parse_telegram(self, stats_text: str) -> Dict:
        """
        Parse space-separated stats format from Telegram.

        Args:
            stats_text: Space-separated stats text

        Returns:
            Dictionary containing parsed stats
        """
        lines = stats_text.strip().split('\n')
        if len(lines) < 2:
            return {'error': 'Insufficient data lines', 'error_code': 2}

        header_line = lines[0]
        values_line = lines[1]

        # Extract values from space-separated format
        values = self._split_telegram_values(values_line)

        if len(values) < 5:
            return {'error': 'Not enough values in stats line', 'error_code': 5}

        # Check for ALL TIME
        if values[0] != 'ALL TIME':
            return {'error': 'Not ALL TIME stats', 'error_code': 4}

        result = {
            'format': 'telegram',
            'timezone': 'UTC',
            'timestamp': int(time.time()),
            'stats_count': len(values)
        }

        # Parse headers and map to stat definitions
        headers = header_line.split(' ')

        # Find date position (may be multi-word)
        date_position = self._find_date_position(values)
        if date_position == -1:
            return {'error': 'Could not find date in stats', 'error_code': 6}

        # Consolidate time span if it spans multiple words
        values = self._consolidate_time_span(values, date_position)

        # Map headers to values
        header_idx = 0
        value_idx = 0

        while header_idx < len(headers) and value_idx < len(values):
            header = headers[header_idx].strip()
            if not header:
                header_idx += 1
                continue

            # Handle multi-word headers (like date format)
            if header == 'Date' and header_idx + 1 < len(headers):
                if headers[header_idx + 1] == '(yyyy-mm-dd)':
                    header = 'Date (yyyy-mm-dd)'
                    header_idx += 1
            elif header == 'Time' and header_idx + 1 < len(headers):
                if headers[header_idx + 1] == '(hh:mm:ss)':
                    header = 'Time (hh:mm:ss)'
                    header_idx += 1

            # Find matching stat definition
            stat_def = self._find_stat_by_name(header)
            if stat_def:
                result[stat_def['idx']] = {
                    'idx': stat_def['idx'],
                    'value': values[value_idx],
                    'name': stat_def['name'],
                    'type': stat_def['type'],
                    'original_pos': header_idx
                }
            else:
                # Store unknown stat
                result[f'unknown_{header_idx}'] = {
                    'idx': -1,
                    'value': values[value_idx],
                    'name': header,
                    'type': 'U',
                    'original_pos': header_idx
                }

            header_idx += 1
            value_idx += 1

        # Validate required fields
        validation_result = self._validate_required_fields(result)
        if validation_result:
            return validation_result

        return result

    def _split_telegram_values(self, values_line: str) -> List[str]:
        """
        Split Telegram format values line properly.

        Args:
            values_line: The values line from Telegram format

        Returns:
            List of properly split values
        """
        # Split by spaces, but handle quoted strings and special cases
        values = []
        current = ""
        in_quotes = False

        for char in values_line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ' ' and not in_quotes and current:
                values.append(current)
                current = ""
            elif char != ' ' or in_quotes:
                current += char

        # Add last value
        if current:
            values.append(current)

        return values

    def _find_date_position(self, values: List[str]) -> int:
        """
        Find the position of the date in values array.

        Args:
            values: List of values

        Returns:
            Index of date value, or -1 if not found
        """
        for i, value in enumerate(values):
            # Look for date format (yyyy-mm-dd)
            if re.match(r'\d{4}-\d{2}-\d{2}', value):
                return i
        return -1

    def _consolidate_time_span(self, values: List[str], date_position: int) -> List[str]:
        """
        Consolidate time span if it spans multiple words (should be 'ALL TIME').

        Args:
            values: List of values
            date_position: Position where date starts

        Returns:
            Consolidated values list
        """
        if date_position <= 1:
            return values

        # Consolidate everything before date into time span
        time_span = ' '.join(values[:date_position])
        return [time_span] + values[date_position:]

    def _find_stat_by_name(self, name: str) -> Optional[Dict]:
        """
        Find stat definition by name.

        Args:
            name: The stat name to search for

        Returns:
            Stat definition dictionary or None if not found
        """
        # Direct match first
        for stat_def in self.stats_definitions:
            if stat_def['name'] == name:
                return stat_def

        # Partial match (handles variations)
        name_lower = name.lower()
        for stat_def in self.stats_definitions:
            if name_lower in stat_def['name'].lower():
                return stat_def

        return None

    def _validate_required_fields(self, result: Dict) -> Optional[Dict]:
        """
        Validate that required fields are present and valid.

        Args:
            result: Parsed stats dictionary

        Returns:
            Error dictionary if validation fails, None otherwise
        """
        # Check for minimum stats count
        stats_count = sum(1 for k, v in result.items()
                         if isinstance(k, int) or k.startswith('unknown_'))
        if stats_count < self.minimum_stats_count:
            return {
                'error': f'Insufficient stats: {stats_count} < {self.minimum_stats_count}',
                'error_code': 7
            }

        # Validate required indices (agent name, faction, date, time)
        required_indices = [1, 2, 3, 4]  # agent name, faction, date, time
        for idx in required_indices:
            if idx not in result:
                return {
                    'error': f'Missing required stat index {idx}',
                    'error_code': 8
                }

        # Validate faction
        faction_stat = result.get(2, {})
        faction_value = faction_stat.get('value', '')
        if not validate_faction(faction_value):
            return {
                'error': f'Invalid faction: {faction_value}',
                'error_code': 9
            }

        # Validate numeric stats
        for key, stat in result.items():
            if isinstance(key, int) and stat.get('type') == 'N':
                try:
                    int(stat['value'])
                except ValueError:
                    return {
                        'error': f'Invalid numeric value for {stat.get("name", "unknown")}: {stat.get("value", "empty")}',
                        'error_code': 10
                    }

        return None

    def get_stat_summary(self, parsed_data: Dict) -> Dict:
        """
        Get summary statistics from parsed data.

        Args:
            parsed_data: Parsed stats dictionary

        Returns:
            Dictionary with summary information
        """
        if 'error' in parsed_data:
            return parsed_data

        summary = {
            'format': parsed_data.get('format', 'unknown'),
            'stats_count': parsed_data.get('stats_count', 0),
            'timestamp': parsed_data.get('timestamp', 0),
            'agent_name': None,
            'faction': None,
            'level': None,
            'lifetime_ap': None,
            'valid_numeric_stats': 0,
            'warnings': []
        }

        # Extract key information
        if 1 in parsed_data:  # Agent name
            summary['agent_name'] = parsed_data[1]['value']
        if 2 in parsed_data:  # Faction
            summary['faction'] = parsed_data[2]['value']
        if 5 in parsed_data:  # Level
            try:
                summary['level'] = int(parsed_data[5]['value'])
            except ValueError:
                summary['warnings'].append('Invalid level value')
        if 6 in parsed_data:  # Lifetime AP
            try:
                summary['lifetime_ap'] = int(parsed_data[6]['value'])
            except ValueError:
                summary['warnings'].append('Invalid lifetime AP value')

        # Count numeric stats
        for key, stat in parsed_data.items():
            if isinstance(key, int) and stat.get('type') == 'N':
                try:
                    int(stat['value'])
                    summary['valid_numeric_stats'] += 1
                except ValueError:
                    pass

        return summary