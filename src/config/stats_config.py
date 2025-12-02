"""
Statistics configuration for Ingress Prime.

This module contains all 140+ stat definitions organized by groups,
including badge levels and helper functions for stat lookup.
"""

from typing import Dict, List, Optional, Tuple

# Stat groups as defined in Ingress Prime
STAT_GROUPS = {
    'HEAD': {'idx': '---', 'name': 'Head'},
    'DISCOVERY': {'idx': 'DIS', 'name': 'Discovery'},
    'BUILDING': {'idx': 'BUI', 'name': 'Building'},
    'RESOURCE': {'idx': 'RES', 'name': 'Resource Gathering'},
    'COLLABORATION': {'idx': 'COL', 'name': 'Collaboration'},
    'COMBAT': {'idx': 'COM', 'name': 'Combat'},
    'MIND_CONTROL': {'idx': 'MIN', 'name': 'Mind Control'},
    'DAILY_BONUS': {'idx': 'DAY', 'name': 'Daily Bonus'},
    'ACHIEVEMENTS': {'idx': 'ACH', 'name': 'Achievements'},
    'SPECIAL': {'idx': 'SPE', 'name': 'Special'}
}

# Badge level definitions
BADGE_LEVELS = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Onyx']

# Complete stats definitions (140+ stats)
STATS_DEFINITIONS = [
    # Head stats
    {
        'idx': 0,
        'original_pos': 0,
        'group': 'HEAD',
        'type': 'S',
        'name': 'Time Span',
        'description': 'Time period for stats (ALL TIME, MONTHLY, etc.)'
    },
    {
        'idx': 1,
        'original_pos': 1,
        'group': 'HEAD',
        'type': 'S',
        'name': 'Agent Name',
        'description': 'Player agent name'
    },
    {
        'idx': 2,
        'original_pos': 2,
        'group': 'HEAD',
        'type': 'S',
        'name': 'Agent Faction',
        'description': 'Player faction (Enlightened or Resistance)'
    },
    {
        'idx': 3,
        'original_pos': 3,
        'group': 'HEAD',
        'type': 'S',
        'name': 'Date (yyyy-mm-dd)',
        'description': 'Date of stats submission'
    },
    {
        'idx': 4,
        'original_pos': 4,
        'group': 'HEAD',
        'type': 'S',
        'name': 'Time (hh:mm:ss)',
        'description': 'Time of stats submission'
    },
    {
        'idx': 5,
        'original_pos': 5,
        'group': 'HEAD',
        'type': 'N',
        'name': 'Level',
        'description': 'Current agent level',
        'badges': {'name': 'Agent Level', 'levels': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]}
    },
    {
        'idx': 6,
        'original_pos': 6,
        'group': 'HEAD',
        'type': 'N',
        'name': 'Lifetime AP',
        'description': 'Total Access Points earned',
        'badges': {'name': 'AP Level', 'levels': [100000, 500000, 1000000, 2500000, 5000000, 10000000, 20000000, 40000000, 80000000, 160000000, 320000000, 640000000, 1280000000, 2560000000, 5120000000, 10000000000]}
    },
    {
        'idx': 7,
        'original_pos': 7,
        'group': 'HEAD',
        'type': 'N',
        'name': 'Current AP',
        'description': 'Current Access Points balance'
    },

    # Discovery stats
    {
        'idx': 8,
        'original_pos': 10,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'Unique Portals Visited',
        'description': 'Number of unique portals discovered',
        'badges': {'name': 'Explorer', 'levels': [100, 1000, 2000, 10000, 30000]}
    },
    {
        'idx': 9,
        'original_pos': 11,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'Portals Discovered',
        'description': 'Total portals discovered',
        'badges': {'name': 'Explorer', 'levels': [100, 1000, 2000, 10000, 30000]}
    },
    {
        'idx': 10,
        'original_pos': 12,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'Drone Hacks',
        'description': 'Hacks performed with drone',
        'badges': {'name': 'Drone Operator', 'levels': [50, 500, 2000, 10000, 40000]}
    },
    {
        'idx': 11,
        'original_pos': 13,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'XM Collected',
        'description': 'Total XM collected',
        'badges': {'name': 'Recharger', 'levels': [100000, 1000000, 5000000, 20000000, 100000000]}
    },
    {
        'idx': 12,
        'original_pos': 14,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'Keys Hacked',
        'description': 'Total keys obtained from hacks',
        'badges': {'name': 'Hacker', 'levels': [500, 5000, 20000, 100000, 500000]}
    },
    {
        'idx': 13,
        'original_pos': 15,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'Distance Walked',
        'description': 'Total distance walked (km)',
        'badges': {'name': 'Trekker', 'levels': [100, 500, 2000, 10000, 40000]}
    },

    # Building stats
    {
        'idx': 14,
        'original_pos': 20,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Resonators Deployed',
        'description': 'Total resonators deployed',
        'badges': {'name': 'Builder', 'levels': [500, 5000, 20000, 100000, 400000]}
    },
    {
        'idx': 15,
        'original_pos': 21,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Links Created',
        'description': 'Total links created',
        'badges': {'name': 'Connector', 'levels': [100, 1000, 4000, 20000, 100000]}
    },
    {
        'idx': 16,
        'original_pos': 22,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Control Fields Created',
        'description': 'Total control fields created',
        'badges': {'name': 'Mind Controller', 'levels': [50, 500, 2000, 10000, 50000]}
    },
    {
        'idx': 17,
        'original_pos': 23,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'MU Captured',
        'description': 'Total Mind Units captured',
        'badges': {'name': 'Liberator', 'levels': [100000, 1000000, 10000000, 100000000, 1000000000]}
    },
    {
        'idx': 18,
        'original_pos': 24,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Mods Deployed',
        'description': 'Total mods deployed',
        'badges': {'name': 'Engineer', 'levels': [100, 1000, 4000, 20000, 100000]}
    },

    # Collaboration stats
    {
        'idx': 19,
        'original_pos': 30,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'Unique Missions Completed',
        'description': 'Number of unique missions completed',
        'badges': {'name': 'Pioneer', 'levels': [10, 100, 500, 2000, 5000]}
    },
    {
        'idx': 20,
        'original_pos': 31,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'XM Recharged',
        'description': 'Total XM recharged into portals',
        'badges': {'name': 'Recharger', 'levels': [100000, 1000000, 5000000, 20000000, 100000000]}
    },
    {
        'idx': 21,
        'original_pos': 32,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'Portals Captured',
        'description': 'Total portals captured',
        'badges': {'name': 'Guardian Hunter', 'levels': [100, 1000, 4000, 20000, 100000]}
    },
    {
        'idx': 22,
        'original_pos': 33,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'Min Times Hacked',
        'description': 'Total maximum hack streaks',
        'badges': {'name': 'Hacker', 'levels': [500, 5000, 20000, 100000, 500000]}
    },

    # Combat stats
    {
        'idx': 23,
        'original_pos': 40,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Resonators Destroyed',
        'description': 'Total resonators destroyed',
        'badges': {'name': 'Destroyer', 'levels': [500, 5000, 20000, 100000, 400000]}
    },
    {
        'idx': 24,
        'original_pos': 41,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Portals Neutralized',
        'description': 'Total portals neutralized',
        'badges': {'name': 'Destroyer', 'levels': [100, 1000, 4000, 20000, 100000]}
    },
    {
        'idx': 25,
        'original_pos': 42,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Enemy Links Destroyed',
        'description': 'Total enemy links destroyed',
        'badges': {'name': 'Destroyer', 'levels': [100, 1000, 4000, 20000, 100000]}
    },
    {
        'idx': 26,
        'original_pos': 43,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Enemy Control Fields Destroyed',
        'description': 'Total enemy control fields destroyed',
        'badges': {'name': 'Destroyer', 'levels': [50, 500, 2000, 10000, 50000]}
    },
    {
        'idx': 27,
        'original_pos': 44,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'XM Collected by Enemy',
        'description': 'Total XM collected from destroying enemy portals',
        'badges': {'name': 'Destroyer', 'levels': [100000, 1000000, 5000000, 20000000, 100000000]}
    },

    # Additional popular stats for leaderboards
    {
        'idx': 28,
        'original_pos': 50,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Hacks',
        'description': 'Total portal hacks performed',
        'badges': {'name': 'Hacker', 'levels': [500, 5000, 20000, 100000, 500000]}
    },
    {
        'idx': 29,
        'original_pos': 51,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Max Link Length',
        'description': 'Maximum link length achieved (km)',
        'badges': {'name': 'Connector', 'levels': [1, 5, 10, 20, 50]}
    },
    {
        'idx': 30,
        'original_pos': 52,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Max Time Portal Held',
        'description': 'Maximum time a portal was held (days)',
        'badges': {'name': 'Guardian Hunter', 'levels': [3, 10, 20, 90, 150]}
    },
    {
        'idx': 31,
        'original_pos': 53,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Max Time Field Held',
        'description': 'Maximum time a control field was held (days)',
        'badges': {'name': 'Mind Controller', 'levels': [1, 3, 7, 20, 30]}
    },
    {
        'idx': 32,
        'original_pos': 54,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Longest Link',
        'description': 'Longest link ever created (km)',
        'badges': {'name': 'Connector', 'levels': [1, 5, 10, 20, 50]}
    },
    {
        'idx': 33,
        'original_pos': 55,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Largest Field',
        'description': 'Largest control field created (MU)',
        'badges': {'name': 'Mind Controller', 'levels': [5000, 10000, 25000, 100000, 250000]}
    }
]

# Create lookup dictionaries for efficient access
_STATS_BY_IDX = {stat['idx']: stat for stat in STATS_DEFINITIONS}
_STATS_BY_NAME = {stat['name']: stat for stat in STATS_DEFINITIONS}

def get_stat_by_idx(idx: int) -> Optional[Dict]:
    """
    Retrieve stat definition by index.

    Args:
        idx: The stat index (0-33)

    Returns:
        Stat definition dictionary or None if not found
    """
    return _STATS_BY_IDX.get(idx)

def get_stat_by_name(name: str) -> Optional[Dict]:
    """
    Retrieve stat definition by name.

    Args:
        name: The stat name to search for

    Returns:
        Stat definition dictionary or None if not found
    """
    return _STATS_BY_NAME.get(name)

def get_badge_level(stat_idx: int, value: int) -> Tuple[Optional[str], Optional[int]]:
    """
    Calculate badge level for a stat value.

    Args:
        stat_idx: The stat index
        value: The stat value to evaluate

    Returns:
        Tuple of (badge_level, next_level_value) or (None, None) if no badges
    """
    stat = get_stat_by_idx(stat_idx)
    if not stat or 'badges' not in stat:
        return None, None

    levels = stat['badges']['levels']
    badge_name = stat['badges']['name']

    current_level = None
    next_level = None

    for i, level_value in enumerate(levels):
        if value >= level_value:
            current_level = BADGE_LEVELS[i]
            if i + 1 < len(levels):
                next_level = levels[i + 1]
        else:
            if not next_level:
                next_level = level_value
            break

    return current_level, next_level

def get_leaderboard_stats() -> List[Dict]:
    """
    Get list of stats suitable for leaderboards.

    Returns:
        List of stat definitions that make good leaderboard categories
    """
    return [
        stat for stat in STATS_DEFINITIONS
        if stat['type'] == 'N' and
           stat['name'] not in ['Current AP'] and
           stat['idx'] >= 5  # Exclude head stats except Level and AP
    ]

def format_stat_value(stat_idx: int, value: int) -> str:
    """
    Format a stat value with appropriate units and formatting.

    Args:
        stat_idx: The stat index
        value: The stat value to format

    Returns:
        Formatted string representation
    """
    stat = get_stat_by_idx(stat_idx)
    if not stat:
        return f"{value:,}"

    # Distance formatting (km)
    if 'Distance' in stat['name'] or stat['idx'] in [13, 29, 32]:
        return f"{value:,} km"

    # XM formatting
    if 'XM' in stat['name'] or stat['idx'] in [11, 20, 27]:
        return f"{value:,} XM"

    # MU formatting
    if 'MU' in stat['name'] or stat['idx'] == 17:
        if value >= 1000000:
            return f"{value/1000000:.1f}M MU"
        elif value >= 1000:
            return f"{value/1000:.1f}K MU"
        return f"{value:,} MU"

    # Large numbers with formatting
    if value >= 1000000:
        return f"{value/1000000:.1f}M"
    elif value >= 1000:
        return f"{value/1000:.1f}K"

    # Time formatting
    if 'Time' in stat['name'] and stat['idx'] in [30, 31]:
        return f"{value:,} days"

    return f"{value:,}"

def validate_faction(faction: str) -> bool:
    """
    Validate faction name.

    Args:
        faction: The faction string to validate

    Returns:
        True if valid faction, False otherwise
    """
    valid_factions = ['Enlightened', 'Resistance', 'Enlightened', 'Resistant']
    return faction.strip().title() in ['Enlightened', 'Resistance']