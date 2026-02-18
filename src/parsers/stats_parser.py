"""
Dynamic stats parser for Ingress Prime statistics.

DESIGN: Header-driven, not position-driven.
- Parses the header line to identify stats
- Uses alias + fuzzy matching for name resolution
- Handles 4 formats: tab-separated, space-separated, single-line, no-delimiter
- Stores unknown stats instead of rejecting them
"""

import re
import time
import logging
from typing import Dict, List, Optional, Tuple

from ..config.stats_config import (
    STATS_DEFINITIONS, REQUIRED_STAT_NAMES,
    resolve_stat_name, assign_dynamic_idx, infer_stat_type, validate_faction
)

logger = logging.getLogger(__name__)


class StatsParser:
    """Dynamic parser for Ingress Prime statistics from Telegram messages."""

    def __init__(self):
        self.minimum_stats_count = 6

    # ================================================================
    # PUBLIC API
    # ================================================================

    def parse(self, stats_text: str) -> Dict:
        """
        Main parsing entry point. Auto-detects format.

        Args:
            stats_text: Raw stats text from Ingress Prime

        Returns:
            Dictionary containing parsed stats or error information
        """
        try:
            text = self._clean_input(stats_text)

            if not self._looks_like_stats(text):
                return {'error': 'Invalid stats format', 'error_code': 1}

            # Split into header + values lines
            header_line, values_line = self._split_header_values(text)
            if not header_line or not values_line:
                return {'error': 'Could not separate headers from values', 'error_code': 2}

            # Detect delimiter and split
            headers = self._split_line(header_line)
            values = self._split_line(values_line)

            if len(headers) < 5 or len(values) < 5:
                return {
                    'error': f'Too few fields: {len(headers)} headers, {len(values)} values',
                    'error_code': 3
                }

            # Check for ALL TIME
            if values[0].upper() not in ('ALL TIME', 'ALLTIME', 'ALL'):
                # Try consolidating first two values
                if len(values) > 1 and (values[0] + ' ' + values[1]).upper() == 'ALL TIME':
                    values = [values[0] + ' ' + values[1]] + values[2:]
                else:
                    return {'error': 'Not ALL TIME stats', 'error_code': 4}

            # Header-driven parsing
            result = self._parse_header_driven(headers, values)
            return result

        except Exception as e:
            logger.error(f"Parsing error: {e}", exc_info=True)
            return {'error': f'Parsing error: {str(e)}', 'error_code': 99}

    def is_valid_stats(self, text: str) -> bool:
        """Check if text looks like Ingress stats."""
        return self._looks_like_stats(text)

    def get_stat_summary(self, parsed_data: Dict) -> Dict:
        """Get summary from parsed data."""
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
            'unknown_stats': [],
            'warnings': []
        }

        # Extract key fields
        for key, stat in parsed_data.items():
            if not isinstance(stat, dict) or 'canonical_name' not in stat:
                continue

            name = stat['canonical_name']
            val = stat.get('value', '')

            if name == 'Agent Name':
                summary['agent_name'] = val
            elif name == 'Agent Faction':
                summary['faction'] = val
            elif name == 'Level':
                try:
                    summary['level'] = int(val)
                except ValueError:
                    summary['warnings'].append({'message': f'Invalid level: {val}'})
            elif name == 'Lifetime AP':
                try:
                    summary['lifetime_ap'] = int(val.replace(',', ''))
                except ValueError:
                    summary['warnings'].append({'message': f'Invalid AP: {val}'})

            # Count numeric stats
            if stat.get('type') == 'N':
                try:
                    int(str(val).replace(',', ''))
                    summary['valid_numeric_stats'] += 1
                except ValueError:
                    pass

            # Track unknown stats
            if stat.get('is_unknown'):
                summary['unknown_stats'].append(stat['original_header'])

        if summary['unknown_stats']:
            logger.info(f"Unknown stats found: {summary['unknown_stats']}")

        return summary

    # ================================================================
    # FORMAT DETECTION & SPLITTING
    # ================================================================

    def _clean_input(self, text: str) -> str:
        """Clean and normalize input text."""
        text = text.strip('\'"')
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{2,}', '\n', text)
        return text.strip()

    def _looks_like_stats(self, text: str) -> bool:
        """Flexible detection: does this look like Ingress stats?"""
        text_upper = text.upper()
        has_time_span = 'TIME SPAN' in text_upper
        has_agent = 'AGENT NAME' in text_upper or 'AGENT FACTION' in text_upper
        has_all_time = 'ALL TIME' in text_upper
        return has_time_span and has_agent and has_all_time

    def _split_header_values(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Split text into header line and values line.
        
        Handles:
        - Two-line format (header\nvalues)
        - Single-line format (header...ALL TIME...values)
        - Tab-separated single line
        """
        lines = text.strip().split('\n')

        # Two or more lines — standard format
        if len(lines) >= 2:
            return lines[0].strip(), lines[1].strip()

        # Single line — split at 'ALL TIME'
        single = lines[0]
        
        # Try tab-based split first
        if '\t' in single:
            idx = single.find('\tALL TIME')
            if idx == -1:
                idx = single.upper().find('\tALL TIME')
            if idx != -1:
                return single[:idx].strip(), single[idx+1:].strip()

        # Space-based split at 'ALL TIME'
        idx = single.find('ALL TIME')
        if idx == -1:
            idx = single.upper().find('ALL TIME')
        if idx > 0:
            return single[:idx].strip(), single[idx:].strip()

        return None, None

    def _split_line(self, line: str) -> List[str]:
        """
        Split a line into fields.
        
        Auto-detects: tabs > smart space-splitting
        """
        # Tab-separated
        if '\t' in line:
            return [f.strip() for f in line.split('\t') if f.strip()]

        # Space-separated — use header-aware splitting
        return self._smart_split(line)

    def _smart_split(self, line: str) -> List[str]:
        """
        Smart split for space-separated stats.
        
        Value lines start with 'ALL TIME', header lines don't.
        """
        if re.match(r'ALL\s+TIME', line, re.IGNORECASE):
            return self._split_values_line(line)
        else:
            return self._split_header_line(line)

    def _split_header_line(self, line: str) -> List[str]:
        """
        Split a header line into stat names using known stat name matching.
        
        Strategy: Replace known stat names with tokens (longest first),
        then reassemble.
        """
        # Collect all known stat names (canonical + aliases)
        from ..config.stats_config import STAT_ALIASES
        
        all_names = [s['name'] for s in STATS_DEFINITIONS]
        all_names.extend(STAT_ALIASES.keys())
        # Sort by length descending — match longest first
        all_names = sorted(set(all_names), key=len, reverse=True)

        tokenized = line
        token_map = {}
        
        for i, name in enumerate(all_names):
            token = f"__STAT_{i}__"
            # Case-insensitive replacement
            pattern = re.escape(name)
            match = re.search(pattern, tokenized, re.IGNORECASE)
            if match:
                # Replace only first occurrence to preserve order
                tokenized = tokenized[:match.start()] + token + tokenized[match.end():]
                token_map[token] = match.group(0)  # preserve original case

        # Split remaining text
        parts = tokenized.split()
        
        # Reassemble tokens to stat names
        result = []
        for part in parts:
            if part.startswith('__STAT_') and part.endswith('__'):
                result.append(token_map.get(part, part))
            else:
                result.append(part)

        return result

    def _split_values_line(self, line: str) -> List[str]:
        """Split a values line by spaces, handling quoted strings."""
        values = []
        current = ""

        for char in line:
            if char == '"':
                continue  # skip quotes
            elif char == ' ' and current:
                values.append(current)
                current = ""
            elif char != ' ':
                current += char

        if current:
            values.append(current)

        # Consolidate 'ALL' + 'TIME' -> 'ALL TIME'
        if len(values) >= 2 and values[0].upper() == 'ALL' and values[1].upper() == 'TIME':
            values = ['ALL TIME'] + values[2:]

        return values

    # ================================================================
    # HEADER-DRIVEN PARSING
    # ================================================================

    def _parse_header_driven(self, headers: List[str], values: List[str]) -> Dict:
        """
        Core parsing: match each header to a known stat, pair with its value.
        
        This is the key innovation — we don't care about positions,
        we care about WHAT the header says.
        """
        result = {
            'format': 'dynamic',
            'timezone': 'UTC',
            'timestamp': int(time.time()),
        }

        matched_count = 0
        unknown_count = 0

        for i, header in enumerate(headers):
            if i >= len(values):
                break

            value = values[i].strip()
            header_clean = header.strip()

            if not header_clean:
                continue

            # Resolve the header to a known stat
            stat_def, canonical_name = resolve_stat_name(header_clean)

            if stat_def:
                # Known stat
                result[stat_def['idx']] = {
                    'idx': stat_def['idx'],
                    'value': value,
                    'name': stat_def['name'],
                    'canonical_name': canonical_name,
                    'original_header': header_clean,
                    'type': stat_def['type'],
                    'is_unknown': False,
                    'position': i,
                }
                matched_count += 1
            else:
                # Unknown stat — store it anyway!
                dynamic_idx = assign_dynamic_idx()
                inferred_type = infer_stat_type(value)
                result[f'unknown_{dynamic_idx}'] = {
                    'idx': dynamic_idx,
                    'value': value,
                    'name': canonical_name,
                    'canonical_name': canonical_name,
                    'original_header': header_clean,
                    'type': inferred_type,
                    'is_unknown': True,
                    'position': i,
                }
                unknown_count += 1
                logger.info(f"Unknown stat discovered: '{header_clean}' = '{value}'")

        result['stats_count'] = matched_count + unknown_count
        result['matched_count'] = matched_count
        result['unknown_count'] = unknown_count

        # Validate required fields
        validation_error = self._validate(result)
        if validation_error:
            return validation_error

        return result

    def _validate(self, result: Dict) -> Optional[Dict]:
        """Validate parsed result has required fields."""
        # Count actual stats
        stats_count = sum(1 for k in result if isinstance(k, int) or str(k).startswith('unknown_'))
        if stats_count < self.minimum_stats_count:
            return {
                'error': f'Insufficient stats: {stats_count} < {self.minimum_stats_count}',
                'error_code': 7
            }

        # Check required fields by canonical name
        found_names = set()
        for key, stat in result.items():
            if isinstance(stat, dict) and 'canonical_name' in stat:
                found_names.add(stat['canonical_name'])

        for required in REQUIRED_STAT_NAMES:
            if required not in found_names:
                return {
                    'error': f'Missing required field: {required}',
                    'error_code': 8
                }

        # Validate faction
        faction_value = None
        for key, stat in result.items():
            if isinstance(stat, dict) and stat.get('canonical_name') == 'Agent Faction':
                faction_value = stat.get('value', '')
                break

        if faction_value and not validate_faction(faction_value):
            return {
                'error': f'Invalid faction: {faction_value}',
                'error_code': 9
            }

        return None