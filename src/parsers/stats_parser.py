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

            # If standard splitting failed, try no-delimiter mode
            if len(headers) < 5 or len(values) < 5:
                logger.info("Standard splitting produced too few fields, trying no-delimiter mode")
                headers = self._split_no_delimiter_header(header_line)
                if len(headers) >= 5:
                    values = self._split_no_delimiter_values(values_line, headers)
                    logger.info(f"No-delimiter mode: {len(headers)} headers, {len(values)} values")

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
    # NO-DELIMITER SPLITTING (Telegram strips tabs)
    # ================================================================

    def _split_no_delimiter_header(self, line: str) -> List[str]:
        """
        Split a concatenated header line using known stat names as markers.
        
        When Telegram strips tabs, headers become:
        'Time SpanAgent NameAgent Faction...'
        
        We find known stat names (longest first) and use their positions
        to split the string.
        """
        from ..config.stats_config import STAT_ALIASES
        
        # Build list of all known names (canonical + aliases)
        all_names = [s['name'] for s in STATS_DEFINITIONS]
        all_names.extend(STAT_ALIASES.keys())
        # Sort by length descending — match longest first to avoid partial matches
        all_names = sorted(set(all_names), key=len, reverse=True)

        # Find all matches with their positions
        matches = []  # (start_pos, end_pos, matched_name)
        remaining = line
        offset = 0

        # Iteratively find and mark known names
        marked = list(range(len(line)))  # Track which chars are "claimed"
        found_names = []  # (start, name)

        for name in all_names:
            pattern = re.compile(re.escape(name), re.IGNORECASE)
            for match in pattern.finditer(line):
                start, end = match.start(), match.end()
                # Check this region hasn't been claimed by a longer match
                if all(marked[i] == i for i in range(start, end)):
                    found_names.append((start, match.group(0)))
                    # Mark these positions as claimed
                    for i in range(start, end):
                        marked[i] = -1

        # Sort by position in the original string
        found_names.sort(key=lambda x: x[0])

        # Extract just the names in order
        headers = [name for _, name in found_names]

        if headers:
            logger.info(f"No-delimiter header split: found {len(headers)} stat names")

        return headers

    def _split_no_delimiter_values(self, line: str, headers: List[str]) -> List[str]:
        """
        Split a concatenated values line using header types as guides.
        
        When Telegram strips tabs, values become:
        'ALL TIMEH1GHT0WEREnlightened2026-02-1815:28:29141849712818497128...'
        
        Strategy:
        1. Match structured fields first: Time Span, Agent Name, Faction, Date, Time
        2. For the remaining digit stream (Level + all numeric stats):
           use domain knowledge to split intelligently
        """
        from ..config.stats_config import resolve_stat_name

        values = []
        pos = 0
        text = line

        for i, header in enumerate(headers):
            if pos >= len(text):
                values.append('')
                continue

            remaining = text[pos:]
            stat_def, canonical = resolve_stat_name(header)
            stat_type = stat_def['type'] if stat_def else 'S'
            stat_name = canonical

            value = None

            # --- Special pattern matching by known stat name ---
            if stat_name == 'Time Span':
                m = re.match(r'(ALL\s*TIME|LAST\s+\d+\s+DAYS?)', remaining, re.IGNORECASE)
                if m:
                    value = m.group(0)

            elif stat_name == 'Agent Faction':
                m = re.match(r'(Enlightened|Resistance)', remaining, re.IGNORECASE)
                if m:
                    value = m.group(0)

            elif stat_name == 'Date (yyyy-mm-dd)':
                m = re.match(r'(\d{4}-\d{2}-\d{2})', remaining)
                if m:
                    value = m.group(0)

            elif stat_name == 'Time (hh:mm:ss)':
                m = re.match(r'(\d{1,2}:\d{2}:\d{2})', remaining)
                if m:
                    value = m.group(0)

            elif stat_name == 'Level':
                # Level in Ingress is always 1-16 (1 or 2 digits)
                m = re.match(r'(\d{1,2})', remaining)
                if m:
                    lvl = int(m.group(0))
                    if lvl > 16 and len(m.group(0)) == 2:
                        # If 2-digit value > 16, it's likely just 1 digit
                        value = m.group(0)[0]
                    else:
                        value = m.group(0)

            elif stat_type == 'N':  # Other numeric stats
                # Count how many numeric headers remain (including current)
                remaining_numeric_count = sum(
                    1 for j in range(i, len(headers))
                    if resolve_stat_name(headers[j])[0]
                    and resolve_stat_name(headers[j])[0]['type'] == 'N'
                    and resolve_stat_name(headers[j])[1] != 'Level'
                )
                # Extract the full digit stream from current position
                m = re.match(r'(\d+)', remaining)
                if m:
                    digit_stream = m.group(0)
                    if remaining_numeric_count <= 1:
                        # Last numeric field — take all remaining digits
                        value = digit_stream
                    else:
                        # Split the digit stream: estimate avg digits per field
                        avg_digits = max(1, len(digit_stream) // remaining_numeric_count)
                        # Use at least 1 digit, at most avg_digits + a bit of flexibility
                        take = max(1, min(avg_digits, len(digit_stream) - remaining_numeric_count + 1))
                        value = digit_stream[:take]

            # --- Fallback: Agent Name and other string fields ---
            if value is None:
                if stat_type == 'S':
                    # For string fields, consume until the next known pattern starts
                    next_value = self._find_next_value_boundary(remaining, i, headers)
                    if next_value is not None:
                        value = remaining[:next_value]
                    else:
                        value = remaining  # Take the rest
                else:
                    # Unknown — take until next recognized pattern
                    m = re.match(r'([^\d]*\d[\d,]*)', remaining)
                    if m:
                        value = m.group(1)
                    else:
                        value = remaining

            value = value.strip() if value else ''
            values.append(value)
            pos += len(value) if value else 0

        return values

    def _find_next_value_boundary(self, remaining: str, current_idx: int, headers: List[str]) -> Optional[int]:
        """
        Find where the next value starts in a no-delimiter string.
        
        Looks ahead at the next header's expected type to find a boundary.
        """
        from ..config.stats_config import resolve_stat_name

        if current_idx + 1 >= len(headers):
            return None

        next_header = headers[current_idx + 1]
        next_def, next_canonical = resolve_stat_name(next_header)
        next_type = next_def['type'] if next_def else 'S'

        # Try to find where the next value starts
        if next_canonical == 'Agent Faction':
            m = re.search(r'(Enlightened|Resistance)', remaining, re.IGNORECASE)
            if m:
                return m.start()

        elif next_canonical == 'Date (yyyy-mm-dd)':
            m = re.search(r'\d{4}-\d{2}-\d{2}', remaining)
            if m:
                return m.start()

        elif next_canonical == 'Time (hh:mm:ss)':
            m = re.search(r'\d{1,2}:\d{2}:\d{2}', remaining)
            if m:
                return m.start()

        elif next_type == 'N':
            # Next field is numeric — find where digits start
            # But be careful: agent names can contain digits (e.g. H1GHT0WER)
            # Look for a faction name first as a better boundary
            faction_match = re.search(r'(Enlightened|Resistance)', remaining, re.IGNORECASE)
            if faction_match:
                return faction_match.start()
            # Otherwise find the digit boundary
            m = re.search(r'\d', remaining)
            if m:
                return m.start()

        return None

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