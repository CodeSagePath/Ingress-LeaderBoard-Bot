# Ingress Prime Stats Reference

This comprehensive reference documents all 140+ statistics tracked by the Ingress Prime Leaderboard Bot, organized by category with badge level requirements and explanations.

## Table of Contents

- [Badge System](#badge-system)
- [Header Statistics](#header-statistics)
- [Discovery Stats](#discovery-stats)
- [Building Stats](#building-stats)
- [Collaboration Stats](#collaboration-stats)
- [Combat Stats](#combat-stats)
- [Mind Control Stats](#mind-control-stats)
- [Daily Bonus Stats](#daily-bonus-stats)
- [Achievement Stats](#achievement-stats)
- [Special Stats](#special-stats)
- [Quick Reference Table](#quick-reference-table)

---

## Badge System

Ingress Prime uses a 5-tier badge system for most statistics:

| Badge | Color | Description |
|-------|-------|-------------|
| **Bronze** | 🟫 | Entry level achievement |
| **Silver** | ⬜ | Intermediate progress |
| **Gold** | 🟨 | Advanced achievement |
| **Platinum** | ⬜ | Expert level |
| **Onyx** | ⚫ | Master level achievement |

Each stat has specific threshold values for each badge level, detailed in the sections below.

---

## Header Statistics

These are the core identifying statistics at the beginning of every stats submission.

### Agent Information

| Index | Stat | Type | Description |
|-------|------|------|-------------|
| 0 | Time Span | String | Period covered (ALL TIME, MONTHLY, WEEKLY, DAILY) |
| 1 | Agent Name | String | Your Ingress agent name |
| 2 | Agent Faction | String | Enlightened or Resistance |
| 3 | Date (yyyy-mm-dd) | String | Date of stats recording |
| 4 | Time (hh:mm:ss) | String | Time of stats recording |

### Core Progress Stats

| Index | Stat | Type | Description | Badge Levels |
|-------|------|------|-------------|--------------|
| 5 | Level | Numeric | Current agent level (1-16) | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 |
| 6 | Lifetime AP | Numeric | Total Access Points earned | 100K, 500K, 1M, 2.5M, 5M, 10M, 20M, 40M, 80M, 160M, 320M, 640M, 1.28B, 2.56B, 5.12B, 10B |
| 7 | Current AP | Numeric | Current AP balance | N/A |

---

## Discovery Stats

Statistics related to exploring and discovering the game world.

| Index | Stat | Description | Badge Levels | Tips |
|-------|------|-------------|--------------|------|
| 8 | Unique Portals Visited | Number of unique portals you've visited | 100, 1K, 2K, 10K, 30K | **Explorer Badge** - Visit new areas regularly |
| 9 | Portals Discovered | Total portals you've discovered | 100, 1K, 2K, 10K, 30K | First to discover portals in new areas |
| 10 | Drone Hacks | Total hacks performed with your drone | 50, 500, 2K, 10K, 40K | **Drone Operator Badge** - Use drone daily |
| 11 | XM Collected | Total XM collected from all sources | 100K, 1M, 5M, 20M, 100M | **Recharger Badge** - Gather XM from portals |
| 12 | Keys Hacked | Total portal keys obtained | 500, 5K, 20K, 100K, 500K | **Hacker Badge** - Hack portals frequently |
| 13 | Distance Walked | Total distance walked while playing (km) | 100, 500, 2K, 10K, 40K | **Trekker Badge** - Walk between portals |

---

## Building Stats

Statistics related to creating and maintaining portal infrastructure.

| Index | Stat | Description | Badge Levels | Tips |
|-------|------|-------------|--------------|------|
| 14 | Resonators Deployed | Total resonators deployed on portals | 500, 5K, 20K, 100K, 400K | **Builder Badge** - Upgrade portals to level 8 |
| 15 | Links Created | Total links between portals | 100, 1K, 4K, 20K, 100K | **Connector Badge** - Create strategic links |
| 16 | Control Fields Created | Total control fields created | 50, 500, 2K, 10K, 50K | **Mind Controller Badge** - Create large fields |
| 17 | MU Captured | Total Mind Units captured by your fields | 100K, 1M, 10M, 100M, 1B | **Liberator Badge** - Create dense fields in populated areas |
| 18 | Mods Deployed | Total portal mods deployed | 100, 1K, 4K, 20K, 100K | **Engineer Badge** - Keep portals well-modded |

---

## Collaboration Stats

Statistics related to working with other agents and team activities.

| Index | Stat | Description | Badge Levels | Tips |
|-------|------|-------------|--------------|------|
| 19 | Unique Missions Completed | Number of different missions completed | 10, 100, 500, 2K, 5K | **Pioneer Badge** - Explore different mission areas |
| 20 | XM Recharged | Total XM recharged into portals | 100K, 1M, 5M, 20M, 100M | **Recharger Badge** - Recharge friendly portals |
| 21 | Portals Captured | Total enemy portals captured | 100, 1K, 4K, 20K, 100K | **Guardian Hunter Badge** - Flip enemy portals |
| 22 | Max Times Hacked | Total maximum hack streaks achieved | 500, 5K, 20K, 100K, 500K | **Hacker Badge** - Maintain hack streaks |

---

## Combat Stats

Statistics related to destroying enemy infrastructure and direct confrontation.

| Index | Stat | Description | Badge Levels | Tips |
|-------|------|-------------|--------------|------|
| 23 | Resonators Destroyed | Total enemy resonators destroyed | 500, 5K, 20K, 100K, 400K | **Destroyer Badge** - Attack enemy portals aggressively |
| 24 | Portals Neutralized | Total enemy portals completely neutralized | 100, 1K, 4K, 20K, 100K | **Destroyer Badge** - Clear enemy strongholds |
| 25 | Enemy Links Destroyed | Total enemy links destroyed | 100, 1K, 4K, 20K, 100K | **Destroyer Badge** - Break enemy fields efficiently |
| 26 | Enemy Control Fields Destroyed | Total enemy control fields destroyed | 50, 500, 2K, 10K, 50K | **Destroyer Badge** - Target large enemy fields |
| 27 | XM Collected from Enemy | Total XM gained from destroying enemy portals | 100K, 1M, 5M, 20M, 100M | **Destroyer Badge** - Profit from destruction |

---

## Mind Control Stats

Advanced statistics related to field creation and control mechanics.

| Index | Stat | Description | Badge Levels | Tips |
|-------|------|-------------|--------------|------|
| 28 | Hacks | Total portal hacks (friendly and enemy) | 500, 5K, 20K, 100K, 500K | **Hacker Badge** - Hack frequently for gear and AP |
| 29 | Longest Link | Length of longest link created (km) | Varies | Create strategic long-distance links |
| 30 | Largest Field | Largest control field created (MU) | Varies | Target high-population areas |
| 31 | Time Played | Total time spent playing (days) | Varies | Consistent daily activity |
| 32 | Unique Portals Captured | Unique portals captured from enemies | 100, 1K, 4K, 20K, 100K | **Pioneer Badge** - Explore diverse areas |

---

## Daily Bonus Stats

Statistics related to daily and recurring bonuses.

| Index | Stat | Description | Badge Levels | Tips |
|-------|------|-------------|--------------|------|
| 33 | First Hack Captures | Portals captured on first hack | Varies | Hack unknown portals for bonus AP |
| 34 | First Link Links | Links created on first link attempt | Varies | Create links immediately after capture |
| 35 | First Field Fields | Fields created on first field attempt | Varies | Complete triangles quickly |
| 36 | Capture Streak Days | Consecutive days with portal captures | Varies | Maintain daily activity |
| 37 | Hacking Streak Days | Consecutive days with successful hacks | Varies | Hack at least one portal daily |

---

## Achievement Stats

Special achievement-based statistics.

| Index | Stat | Description | Badge Levels | Tips |
|-------|------|-------------|--------------|------|
| 38 | Missions Completed | Total missions of all types completed | 10, 100, 500, 2K, 5K | **Pioneer Badge** - Complete missions regularly |
| 39 | Seer Points | Points earned from Portal Seer submissions | 100, 1K, 5K, 25K, 100K | Submit new portals via Seer |
| 40 | Recursed Agent | Number of times you've recursed | 1, 2, 3, 4, 5 | Reach level 16 and recurse |
| 41 | Battle Trophies | Battle trophies earned from events | Varies | Participate in Anomaly events |
| 42 | Oldest Portal | Age of oldest portal you've captured | Varies | Find and maintain historic portals |

---

## Special Stats

Additional tracked statistics for comprehensive gameplay analysis.

| Index | Stat | Description | Badge Levels | Tips |
|-------|------|-------------|--------------|------|
| 43-99 | Various Stats | Additional gameplay metrics | Varies | Diverse gameplay activities |
| 100+ | Extended Stats | Advanced metrics and rare achievements | Varies | Expert-level activities |

---

## Quick Reference Table

### Most Important Stats for Leaderboards

| Category | Key Stats | Index | Badge Focus |
|----------|-----------|-------|-------------|
| **Overall Progress** | Lifetime AP | 6 | AP Level Badge |
| **Exploration** | Unique Portals Visited | 8 | Explorer Badge |
| **Building** | Links Created | 15 | Connector Badge |
| **Building** | Control Fields Created | 16 | Mind Controller Badge |
| **Collaboration** | XM Recharged | 20 | Recharger Badge |
| **Combat** | Resonators Destroyed | 23 | Destroyer Badge |
| **Activity** | Hacks | 28 | Hacker Badge |
| **Mobility** | Distance Walked | 13 | Trekker Badge |

### Badge Progression Requirements

#### Explorer (Discovery)
- **Bronze:** 100 unique portals
- **Silver:** 1,000 unique portals
- **Gold:** 2,000 unique portals
- **Platinum:** 10,000 unique portals
- **Onyx:** 30,000 unique portals

#### Builder (Building)
- **Bronze:** 500 resonators deployed
- **Silver:** 5,000 resonators deployed
- **Gold:** 20,000 resonators deployed
- **Platinum:** 100,000 resonators deployed
- **Onyx:** 400,000 resonators deployed

#### Connector (Building)
- **Bronze:** 100 links created
- **Silver:** 1,000 links created
- **Gold:** 4,000 links created
- **Platinum:** 20,000 links created
- **Onyx:** 100,000 links created

#### Mind Controller (Building)
- **Bronze:** 50 control fields created
- **Silver:** 500 control fields created
- **Gold:** 2,000 control fields created
- **Platinum:** 10,000 control fields created
- **Onyx:** 50,000 control fields created

#### Hacker (Discovery/Combat)
- **Bronze:** 500 hacks
- **Silver:** 5,000 hacks
- **Gold:** 20,000 hacks
- **Platinum:** 100,000 hacks
- **Onyx:** 500,000 hacks

#### Destroyer (Combat)
- **Bronze:** 100 portals neutralized
- **Silver:** 1,000 portals neutralized
- **Gold:** 4,000 portals neutralized
- **Platinum:** 20,000 portals neutralized
- **Onyx:** 100,000 portals neutralized

#### Recharger (Collaboration)
- **Bronze:** 100,000 XM recharged
- **Silver:** 1,000,000 XM recharged
- **Gold:** 5,000,000 XM recharged
- **Platinum:** 20,000,000 XM recharged
- **Onyx:** 100,000,000 XM recharged

#### Trekker (Discovery)
- **Bronze:** 100 km walked
- **Silver:** 500 km walked
- **Gold:** 2,000 km walked
- **Platinum:** 10,000 km walked
- **Onyx:** 40,000 km walked

#### Pioneer (Collaboration)
- **Bronze:** 10 unique missions
- **Silver:** 100 unique missions
- **Gold:** 500 unique missions
- **Platinum:** 2,000 unique missions
- **Onyx:** 5,000 unique missions

---

## Progress Tracking Tips

### Daily Goals
- **Hack:** At least 100 portals (Hacker badge progress)
- **Walk:** 5-10 km between portals (Trekker badge progress)
- **Recharge:** 50,000 XM into friendly portals (Recharger badge progress)
- **Deploy:** 50 resonators (Builder badge progress)

### Weekly Goals
- **Create:** 20 links and 10 control fields (Connector/Mind Controller badges)
- **Explore:** Visit 50 new unique portals (Explorer badge progress)
- **Destroy:** Neutralize 10 enemy portals (Destroyer badge progress)
- **Complete:** 5 unique missions (Pioneer badge progress)

### Monthly Goals
- **AP Gain:** 1,000,000 lifetime AP increase
- **Fields:** Create 100 control fields
- **Links:** Establish 200 links
- **Distance:** Walk 200 km total

### Badge Focus Strategies

#### For Explorer Badge
1. Plan routes through new neighborhoods
2. Use public transport to reach distant areas
3. Join field trips with other agents
4. Focus on rural areas with undiscovered portals

#### For Builder Badges
1. Upgrade low-level portals in your area
2. Focus on resonator deployment (8 resonators per portal)
3. Rebuild destroyed portals immediately
4. Work in teams to deploy efficiently

#### For Connector/Mind Controller Badges
1. Plan strategic link routes
2. Create large triangles for maximum MU
3. Use Jarvis/ADA flip cards to enable field creation
4. Coordinate with faction for large field operations

#### For Destroyer Badge
1. Focus on heavily clustered enemy portals
2. Use high-powered XMP bursters
5. Target enemy links and fields efficiently
6. Work in teams for maximum destruction

---

## Statistics Glossary

**AP (Access Points):** Experience points used for leveling up

**MU (Mind Units):** Measure of population controlled by your fields

**XM (Exotic Matter):** Energy used for all agent actions

**Resonators:** Power sources that strengthen portals (levels 1-8)

**Links:** Connections between portals that enable field creation

**Control Fields:** Triangular areas created by three linked portals

**Mods:** Portal modifications that provide various bonuses

**Hacking:** Action to acquire items, AP, and keys from portals

**Neutralizing:** Destroying all resonators on an enemy portal

**Capturing:** Converting a neutral or enemy portal to your faction

**Recursion:** Restarting from level 1 after reaching level 16

---

## Data Usage in Leaderboards

The bot tracks all statistics but prioritizes certain ones for leaderboards:

### Primary Leaderboard Stats
- **Lifetime AP (6):** Overall progress indicator
- **Unique Portals Visited (8):** Exploration achievement
- **Links Created (15):** Building contribution
- **Control Fields Created (16):** Field creation skill
- **XM Recharged (20):** Team collaboration
- **Hacks (28):** Overall activity level
- **Distance Walked (13):** Physical activity

### Progress-Based Leaderboards
The bot also tracks **improvement over time** for:
- Monthly progress (last 30 days)
- Weekly progress (last 7 days)
- Agent-to-agent progress comparisons

### Faction Comparisons
All stats are tracked separately for:
- **Enlightened** (Green faction)
- **Resistance** (Blue faction)
- **Combined** (All agents)

---

## Tips for Stat Improvement

### General Strategy
1. **Balance** different types of activities for well-rounded stats
2. **Consistency** is key - regular daily activity adds up
3. **Teamwork** accelerates progress in many areas
4. **Planning** efficient routes maximizes multiple stats simultaneously

### Efficient Multi-Stat Activities
- **Field Trips:** Combine exploration (8), distance (13), and building (14-18)
- **OP Days:** Focus on building (14-16) and MU capture (17)
- **Destroy Missions:** Target combat stats (23-26) while clearing areas
- **Mission Tours:** Build unique missions (38) while exploring (8)

### Seasonal Events
- **Anomalies:** Battle trophies and special achievements
- **First Saturdays:** Community building events
- **Mission Days:** Special mission creation and completion
- **IFS (First Saturdays):** Portal capture and linking events

---

This reference provides a comprehensive overview of all Ingress Prime statistics tracked by the bot. Use it to plan your gameplay strategy and work towards specific badge goals!