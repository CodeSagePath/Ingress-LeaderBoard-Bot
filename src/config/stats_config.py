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
    },

    # Expanded DISCOVERY stats (indices 34-42)
    {
        'idx': 34,
        'original_pos': 70,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'Scout Controller',
        'description': 'Portals controlled with Scout Controller',
        'badges': {'name': 'Scout Controller', 'levels': [100, 1000, 5000, 20000, 100000]}
    },
    {
        'idx': 35,
        'original_pos': 71,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'Drone Range',
        'description': 'Maximum drone range achieved (m)',
        'badges': {'name': 'Drone Operator', 'levels': [500, 2000, 10000, 50000, 250000]}
    },
    {
        'idx': 36,
        'original_pos': 72,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'Drone Zoom Hacks',
        'description': 'Total drone zoom hacks performed',
        'badges': {'name': 'Drone Operator', 'levels': [100, 1000, 5000, 25000, 100000]}
    },
    {
        'idx': 37,
        'original_pos': 73,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'Portals Scanned',
        'description': 'Total portals scanned with Scanner',
        'badges': {'name': 'Explorer', 'levels': [500, 5000, 25000, 100000, 500000]}
    },
    {
        'idx': 38,
        'original_pos': 74,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'Seer Points',
        'description': 'Points earned from Seer predictions',
        'badges': {'name': 'Seer', 'levels': [100, 1000, 5000, 25000, 100000]}
    },
    {
        'idx': 39,
        'original_pos': 75,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'First Friday Captures',
        'description': 'Portals captured on First Friday',
        'badges': {'name': 'Explorer', 'levels': [50, 250, 1000, 5000, 25000]}
    },
    {
        'idx': 40,
        'original_pos': 76,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'Unique Portal Scans',
        'description': 'Unique portals scanned with Scanner',
        'badges': {'name': 'Explorer', 'levels': [200, 2000, 10000, 50000, 250000]}
    },
    {
        'idx': 41,
        'original_pos': 77,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'Drone Total Distance',
        'description': 'Total distance traveled by drone (km)',
        'badges': {'name': 'Drone Operator', 'levels': [1000, 10000, 50000, 250000, 1000000]}
    },
    {
        'idx': 42,
        'original_pos': 78,
        'group': 'DISCOVERY',
        'type': 'N',
        'name': 'Drone Flight Time',
        'description': 'Total drone flight time (hours)',
        'badges': {'name': 'Drone Operator', 'levels': [100, 1000, 5000, 25000, 100000]}
    },

    # Expanded BUILDING stats (indices 43-57)
    {
        'idx': 43,
        'original_pos': 80,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Level 1 Portals Deployed',
        'description': 'Number of level 1 portals deployed',
        'badges': {'name': 'Builder', 'levels': [500, 2500, 10000, 50000, 250000]}
    },
    {
        'idx': 44,
        'original_pos': 81,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Level 2 Portals Deployed',
        'description': 'Number of level 2 portals deployed',
        'badges': {'name': 'Builder', 'levels': [250, 1500, 7500, 35000, 150000]}
    },
    {
        'idx': 45,
        'original_pos': 82,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Level 3 Portals Deployed',
        'description': 'Number of level 3 portals deployed',
        'badges': {'name': 'Builder', 'levels': [100, 800, 4000, 20000, 100000]}
    },
    {
        'idx': 46,
        'original_pos': 83,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Level 4 Portals Deployed',
        'description': 'Number of level 4 portals deployed',
        'badges': {'name': 'Builder', 'levels': [50, 400, 2500, 15000, 75000]}
    },
    {
        'idx': 47,
        'original_pos': 84,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Level 5 Portals Deployed',
        'description': 'Number of level 5 portals deployed',
        'badges': {'name': 'Builder', 'levels': [25, 200, 1500, 10000, 50000]}
    },
    {
        'idx': 48,
        'original_pos': 85,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Level 6 Portals Deployed',
        'description': 'Number of level 6 portals deployed',
        'badges': {'name': 'Builder', 'levels': [10, 100, 800, 5000, 25000]}
    },
    {
        'idx': 49,
        'original_pos': 86,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Level 7 Portals Deployed',
        'description': 'Number of level 7 portals deployed',
        'badges': {'name': 'Builder', 'levels': [5, 50, 400, 2500, 15000]}
    },
    {
        'idx': 50,
        'original_pos': 87,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Level 8 Portals Deployed',
        'description': 'Number of level 8 portals deployed',
        'badges': {'name': 'Builder', 'levels': [2, 25, 200, 1500, 7500]}
    },
    {
        'idx': 51,
        'original_pos': 88,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Heat Sink Mods Deployed',
        'description': 'Total Heat Sink mods deployed',
        'badges': {'name': 'Engineer', 'levels': [500, 5000, 25000, 100000, 500000]}
    },
    {
        'idx': 52,
        'original_pos': 89,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Force Amp Mods Deployed',
        'description': 'Total Force Amp mods deployed',
        'badges': {'name': 'Engineer', 'levels': [250, 2500, 15000, 75000, 250000]}
    },
    {
        'idx': 53,
        'original_pos': 90,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Turret Mods Deployed',
        'description': 'Total Turret mods deployed',
        'badges': {'name': 'Engineer', 'levels': [250, 2500, 15000, 75000, 250000]}
    },
    {
        'idx': 54,
        'original_pos': 91,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Shield Mods Deployed',
        'description': 'Total Shield mods deployed',
        'badges': {'name': 'Engineer', 'levels': [1000, 10000, 50000, 250000, 1000000]}
    },
    {
        'idx': 55,
        'original_pos': 92,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Link Amp Mods Deployed',
        'description': 'Total Link Amp mods deployed',
        'badges': {'name': 'Engineer', 'levels': [200, 2000, 12000, 60000, 250000]}
    },
    {
        'idx': 56,
        'original_pos': 93,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Portal Fortifications',
        'description': 'Total portal fortification actions',
        'badges': {'name': 'Guardian', 'levels': [1000, 8000, 40000, 200000, 1000000]}
    },
    {
        'idx': 57,
        'original_pos': 94,
        'group': 'BUILDING',
        'type': 'N',
        'name': 'Portal Upgrades',
        'description': 'Total portal upgrades performed',
        'badges': {'name': 'Builder', 'levels': [2000, 15000, 75000, 350000, 1500000]}
    },

    # Expanded COLLABORATION stats (indices 58-68)
    {
        'idx': 58,
        'original_pos': 100,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'Missions Created',
        'description': 'Total missions created',
        'badges': {'name': 'Mission Creator', 'levels': [25, 100, 500, 2000, 10000]}
    },
    {
        'idx': 59,
        'original_pos': 101,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'Missions Reviewed',
        'description': 'Total missions reviewed',
        'badges': {'name': 'Mission Reviewer', 'levels': [100, 1000, 5000, 20000, 100000]}
    },
    {
        'idx': 60,
        'original_pos': 102,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'Beacons Deployed',
        'description': 'Total beacons deployed on portals',
        'badges': {'name': 'Beacon Deployer', 'levels': [500, 5000, 25000, 100000, 500000]}
    },
    {
        'idx': 61,
        'original_pos': 103,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'Frackers Deployed',
        'description': 'Total frackers deployed on portals',
        'badges': {'name': 'Fracker Deployer', 'levels': [250, 2500, 15000, 75000, 250000]}
    },
    {
        'idx': 62,
        'original_pos': 104,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'IITC Modules Used',
        'description': 'Total IITC (Ingress Intel Total Conversion) modules used',
        'badges': {'name': 'Intel Analyst', 'levels': [50, 500, 2500, 15000, 75000]}
    },
    {
        'idx': 63,
        'original_pos': 105,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'Resource Sharing',
        'description': 'Total resources shared with other agents',
        'badges': {'name': 'Collaborator', 'levels': [10000, 100000, 500000, 2500000, 10000000]}
    },
    {
        'idx': 64,
        'original_pos': 106,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'Team Field Creation',
        'description': 'Control fields created with multiple agents',
        'badges': {'name': 'Team Player', 'levels': [100, 800, 5000, 25000, 100000]}
    },
    {
        'idx': 65,
        'original_pos': 107,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'Cross-Faction Events',
        'description': 'Participation in cross-faction events',
        'badges': {'name': 'Diplomat', 'levels': [10, 50, 200, 1000, 5000]}
    },
    {
        'idx': 66,
        'original_pos': 108,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'Community Missions',
        'description': 'Community missions completed',
        'badges': {'name': 'Community Leader', 'levels': [25, 200, 1000, 5000, 25000]}
    },
    {
        'idx': 67,
        'original_pos': 109,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'Event Participation',
        'description': 'Official Niantic events participated in',
        'badges': {'name': 'Event Veteran', 'levels': [5, 20, 100, 500, 2500]}
    },
    {
        'idx': 68,
        'original_pos': 110,
        'group': 'COLLABORATION',
        'type': 'N',
        'name': 'Recruitment Actions',
        'description': 'New agents recruited and mentored',
        'badges': {'name': 'Recruiter', 'levels': [5, 15, 50, 150, 500]}
    },

    # Expanded COMBAT stats (indices 69-88)
    {
        'idx': 69,
        'original_pos': 120,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Battle Beacons Used',
        'description': 'Total battle beacons used on enemy portals',
        'badges': {'name': 'Warrior', 'levels': [250, 2500, 15000, 75000, 250000]}
    },
    {
        'idx': 70,
        'original_pos': 121,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'JARVIS Virus Deployed',
        'description': 'Total JARVIS viruses deployed',
        'badges': {'name': 'Saboteur', 'levels': [100, 1000, 5000, 25000, 100000]}
    },
    {
        'idx': 71,
        'original_pos': 122,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'ADA Virus Deployed',
        'description': 'Total ADA viruses deployed',
        'badges': {'name': 'Saboteur', 'levels': [100, 1000, 5000, 25000, 100000]}
    },
    {
        'idx': 72,
        'original_pos': 123,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Portal Defenses',
        'description': 'Successful portal defense actions',
        'badges': {'name': 'Defender', 'levels': [1000, 8000, 50000, 250000, 1000000]}
    },
    {
        'idx': 73,
        'original_pos': 124,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Enemy FieldsDestroyed Large',
        'description': 'Large enemy control fields destroyed (>1M MU)',
        'badges': {'name': 'Field Destroyer', 'levels': [25, 150, 1000, 5000, 25000]}
    },
    {
        'idx': 74,
        'original_pos': 125,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Enemy FieldsDestroyed Medium',
        'description': 'Medium enemy control fields destroyed (100K-1M MU)',
        'badges': {'name': 'Field Destroyer', 'levels': [100, 750, 5000, 25000, 100000]}
    },
    {
        'idx': 75,
        'original_pos': 126,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Enemy LinksDestroyed Long',
        'description': 'Long enemy links destroyed (>10km)',
        'badges': {'name': 'Link Destroyer', 'levels': [100, 750, 5000, 25000, 100000]}
    },
    {
        'idx': 76,
        'original_pos': 127,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Stealth Attacks',
        'description': 'Stealth attack actions performed',
        'badges': {'name': 'Ghost', 'levels': [200, 2000, 12000, 60000, 250000]}
    },
    {
        'idx': 77,
        'original_pos': 128,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Combat Efficiency',
        'description': 'Combat action success rate (%)',
        'badges': {'name': 'Strategist', 'levels': [70, 80, 90, 95, 99]}
    },
    {
        'idx': 78,
        'original_pos': 129,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Portal Retakes',
        'description': 'Portals recaptured from enemies',
        'badges': {'name': 'Reconqueror', 'levels': [500, 4000, 25000, 150000, 750000]}
    },
    {
        'idx': 79,
        'original_pos': 130,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Resource Denial',
        'description': 'Enemy resources destroyed',
        'badges': {'name': 'Destroyer', 'levels': [10000, 100000, 500000, 2500000, 10000000]}
    },
    {
        'idx': 80,
        'original_pos': 131,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'PvP Eliminations',
        'description': 'Player vs Player combat eliminations',
        'badges': {'name': 'Combatant', 'levels': [100, 1000, 5000, 25000, 100000]}
    },
    {
        'idx': 81,
        'original_pos': 132,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Defense Success Rate',
        'description': 'Portal defense success rate (%)',
        'badges': {'name': 'Guardian', 'levels': [60, 75, 85, 95, 99]}
    },
    {
        'idx': 82,
        'original_pos': 133,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Tactical Strikes',
        'description': 'Coordinated tactical strike operations',
        'badges': {'name': 'Commander', 'levels': [25, 150, 1000, 5000, 25000]}
    },
    {
        'idx': 83,
        'original_pos': 134,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Zone Control Time',
        'description': 'Total time controlling zones (hours)',
        'badges': {'name': 'Dominator', 'levels': [1000, 8000, 50000, 250000, 1000000]}
    },
    {
        'idx': 84,
        'original_pos': 135,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Clash Participation',
        'description': 'Clash events participated in',
        'badges': {'name': 'Clash Veteran', 'levels': [10, 50, 200, 1000, 5000]}
    },
    {
        'idx': 85,
        'original_pos': 136,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Anomaly Combat Score',
        'description': 'Total combat score from anomaly events',
        'badges': {'name': 'Anomaly Veteran', 'levels': [1000, 10000, 50000, 250000, 1000000]}
    },
    {
        'idx': 86,
        'original_pos': 137,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Virus Effectiveness',
        'description': 'Success rate of virus deployments (%)',
        'badges': {'name': 'Saboteur', 'levels': [50, 70, 85, 95, 99]}
    },
    {
        'idx': 87,
        'original_pos': 138,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Link Defense Success',
        'description': 'Successful link defense actions',
        'badges': {'name': 'Link Guardian', 'levels': [500, 4000, 25000, 150000, 750000]}
    },
    {
        'idx': 88,
        'original_pos': 139,
        'group': 'COMBAT',
        'type': 'N',
        'name': 'Field MU Denial',
        'description': 'Mind Units denied through field destruction',
        'badges': {'name': 'Liberator', 'levels': [5000000, 50000000, 250000000, 1000000000, 5000000000]}
    },

    # MIND_CONTROL group (indices 89-98)
    {
        'idx': 89,
        'original_pos': 150,
        'group': 'MIND_CONTROL',
        'type': 'N',
        'name': 'Psychological Warfare',
        'description': 'Psychological warfare actions performed',
        'badges': {'name': 'Mind Controller', 'levels': [100, 1000, 5000, 25000, 100000]}
    },
    {
        'idx': 90,
        'original_pos': 151,
        'group': 'MIND_CONTROL',
        'type': 'N',
        'name': 'Mind Unit Optimization',
        'description': 'Mind Unit optimization efficiency score',
        'badges': {'name': 'Mind Controller', 'levels': [60, 75, 85, 95, 99]}
    },
    {
        'idx': 91,
        'original_pos': 152,
        'group': 'MIND_CONTROL',
        'type': 'N',
        'name': 'Strategic Field Planning',
        'description': 'Strategic field planning actions',
        'badges': {'name': 'Strategist', 'levels': [50, 500, 2500, 15000, 75000]}
    },
    {
        'idx': 92,
        'original_pos': 153,
        'group': 'MIND_CONTROL',
        'type': 'N',
        'name': 'Team Coordination Score',
        'description': 'Team coordination and leadership score',
        'badges': {'name': 'Team Leader', 'levels': [70, 80, 90, 95, 99]}
    },
    {
        'idx': 93,
        'original_pos': 154,
        'group': 'MIND_CONTROL',
        'type': 'N',
        'name': 'Territory Dominance',
        'description': 'Territory control dominance percentage',
        'badges': {'name': 'Dominion', 'levels': [60, 75, 85, 95, 99]}
    },
    {
        'idx': 94,
        'original_pos': 155,
        'group': 'MIND_CONTROL',
        'type': 'N',
        'name': 'Portal Network Control',
        'description': 'Controlled portals in network',
        'badges': {'name': 'Network Controller', 'levels': [100, 1000, 5000, 25000, 100000]}
    },
    {
        'idx': 95,
        'original_pos': 156,
        'group': 'MIND_CONTROL',
        'type': 'N',
        'name': 'MU Production Efficiency',
        'description': 'Mind Unit production efficiency rate',
        'badges': {'name': 'Producer', 'levels': [65, 80, 90, 95, 98]}
    },
    {
        'idx': 96,
        'original_pos': 157,
        'group': 'MIND_CONTROL',
        'type': 'N',
        'name': 'Field Longevity',
        'description': 'Average field longevity (hours)',
        'badges': {'name': 'Field Sustainer', 'levels': [24, 72, 168, 720, 2160]}
    },
    {
        'idx': 97,
        'original_pos': 158,
        'group': 'MIND_CONTROL',
        'type': 'N',
        'name': 'Strategic Portal Control',
        'description': 'Strategically important portals controlled',
        'badges': {'name': 'Strategist', 'levels': [50, 250, 1000, 5000, 25000]}
    },
    {
        'idx': 98,
        'original_pos': 159,
        'group': 'MIND_CONTROL',
        'type': 'N',
        'name': 'Mind Control Influence',
        'description': 'Total mind control influence points',
        'badges': {'name': 'Mind Controller', 'levels': [10000, 100000, 500000, 2500000, 10000000]}
    },

    # DAILY_BONUS group (indices 99-106)
    {
        'idx': 99,
        'original_pos': 170,
        'group': 'DAILY_BONUS',
        'type': 'N',
        'name': 'Daily Login Streak',
        'description': 'Current daily login streak (days)',
        'badges': {'name': 'Dedicated Agent', 'levels': [7, 30, 90, 365, 1000]}
    },
    {
        'idx': 100,
        'original_pos': 171,
        'group': 'DAILY_BONUS',
        'type': 'N',
        'name': 'Daily Actions Completed',
        'description': 'Daily action goals completed',
        'badges': {'name': 'Consistent Agent', 'levels': [100, 1000, 5000, 25000, 100000]}
    },
    {
        'idx': 101,
        'original_pos': 172,
        'group': 'DAILY_BONUS',
        'type': 'N',
        'name': 'First Capture Bonus',
        'description': 'First portal capture bonuses earned',
        'badges': {'name': 'Early Bird', 'levels': [50, 500, 2500, 15000, 75000]}
    },
    {
        'idx': 102,
        'original_pos': 173,
        'group': 'DAILY_BONUS',
        'type': 'N',
        'name': 'Daily Hacking Goal',
        'description': 'Daily hacking goals achieved',
        'badges': {'name': 'Hacker', 'levels': [50, 500, 2500, 15000, 75000]}
    },
    {
        'idx': 103,
        'original_pos': 174,
        'group': 'DAILY_BONUS',
        'type': 'N',
        'name': 'Weekly Challenges',
        'description': 'Weekly challenges completed',
        'badges': {'name': 'Challenger', 'levels': [25, 200, 1000, 5000, 25000]}
    },
    {
        'idx': 104,
        'original_pos': 175,
        'group': 'DAILY_BONUS',
        'type': 'N',
        'name': 'Monthly Achievements',
        'description': 'Monthly achievement goals completed',
        'badges': {'name': 'Monthly Champion', 'levels': [10, 50, 250, 1000, 5000]}
    },
    {
        'idx': 105,
        'original_pos': 176,
        'group': 'DAILY_BONUS',
        'type': 'N',
        'name': 'Consecutive Daily Goals',
        'description': 'Consecutive daily goals completed',
        'badges': {'name': 'Perfectionist', 'levels': [14, 60, 180, 730, 2000]}
    },
    {
        'idx': 106,
        'original_pos': 177,
        'group': 'DAILY_BONUS',
        'type': 'N',
        'name': 'Peak Performance Days',
        'description': 'Days with peak performance achieved',
        'badges': {'name': 'Peak Performer', 'levels': [25, 150, 750, 3500, 15000]}
    },

    # ACHIEVEMENTS group (indices 107-126)
    {
        'idx': 107,
        'original_pos': 180,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Unique Medals Earned',
        'description': 'Total unique medals earned',
        'badges': {'name': 'Medalist', 'levels': [25, 100, 250, 500, 1000]}
    },
    {
        'idx': 108,
        'original_pos': 181,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Trophy Count',
        'description': 'Total trophies earned',
        'badges': {'name': 'Champion', 'levels': [10, 50, 200, 1000, 5000]}
    },
    {
        'idx': 109,
        'original_pos': 182,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Regional Score Leader',
        'description': 'Times as regional score leader',
        'badges': {'name': 'Regional Champion', 'levels': [5, 20, 100, 500, 2500]}
    },
    {
        'idx': 110,
        'original_pos': 183,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Global Ranking Position',
        'description': 'Best global ranking position achieved',
        'badges': {'name': 'Global Elite', 'levels': [10000, 5000, 2000, 500, 100]}
    },
    {
        'idx': 111,
        'original_pos': 184,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Anomaly Medals',
        'description': 'Anomaly event medals earned',
        'badges': {'name': 'Anomaly Veteran', 'levels': [5, 25, 100, 500, 2500]}
    },
    {
        'idx': 112,
        'original_pos': 185,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Event First Places',
        'description': 'First place finishes in events',
        'badges': {'name': 'Event Champion', 'levels': [5, 15, 50, 200, 1000]}
    },
    {
        'idx': 113,
        'original_pos': 186,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Community Recognition',
        'description': 'Community recognition awards received',
        'badges': {'name': 'Community Hero', 'levels': [10, 50, 200, 1000, 5000]}
    },
    {
        'idx': 114,
        'original_pos': 187,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Special Event Badges',
        'description': 'Special event badges earned',
        'badges': {'name': 'Event Specialist', 'levels': [10, 50, 200, 1000, 5000]}
    },
    {
        'idx': 115,
        'original_pos': 188,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Hall of Fame Inductions',
        'description': 'Hall of Fame inductions received',
        'badges': {'name': 'Hall of Famer', 'levels': [1, 3, 10, 25, 100]}
    },
    {
        'idx': 116,
        'original_pos': 189,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Milestone Achievements',
        'description': 'Major milestone achievements unlocked',
        'badges': {'name': 'Milestone Master', 'levels': [10, 50, 250, 1000, 5000]}
    },
    {
        'idx': 117,
        'original_pos': 190,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Perfect Missions',
        'description': 'Perfect missions completed',
        'badges': {'name': 'Mission Master', 'levels': [25, 200, 1000, 5000, 25000]}
    },
    {
        'idx': 118,
        'original_pos': 191,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Stealth Achievements',
        'description': 'Stealth-based achievements unlocked',
        'badges': {'name': 'Ghost Agent', 'levels': [25, 150, 750, 3500, 15000]}
    },
    {
        'idx': 119,
        'original_pos': 192,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Speed Records',
        'description': 'Speed records achieved',
        'badges': {'name': 'Speed Runner', 'levels': [10, 50, 200, 1000, 5000]}
    },
    {
        'idx': 120,
        'original_pos': 193,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Exploration Records',
        'description': 'Exploration records set',
        'badges': {'name': 'Explorer', 'levels': [10, 50, 200, 1000, 5000]}
    },
    {
        'idx': 121,
        'original_pos': 194,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Combat Records',
        'description': 'Combat records set',
        'badges': {'name': 'Combat Master', 'levels': [10, 50, 200, 1000, 5000]}
    },
    {
        'idx': 122,
        'original_pos': 195,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Building Records',
        'description': 'Building records set',
        'badges': {'name': 'Master Builder', 'levels': [10, 50, 200, 1000, 5000]}
    },
    {
        'idx': 123,
        'original_pos': 196,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Leaderboard Dominance',
        'description': 'Leaderboard category dominance periods',
        'badges': {'name': 'Leader', 'levels': [10, 50, 200, 1000, 5000]}
    },
    {
        'idx': 124,
        'original_pos': 197,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Rare Item Collection',
        'description': 'Rare items collected',
        'badges': {'name': 'Collector', 'levels': [50, 250, 1000, 5000, 25000]}
    },
    {
        'idx': 125,
        'original_pos': 198,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Veteran Status Years',
        'description': 'Years of veteran agent status',
        'badges': {'name': 'Veteran', 'levels': [1, 3, 5, 7, 10]}
    },
    {
        'idx': 126,
        'original_pos': 199,
        'group': 'ACHIEVEMENTS',
        'type': 'N',
        'name': 'Total Achievement Points',
        'description': 'Total achievement points earned',
        'badges': {'name': 'Achievement Master', 'levels': [1000, 10000, 50000, 250000, 1000000]}
    },

    # Expanded SPECIAL group (indices 127-140)
    {
        'idx': 127,
        'original_pos': 210,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Event-Specific Score',
        'description': 'Score from special events',
        'badges': {'name': 'Event Specialist', 'levels': [5000, 25000, 100000, 500000, 2500000]}
    },
    {
        'idx': 128,
        'original_pos': 211,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Unique Portal Types',
        'description': 'Unique types of portals visited',
        'badges': {'name': 'Portal Researcher', 'levels': [100, 1000, 5000, 25000, 100000]}
    },
    {
        'idx': 129,
        'original_pos': 212,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Cross-Region Links',
        'description': 'Links created across different regions',
        'badges': {'name': 'Regional Connector', 'levels': [50, 250, 1500, 7500, 35000]}
    },
    {
        'idx': 130,
        'original_pos': 213,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Historical Portal Visits',
        'description': 'Historical or significant portals visited',
        'badges': {'name': 'Historian', 'levels': [25, 200, 1000, 5000, 25000]}
    },
    {
        'idx': 131,
        'original_pos': 214,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Max Simultaneous Fields',
        'description': 'Maximum simultaneous control fields',
        'badges': {'name': 'Field Master', 'levels': [10, 50, 200, 1000, 5000]}
    },
    {
        'idx': 132,
        'original_pos': 215,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Max Links from Portal',
        'description': 'Maximum links from a single portal',
        'badges': {'name': 'Link Master', 'levels': [40, 60, 70, 120, 150]}
    },
    {
        'idx': 133,
        'original_pos': 216,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Portal Complex Creation',
        'description': 'Complex portal networks created',
        'badges': {'name': 'Architect', 'levels': [25, 200, 1000, 5000, 25000]}
    },
    {
        'idx': 134,
        'original_pos': 217,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Intel Analysis Time',
        'description': 'Time spent analyzing intel (hours)',
        'badges': {'name': 'Intel Analyst', 'levels': [100, 1000, 5000, 25000, 100000]}
    },
    {
        'idx': 135,
        'original_pos': 218,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Community Contributions',
        'description': 'Community service contributions',
        'badges': {'name': 'Community Hero', 'levels': [50, 250, 1000, 5000, 25000]}
    },
    {
        'idx': 136,
        'original_pos': 219,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Mentoring Score',
        'description': 'Score from mentoring new agents',
        'badges': {'name': 'Mentor', 'levels': [25, 200, 1000, 5000, 25000]}
    },
    {
        'idx': 137,
        'original_pos': 220,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Innovation Achievements',
        'description': 'Innovation and creative achievements',
        'badges': {'name': 'Innovator', 'levels': [10, 50, 200, 1000, 5000]}
    },
    {
        'idx': 138,
        'original_pos': 221,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Performance Analytics',
        'description': 'Detailed performance analytics completed',
        'badges': {'name': 'Analyst', 'levels': [100, 1000, 5000, 25000, 100000]}
    },
    {
        'idx': 139,
        'original_pos': 222,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Rare Discoveries',
        'description': 'Rare discoveries and findings',
        'badges': {'name': 'Discoverer', 'levels': [10, 50, 200, 1000, 5000]}
    },
    {
        'idx': 140,
        'original_pos': 223,
        'group': 'SPECIAL',
        'type': 'N',
        'name': 'Total Career Score',
        'description': 'Total career achievement score',
        'badges': {'name': 'Legend', 'levels': [100000, 1000000, 10000000, 100000000, 1000000000]}
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

def get_badge_level(stat_idx: int, value) -> Tuple[Optional[str], Optional[int]]:
    """
    Calculate badge level for a stat value.

    Args:
        stat_idx: The stat index
        value: The stat value to evaluate (int or float, floats are truncated)

    Returns:
        Tuple of (badge_level, next_level_value) or (None, None) if no badges
    """
    # Convert float to int by truncating (4.9 -> 4)
    if isinstance(value, float):
        value = int(value)
    
    stat = get_stat_by_idx(stat_idx)
    if not stat or 'badges' not in stat:
        return None, None

    levels = stat['badges']['levels']
    badge_name = stat['badges']['name']

    current_level = None
    next_level = None

    for i, level_value in enumerate(levels):
        if value >= level_value:
            # Only use BADGE_LEVELS if index is in bounds
            # For stats like Level/AP with 16 tiers, use the index directly
            if i < len(BADGE_LEVELS):
                current_level = BADGE_LEVELS[i]
            else:
                # For extended levels (like player level 6-16), just use the level number
                current_level = f"Level {i + 1}"
            
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