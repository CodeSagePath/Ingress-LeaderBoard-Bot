"""
Statistics configuration for Ingress Prime.

This module contains the real Ingress Prime stat definitions,
aliases for handling Niantic's format changes, and helper functions.

DESIGN: Header-driven, not position-driven.
- Stats are identified by their header name, not their position
- Aliases handle Niantic's frequent stat renames
- Unknown stats are accepted and stored, not rejected
"""

import difflib
from typing import Dict, List, Optional, Tuple

# Stat groups
STAT_GROUPS = {
    'HEAD': {'name': 'Head'},
    'DISCOVERY': {'name': 'Discovery'},
    'BUILDING': {'name': 'Building'},
    'RESOURCE': {'name': 'Resource Gathering'},
    'COMBAT': {'name': 'Combat'},
    'MACHINA': {'name': 'Machina'},
    'RECORDS': {'name': 'Records'},
    'EVENTS': {'name': 'Events'},
    'SPECIAL': {'name': 'Special'},
}

# Badge level names
BADGE_LEVELS = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Onyx']

# ============================================================================
# REAL INGRESS PRIME STATS (based on actual game data as of Feb 2026)
# These are the ~55 stats that Ingress Prime actually exports.
# The 'idx' is used internally for database storage.
# The 'name' is the CANONICAL name we use.
# ============================================================================
STATS_DEFINITIONS = [
    # === HEAD (meta fields) ===
    {'idx': 0, 'group': 'HEAD', 'type': 'S', 'name': 'Time Span'},
    {'idx': 1, 'group': 'HEAD', 'type': 'S', 'name': 'Agent Name'},
    {'idx': 2, 'group': 'HEAD', 'type': 'S', 'name': 'Agent Faction'},
    {'idx': 3, 'group': 'HEAD', 'type': 'S', 'name': 'Date (yyyy-mm-dd)'},
    {'idx': 4, 'group': 'HEAD', 'type': 'S', 'name': 'Time (hh:mm:ss)'},
    {'idx': 5, 'group': 'HEAD', 'type': 'N', 'name': 'Level'},
    {'idx': 6, 'group': 'HEAD', 'type': 'N', 'name': 'Lifetime AP',
     'badges': {'name': 'AP', 'levels': [2500000, 5000000, 10000000, 40000000, 160000000]}},
    {'idx': 7, 'group': 'HEAD', 'type': 'N', 'name': 'Current AP'},

    # === DISCOVERY ===
    {'idx': 8, 'group': 'DISCOVERY', 'type': 'N', 'name': 'Unique Portals Visited',
     'badges': {'name': 'Explorer', 'levels': [100, 1000, 2000, 10000, 30000]}},
    {'idx': 9, 'group': 'DISCOVERY', 'type': 'N', 'name': 'Unique Portals Drone Visited',
     'badges': {'name': 'Maverick', 'levels': [100, 500, 2000, 10000, 30000]}},
    {'idx': 10, 'group': 'DISCOVERY', 'type': 'N', 'name': 'Furthest Drone Distance'},
    {'idx': 11, 'group': 'DISCOVERY', 'type': 'N', 'name': 'Seer Points',
     'badges': {'name': 'Seer', 'levels': [10, 50, 200, 500, 5000]}},
    {'idx': 12, 'group': 'DISCOVERY', 'type': 'N', 'name': 'XM Collected'},
    {'idx': 13, 'group': 'DISCOVERY', 'type': 'N', 'name': 'OPR Agreements',
     'badges': {'name': 'Recon', 'levels': [100, 750, 2500, 5000, 10000]}},
    {'idx': 14, 'group': 'DISCOVERY', 'type': 'N', 'name': 'Portal Scans Uploaded',
     'badges': {'name': 'Scout', 'levels': [50, 250, 1000, 5000, 15000]}},
    {'idx': 15, 'group': 'DISCOVERY', 'type': 'N', 'name': 'Uniques Scout Controlled',
     'badges': {'name': 'Scout Controller', 'levels': [100, 500, 2000, 6000, 15000]}},

    # === BUILDING ===
    {'idx': 16, 'group': 'BUILDING', 'type': 'N', 'name': 'Resonators Deployed',
     'badges': {'name': 'Builder', 'levels': [2000, 10000, 30000, 100000, 300000]}},
    {'idx': 17, 'group': 'BUILDING', 'type': 'N', 'name': 'Links Created',
     'badges': {'name': 'Connector', 'levels': [300, 2000, 10000, 30000, 100000]}},
    {'idx': 18, 'group': 'BUILDING', 'type': 'N', 'name': 'Control Fields Created',
     'badges': {'name': 'Mind Controller', 'levels': [100, 500, 2000, 10000, 40000]}},
    {'idx': 19, 'group': 'BUILDING', 'type': 'N', 'name': 'Mind Units Captured',
     'badges': {'name': 'Illuminator', 'levels': [5000, 50000, 250000, 1000000, 4000000]}},
    {'idx': 20, 'group': 'BUILDING', 'type': 'N', 'name': 'Longest Link Ever Created'},
    {'idx': 21, 'group': 'BUILDING', 'type': 'N', 'name': 'Largest Control Field'},
    {'idx': 22, 'group': 'BUILDING', 'type': 'N', 'name': 'XM Recharged',
     'badges': {'name': 'Recharger', 'levels': [100000, 1000000, 3000000, 10000000, 25000000]}},
    {'idx': 23, 'group': 'BUILDING', 'type': 'N', 'name': 'Portals Captured',
     'badges': {'name': 'Liberator', 'levels': [100, 1000, 5000, 15000, 40000]}},
    {'idx': 24, 'group': 'BUILDING', 'type': 'N', 'name': 'Unique Portals Captured',
     'badges': {'name': 'Pioneer', 'levels': [20, 200, 1000, 5000, 20000]}},
    {'idx': 25, 'group': 'BUILDING', 'type': 'N', 'name': 'Mods Deployed',
     'badges': {'name': 'Engineer', 'levels': [150, 1500, 5000, 20000, 50000]}},

    # === RESOURCE ===
    {'idx': 26, 'group': 'RESOURCE', 'type': 'N', 'name': 'Hacks',
     'badges': {'name': 'Hacker', 'levels': [2000, 10000, 30000, 100000, 200000]}},
    {'idx': 27, 'group': 'RESOURCE', 'type': 'N', 'name': 'Drone Hacks'},
    {'idx': 28, 'group': 'RESOURCE', 'type': 'N', 'name': 'Glyph Hack Points',
     'badges': {'name': 'Translator', 'levels': [200, 2000, 6000, 20000, 50000]}},
    {'idx': 29, 'group': 'RESOURCE', 'type': 'N', 'name': 'Overclock Hack Points'},
    {'idx': 30, 'group': 'RESOURCE', 'type': 'N', 'name': 'Completed Hackstreaks'},
    {'idx': 31, 'group': 'RESOURCE', 'type': 'N', 'name': 'Longest Sojourner Streak',
     'badges': {'name': 'Sojourner', 'levels': [15, 30, 60, 180, 360]}},

    # === COMBAT ===
    {'idx': 32, 'group': 'COMBAT', 'type': 'N', 'name': 'Resonators Destroyed',
     'badges': {'name': 'Purifier', 'levels': [2000, 10000, 30000, 100000, 300000]}},
    {'idx': 33, 'group': 'COMBAT', 'type': 'N', 'name': 'Portals Neutralized'},
    {'idx': 34, 'group': 'COMBAT', 'type': 'N', 'name': 'Enemy Links Destroyed'},
    {'idx': 35, 'group': 'COMBAT', 'type': 'N', 'name': 'Enemy Fields Destroyed'},
    {'idx': 36, 'group': 'COMBAT', 'type': 'N', 'name': 'Drones Returned'},

    # === MACHINA ===
    {'idx': 37, 'group': 'MACHINA', 'type': 'N', 'name': 'Machina Links Destroyed',
     'badges': {'name': 'Machina Recycler', 'levels': [100, 500, 4000, 10000, 40000]}},
    {'idx': 38, 'group': 'MACHINA', 'type': 'N', 'name': 'Machina Resonators Destroyed'},
    {'idx': 39, 'group': 'MACHINA', 'type': 'N', 'name': 'Machina Portals Neutralized'},
    {'idx': 40, 'group': 'MACHINA', 'type': 'N', 'name': 'Machina Portals Reclaimed',
     'badges': {'name': 'Reclaimer', 'levels': [100, 500, 2000, 10000, 20000]}},

    # === RECORDS ===
    {'idx': 41, 'group': 'RECORDS', 'type': 'N', 'name': 'Max Time Portal Held',
     'badges': {'name': 'Guardian', 'levels': [3, 10, 20, 90, 150]}},
    {'idx': 42, 'group': 'RECORDS', 'type': 'N', 'name': 'Max Time Link Maintained'},
    {'idx': 43, 'group': 'RECORDS', 'type': 'N', 'name': 'Max Link Length x Days'},
    {'idx': 44, 'group': 'RECORDS', 'type': 'N', 'name': 'Max Time Field Held'},
    {'idx': 45, 'group': 'RECORDS', 'type': 'N', 'name': 'Largest Field MUs x Days'},
    {'idx': 46, 'group': 'RECORDS', 'type': 'N', 'name': 'Forced Drone Recalls'},

    # === MOVEMENT & MISC ===
    {'idx': 47, 'group': 'DISCOVERY', 'type': 'N', 'name': 'Distance Walked',
     'badges': {'name': 'Trekker', 'levels': [10, 100, 300, 1000, 2500]}},
    {'idx': 48, 'group': 'RESOURCE', 'type': 'N', 'name': 'Kinetic Capsules Completed'},
    {'idx': 49, 'group': 'DISCOVERY', 'type': 'N', 'name': 'Unique Missions Completed',
     'badges': {'name': 'SpecOps', 'levels': [5, 25, 100, 200, 500]}},
    {'idx': 50, 'group': 'DISCOVERY', 'type': 'N', 'name': 'Research Bounties Completed'},
    {'idx': 51, 'group': 'DISCOVERY', 'type': 'N', 'name': 'Research Days Completed'},

    # === EVENTS ===
    {'idx': 52, 'group': 'EVENTS', 'type': 'N', 'name': 'NL-1331 Meetup(s) Attended',
     'badges': {'name': 'NL-1331 Meetups', 'levels': [1, 5, 10, 25, 50]}},
    {'idx': 53, 'group': 'EVENTS', 'type': 'N', 'name': 'First Saturday Events',
     'badges': {'name': 'First Saturday', 'levels': [1, 6, 12, 24, 36]}},
    {'idx': 54, 'group': 'EVENTS', 'type': 'N', 'name': 'Second Sunday Events'},
    {'idx': 55, 'group': 'EVENTS', 'type': 'N', 'name': 'Mission Day(s) Attended',
     'badges': {'name': 'Mission Day', 'levels': [1, 3, 6, 10, 20]}},

    # === SPECIAL ===
    {'idx': 56, 'group': 'SPECIAL', 'type': 'N', 'name': '+Gamma Tokens'},
    {'idx': 57, 'group': 'SPECIAL', 'type': 'N', 'name': '+Gamma Link Points'},
    {'idx': 58, 'group': 'SPECIAL', 'type': 'N', 'name': 'Agents Recruited',
     'badges': {'name': 'Recruiter', 'levels': [2, 10, 25, 50, 100]}},
    {'idx': 59, 'group': 'SPECIAL', 'type': 'N', 'name': 'Months Subscribed',
     'badges': {'name': 'Patron', 'levels': [1, 3, 6, 12, 24]}},
    {'idx': 60, 'group': 'SPECIAL', 'type': 'N', 'name': 'Recursions'},
]

# ============================================================================
# STAT ALIASES
# Maps alternate/old names → canonical name.
# When Niantic renames a stat, just add a new alias here.
# Keys are LOWERCASE for case-insensitive matching.
# ============================================================================
STAT_ALIASES = {
    # Head aliases
    'date': 'Date (yyyy-mm-dd)',
    'time': 'Time (hh:mm:ss)',
    'date (yyyy/mm/dd)': 'Date (yyyy-mm-dd)',
    'faction': 'Agent Faction',

    # Discovery aliases
    'portals discovered': 'Unique Portals Visited',
    'seer': 'Seer Points',
    'portal scans': 'Portal Scans Uploaded',
    'scout controlled': 'Uniques Scout Controlled',
    'unique scout controlled': 'Uniques Scout Controlled',
    'furthest drone flight distance': 'Furthest Drone Distance',

    # Building aliases
    'mu captured': 'Mind Units Captured',
    'mind units': 'Mind Units Captured',
    'longest link': 'Longest Link Ever Created',
    'largest field': 'Largest Control Field',
    'largest control field mu': 'Largest Control Field',
    'unique portals owned': 'Unique Portals Captured',

    # Resource aliases
    'glyph hack points completed': 'Glyph Hack Points',
    'glyph points': 'Glyph Hack Points',
    'overclock hack points completed': 'Overclock Hack Points',
    'sojourner': 'Longest Sojourner Streak',
    'sojourner streak': 'Longest Sojourner Streak',
    'hackstreaks': 'Completed Hackstreaks',
    'hack streaks': 'Completed Hackstreaks',

    # Combat aliases
    'enemy control fields destroyed': 'Enemy Fields Destroyed',
    'combatant drones returned': 'Drones Returned',
    'battle beacon combatant': 'Drones Returned',

    # Machina aliases
    'machina links': 'Machina Links Destroyed',
    'machina resonators': 'Machina Resonators Destroyed',
    'machina portals destroyed': 'Machina Portals Neutralized',
    'machina reclaimed': 'Machina Portals Reclaimed',

    # Records aliases
    'max time portal held days': 'Max Time Portal Held',
    'max time link maintained days': 'Max Time Link Maintained',
    'max link length x days km': 'Max Link Length x Days',
    'max time field held days': 'Max Time Field Held',
    'largest field mus x days': 'Largest Field MUs x Days',

    # Events aliases
    'nl-1331 meetups attended': 'NL-1331 Meetup(s) Attended',
    'nl-1331 meetups': 'NL-1331 Meetup(s) Attended',
    'first saturday': 'First Saturday Events',
    'second sunday': 'Second Sunday Events',
    'mission days attended': 'Mission Day(s) Attended',
    'mission day(s)': 'Mission Day(s) Attended',
    'mission days': 'Mission Day(s) Attended',

    # Special aliases
    'beta tokens': '+Gamma Tokens',
    '+beta tokens': '+Gamma Tokens',
    'gamma tokens': '+Gamma Tokens',
    'gamma link points': '+Gamma Link Points',
    'recruited': 'Agents Recruited',
    'subscription months': 'Months Subscribed',
    'recursion': 'Recursions',

    # Movement
    'trekker': 'Distance Walked',
    'distance walked km': 'Distance Walked',
    'kinetic capsules': 'Kinetic Capsules Completed',
    'missions completed': 'Unique Missions Completed',
    'research bounties': 'Research Bounties Completed',
    'research days': 'Research Days Completed',
}

# ============================================================================
# REQUIRED STATS (must be present for a valid submission)
# ============================================================================
REQUIRED_STAT_NAMES = [
    'Agent Name',
    'Agent Faction',
    'Date (yyyy-mm-dd)',
]

# ============================================================================
# Lookup dictionaries (built once at import time)
# ============================================================================
_STATS_BY_IDX = {stat['idx']: stat for stat in STATS_DEFINITIONS}
_STATS_BY_NAME = {stat['name'].lower(): stat for stat in STATS_DEFINITIONS}
_ALL_KNOWN_NAMES = list(_STATS_BY_NAME.keys())
_NEXT_DYNAMIC_IDX = max(s['idx'] for s in STATS_DEFINITIONS) + 1


def get_stat_by_idx(idx: int) -> Optional[Dict]:
    """Retrieve stat definition by index."""
    return _STATS_BY_IDX.get(idx)


def get_stat_by_name(name: str) -> Optional[Dict]:
    """Retrieve stat definition by exact name (case-insensitive)."""
    return _STATS_BY_NAME.get(name.lower())


def resolve_stat_name(header: str) -> Tuple[Optional[Dict], str]:
    """
    Resolve a header name to a known stat definition.
    
    Uses 3-tier matching:
      1. Exact match (case-insensitive)
      2. Alias match
      3. Fuzzy match (>80% similarity)
    
    Args:
        header: The header name from the stats export
        
    Returns:
        Tuple of (stat_definition_or_None, canonical_name)
    """
    header_clean = header.strip()
    header_lower = header_clean.lower()
    
    # 1. Exact match
    stat = _STATS_BY_NAME.get(header_lower)
    if stat:
        return stat, stat['name']
    
    # 2. Alias match
    canonical = STAT_ALIASES.get(header_lower)
    if canonical:
        stat = _STATS_BY_NAME.get(canonical.lower())
        if stat:
            return stat, stat['name']
    
    # 3. Fuzzy match (>80% similarity)
    matches = difflib.get_close_matches(header_lower, _ALL_KNOWN_NAMES, n=1, cutoff=0.80)
    if matches:
        stat = _STATS_BY_NAME.get(matches[0])
        if stat:
            return stat, stat['name']
    
    # No match — this is an unknown stat
    return None, header_clean


def assign_dynamic_idx() -> int:
    """Assign a new dynamic index for an unknown stat."""
    global _NEXT_DYNAMIC_IDX
    idx = _NEXT_DYNAMIC_IDX
    _NEXT_DYNAMIC_IDX += 1
    return idx


def infer_stat_type(value: str) -> str:
    """
    Infer whether a value is numeric or string.
    
    Args:
        value: The raw value string
        
    Returns:
        'N' for numeric, 'S' for string
    """
    # Strip commas and spaces
    cleaned = value.replace(',', '').replace(' ', '').strip()
    try:
        int(cleaned)
        return 'N'
    except ValueError:
        try:
            float(cleaned)
            return 'N'
        except ValueError:
            return 'S'


def get_badge_level(stat_idx: int, value) -> Tuple[Optional[str], Optional[int]]:
    """
    Calculate badge level for a stat value.
    
    Returns:
        Tuple of (badge_level_name, next_level_value) or (None, None)
    """
    if isinstance(value, float):
        value = int(value)
    
    stat = get_stat_by_idx(stat_idx)
    if not stat or 'badges' not in stat:
        return None, None

    levels = stat['badges']['levels']
    current_level = None
    next_level = None

    for i, level_value in enumerate(levels):
        if value >= level_value:
            if i < len(BADGE_LEVELS):
                current_level = BADGE_LEVELS[i]
            else:
                current_level = f"Level {i + 1}"
            if i + 1 < len(levels):
                next_level = levels[i + 1]
        else:
            if not next_level:
                next_level = level_value
            break

    return current_level, next_level


def get_leaderboard_stats() -> List[Dict]:
    """Get list of stats suitable for leaderboards."""
    return [
        stat for stat in STATS_DEFINITIONS
        if stat['type'] == 'N' and
           stat['name'] not in ['Current AP'] and
           stat['idx'] >= 5
    ]


def format_stat_value(stat_idx: int, value: int) -> str:
    """Format a stat value with appropriate units."""
    stat = get_stat_by_idx(stat_idx)
    if not stat:
        return f"{value:,}"

    name = stat['name']

    # Distance formatting
    if 'Distance' in name and 'Drone' not in name:
        return f"{value:,} km"

    # XM formatting
    if 'XM' in name:
        return f"{value:,} XM"

    # MU formatting
    if 'MU' in name or 'Mind Units' in name:
        if value >= 1000000:
            return f"{value/1000000:.1f}M MU"
        elif value >= 1000:
            return f"{value/1000:.1f}K MU"
        return f"{value:,} MU"

    # Time formatting
    if 'Time' in name and ('Held' in name or 'Maintained' in name):
        return f"{value:,} days"

    # Large number formatting
    if value >= 1000000:
        return f"{value/1000000:.1f}M"
    elif value >= 1000:
        return f"{value/1000:.1f}K"

    return f"{value:,}"


def validate_faction(faction: str) -> bool:
    """Validate faction name."""
    return faction.strip().title() in ['Enlightened', 'Resistance']