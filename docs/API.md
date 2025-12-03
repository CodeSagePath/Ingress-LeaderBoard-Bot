# Ingress Prime Leaderboard Bot - API Documentation

This document provides comprehensive API documentation for the core modules of the Ingress Prime Leaderboard Bot.

## Table of Contents

- [Stats Parser API](#stats-parser-api)
- [Database API](#database-api)
- [Progress Tracking API](#progress-tracking-api)
- [Leaderboard Generator API](#leaderboard-generator-api)
- [Stats Configuration API](#stats-configuration-api)

---

## Stats Parser API

**Module:** `src/parsers/stats_parser.py`
**Class:** `StatsParser`

The Stats Parser handles parsing of Ingress Prime statistics from both tab-separated and space-separated formats.

### `__init__()`

**Description:** Initialize the StatsParser with default configuration.

**Returns:** `StatsParser` instance

```python
parser = StatsParser()
```

### `parse(stats_text: str) -> Dict`

**Description:** Main parsing entry point that handles both tab-separated and space-separated formats.

**Parameters:**
- `stats_text` (str): Raw stats text copied from Ingress Prime

**Returns:** `Dict` containing:
- **Success case:** Parsed stats dictionary with metadata
- **Error case:** `{'error': str, 'error_code': int}`

**Error Codes:**
- `1`: Invalid stats format
- `2`: Insufficient data lines
- `3`: Invalid tabulated format
- `4`: Not ALL TIME stats
- `5`: Not enough values in stats line
- `6`: Could not find date in stats
- `7`: Insufficient stats count
- `8`: Missing required stat index
- `9`: Invalid faction
- `10`: Invalid numeric value
- `99`: General parsing error

**Example:**
```python
parser = StatsParser()
result = parser.parse(stats_text_from_telegram)

if 'error' in result:
    print(f"Error {result['error_code']}: {result['error']}")
else:
    print(f"Parsed {result['stats_count']} stats for {result[1]['value']}")
```

### `clean_input(text: str) -> str`

**Description:** Clean and normalize input text by removing quotes and normalizing whitespace.

**Parameters:**
- `text` (str): Raw input text

**Returns:** `str` - Cleaned and normalized text

**Example:**
```python
cleaned = parser.clean_input('  "Time Span\tAgent Name\t"  ')
# Returns: 'Time Span Agent Name'
```

### `is_valid_stats(text: str) -> bool`

**Description:** Validate that text starts with recognized stats header.

**Parameters:**
- `text` (str): Text to validate

**Returns:** `bool` - True if valid stats format, False otherwise

**Valid Headers:**
- `'Time Span\tAgent Name\tAgent Faction\tDate'`
- `'Time Span Agent Name Agent Faction Date'`
- `'Time Span Agent Name Agent Faction'`

### `parse_tabulated(stats_text: str) -> Dict`

**Description:** Parse tab-separated stats format (typically from mobile copy).

**Parameters:**
- `stats_text` (str): Tab-separated stats text

**Returns:** `Dict` - Parsed stats dictionary

**Validation:**
- Requires minimum 12 stats count
- Validates required fields (indices 1-4)
- Checks for "ALL TIME" in time span field
- Validates faction is "Enlightened" or "Resistance"

### `parse_telegram(stats_text: str) -> Dict`

**Description:** Parse space-separated stats format from Telegram.

**Parameters:**
- `stats_text` (str): Space-separated stats text

**Returns:** `Dict` - Parsed stats dictionary

**Special Handling:**
- Consolidates multi-word time spans
- Handles quoted agent names
- Detects date positions automatically
- Processes date format annotations

### `get_stat_summary(parsed_data: Dict) -> Dict`

**Description:** Extract summary information from parsed data.

**Parameters:**
- `parsed_data` (Dict): Output from `parse()` method

**Returns:** `Dict` containing:
- `agent_name`: Agent name from stat index 1
- `faction`: Faction from stat index 2
- `level`: Agent level from stat index 5 (as int)
- `lifetime_ap`: Lifetime AP from stat index 6 (as int)
- `valid_numeric_stats`: Count of valid numeric stats
- `warnings`: List of validation warnings

---

## Database API

**Module:** `src/database/stats_database.py`
**Class:** `StatsDatabase`

High-level interface for Ingress stats database operations using SQLAlchemy models.

### `__init__(db_connection: DatabaseConnection)`

**Description:** Initialize StatsDatabase with database connection.

**Parameters:**
- `db_connection` (DatabaseConnection): Database connection instance

### `save_stats(telegram_user_id: int, parsed_stats: Dict, user_info: Optional[Dict] = None) -> Dict[str, Any]`

**Description:** Save parsed stats to database with complete transaction handling.

**Parameters:**
- `telegram_user_id` (int): Telegram user ID
- `parsed_stats` (Dict): Parsed statistics dictionary from StatsParser
- `user_info` (Optional[Dict]): Telegram user information (username, first_name, etc.)

**Returns:** `Dict` with success status and metadata:
- **Success:** `{'success': True, 'submission_id': int, 'agent_name': str, ...}`
- **Duplicate:** `{'success': False, 'error': str, 'duplicate': True, ...}`

**Features:**
- Creates user and agent records if needed
- Detects and records faction changes
- Validates data integrity
- Creates individual stat records
- Generates progress snapshots
- Prevents duplicate submissions

**Example:**
```python
db = StatsDatabase(db_connection)
result = db.save_stats(telegram_user_id, parsed_stats, user_info)

if result['success']:
    print(f"Saved {result['stats_count']} stats for {result['agent_name']}")
    if result['faction_changed']:
        print(f"Faction changed to {result['faction']}")
else:
    if result.get('duplicate'):
        print("Stats already submitted")
    else:
        print(f"Error: {result['error']}")
```

### `get_agent_history(agent_name: str, stat_idx: Optional[int] = None, limit: int = 10) -> List[Dict]`

**Description:** Get submission history for an agent.

**Parameters:**
- `agent_name` (str): Agent name to search for
- `stat_idx` (Optional[int]): Specific stat index to filter by
- `limit` (int): Maximum number of submissions to return

**Returns:** `List[Dict]` - List of submission dictionaries

**Entry Structure:**
```python
{
    'submission_id': int,
    'agent_name': str,
    'submission_date': str,  # ISO format
    'submission_time': str,  # ISO format
    'level': int,
    'lifetime_ap': int,
    'current_ap': int,
    'xm_collected': int,
    'stats_type': str,
    'processed_at': str,
    'stat_value': int,  # Only if stat_idx provided
    'stat_name': str,   # Only if stat_idx provided
    'stats': {...}      # All stats if stat_idx not provided
}
```

### `get_agent_latest_stats(agent_name: str) -> Optional[Dict]`

**Description:** Get the latest stats submission for an agent.

**Parameters:**
- `agent_name` (str): Agent name

**Returns:** `Optional[Dict]` - Latest submission data or None if not found

**Example:**
```python
latest = db.get_agent_latest_stats('AgentName')
if latest:
    print(f"Level: {latest['level']}, AP: {latest['lifetime_ap']}")
else:
    print("Agent not found")
```

### `get_leaderboard_data(stat_idx: int, faction: Optional[str] = None, period: str = 'all_time', limit: int = 20) -> List[Dict]`

**Description:** Get leaderboard data for a specific stat.

**Parameters:**
- `stat_idx` (int): Stat index for leaderboard
- `faction` (Optional[str]): Faction filter ('Enlightened' or 'Resistance')
- `period` (str): Period filter ('all_time', 'monthly', 'weekly')
- `limit` (int): Maximum entries to return

**Returns:** `List[Dict]` - Leaderboard entries

**Entry Structure:**
```python
{
    'rank': int,
    'agent_name': str,
    'faction': str,
    'level': int,
    'stat_name': str,
    'stat_value': int,
    'stat_type': str,
    'submission_date': str,
    'stats_type': str
}
```

### `get_user_agents(telegram_user_id: int) -> List[Dict]`

**Description:** Get all agents associated with a Telegram user.

**Parameters:**
- `telegram_user_id` (int): Telegram user ID

**Returns:** `List[Dict]` - List of agent dictionaries

### `get_database_stats() -> Dict`

**Description:** Get overall database statistics.

**Returns:** `Dict` containing:
```python
{
    'users': int,           # Active users
    'agents': int,          # Active agents
    'submissions': int,     # Total submissions
    'individual_stats': int, # Total stat records
    'factions': {
        'Enlightened': int,
        'Resistance': int
    }
}
```

---

## Progress Tracking API

**Module:** `src/features/progress.py`
**Class:** `ProgressTracker`

Comprehensive progress analysis system for tracking agent improvement over time.

### `__init__(session=None)`

**Description:** Initialize ProgressTracker with optional database session.

**Parameters:**
- `session` (Optional[Session]): SQLAlchemy session or None to create new one

### `calculate_progress(agent_name: str, days: int = 30) -> Dict`

**Description:** Calculate progress for an agent over specified days.

**Parameters:**
- `agent_name` (str): Name of the Ingress agent
- `days` (int): Number of days to look back (default: 30)

**Returns:** `Dict` containing:
- **Success:** Comprehensive progress data with agent info and progress stats
- **Error:** `{'error': str}`

**Key Stats Tracked:** `[6, 8, 11, 13, 14, 15, 16, 17, 20, 28]`
- 6: Lifetime AP
- 8: Unique Portals Visited
- 11: XM Collected
- 13: Distance Walked
- 14: Resonators Deployed
- 15: Links Created
- 16: Control Fields Created
- 17: Links Destroyed
- 20: XM Recharged
- 28: Hacks

**Example:**
```python
tracker = ProgressTracker()
progress = tracker.calculate_progress('AgentName', 30)

if 'error' not in progress:
    print(f"Progress for {progress['agent_name']} ({progress['faction']}):")
    for stat_idx, stat_info in progress['progress'].items():
        improvement = stat_info.get('improvement', 0)
        if improvement > 0:
            print(f"  Stat {stat_idx}: +{improvement}")
```

### `calculate_progress_for_stat(stat_idx: int, days: int = 30, faction: Optional[str] = None) -> List[Dict]`

**Description:** Calculate progress for all agents for a specific stat.

**Parameters:**
- `stat_idx` (int): Index of the stat to analyze
- `days` (int): Number of days to look back
- `faction` (Optional[str]): Faction filter

**Returns:** `List[Dict]` - Progress entries sorted by improvement (descending)

**Entry Structure:**
```python
{
    'rank': int,
    'agent_name': str,
    'agent_id': int,
    'faction': str,
    'level': int,
    'stat_idx': int,
    'first_value': int,
    'last_value': int,
    'progress': int,
    'progress_rate': float,
    'snapshot_count': int
}
```

### `format_progress_report(progress_data: Dict, agent_name: str, days: int = 30) -> str`

**Description:** Format progress data into a human-readable Telegram message.

**Parameters:**
- `progress_data` (Dict): Progress data from `calculate_progress()`
- `agent_name` (str): Name of the agent
- `days` (int): Number of days period

**Returns:** `str` - Formatted HTML/Markdown message for Telegram

**Features:**
- Faction-specific emojis (💚 for Enlightened, 💙 for Resistance)
- Top 10 improvements with progress rates
- Summary statistics
- Error handling and fallback messages

### `get_progress_leaderboard(stat_idx: int, days: int = 30, limit: int = 20, faction: Optional[str] = None) -> List[Dict]`

**Description:** Get progress leaderboard for a specific stat.

**Parameters:**
- `stat_idx` (int): Stat index for leaderboard
- `days` (int): Number of days to look back
- `limit` (int): Maximum entries to return
- `faction` (Optional[str]): Faction filter

**Returns:** `List[Dict]` - Progress leaderboard entries

### `get_multi_stat_progress_leaderboard(stat_indices: List[int], days: int = 30, limit: int = 10) -> List[Dict]`

**Description:** Get progress leaderboard combining multiple stats.

**Parameters:**
- `stat_indices` (List[int]): List of stat indices to include
- `days` (int): Number of days to look back
- `limit` (int): Maximum results to return

**Returns:** `List[Dict]` - Agents with combined progress scores

**Features:**
- Combines improvement across multiple stats
- Identifies well-rounded agents
- Requires improvement in at least 50% of tracked stats

### `get_agent_progress_summary(agent_name: str) -> Dict`

**Description:** Get comprehensive progress summary across multiple periods.

**Parameters:**
- `agent_name` (str): Agent name

**Returns:** `Dict` containing progress data for 7, 30, and 90 day periods

**Structure:**
```python
{
    'agent_name': str,
    'agent_id': int,
    'faction': str,
    'level': int,
    'periods': {
        '7_days': {...},
        '30_days': {...},
        '90_days': {...}
    },
    'calculated_at': str
}
```

### `resolve_stat_reference(stat_ref: str) -> Optional[int]`

**Class Method** - Resolve stat reference (name or index) to stat index.

**Parameters:**
- `stat_ref` (str): Stat name ('ap', 'explorer') or index as string

**Returns:** `Optional[int]` - Stat index or None if not found

**Supported References:**
- `'ap'` → 6 (Lifetime AP)
- `'explorer'` → 8 (Unique Portals Visited)
- `'xm'` → 11 (XM Collected)
- `'trekker'` → 13 (Distance Walked)
- And more...

---

## Leaderboard Generator API

**Module:** `src/leaderboard/generator.py`
**Class:** `LeaderboardGenerator`

Generates leaderboards for different stats, time periods, and faction filters.

### `__init__(session: Session)`

**Description:** Initialize LeaderboardGenerator with database session.

**Parameters:**
- `session` (Session): SQLAlchemy session instance

### `generate(stat_idx: int, limit: int = 20, faction: Optional[str] = None, period: str = 'all_time', use_cache: bool = True) -> Dict`

**Description:** Generate leaderboard for a specific stat with caching.

**Parameters:**
- `stat_idx` (int): Index of the stat
- `limit` (int): Maximum entries to return
- `faction` (Optional[str]): Faction filter
- `period` (str): Time period ('all_time', 'monthly', 'weekly', 'daily')
- `use_cache` (bool): Whether to use cached results

**Returns:** `Dict` containing:
- **Success:** Leaderboard data with metadata and entries
- **Error:** `{'error': str}`

**Result Structure:**
```python
{
    'stat_idx': int,
    'stat_name': str,
    'stat_type': str,
    'period': str,
    'faction': Optional[str],
    'entries': [
        {
            'rank': int,
            'agent_name': str,
            'faction': str,
            'value': int,
            'submission_date': date,
            'level': int,
            'lifetime_ap': int,
            'badge_level': Optional[str]
        }
    ],
    'generated_at': str,
    'from_cache': bool,
    'total_entries': int
}
```

### `get_agent_rank(agent_id: int, stat_idx: int, period: str = 'all_time') -> Optional[Dict]`

**Description:** Get an agent's rank for a specific stat.

**Parameters:**
- `agent_id` (int): Database ID of the agent
- `stat_idx` (int): Index of the stat to check
- `period` (str): Time period for ranking

**Returns:** `Optional[Dict]` - Rank information or None

### `get_faction_summary(stat_idx: int) -> Dict`

**Description:** Get summary statistics by faction for a stat.

**Parameters:**
- `stat_idx` (int): Index of the stat to analyze

**Returns:** `Dict` with faction statistics:
```python
{
    'factions': {
        'Enlightened': {
            'agent_count': int,
            'avg_value': float,
            'min_value': int,
            'max_value': int,
            'total_value': int
        },
        'Resistance': {...}
    },
    'total_agents': int,
    'stat_idx': int,
    'calculated_at': str
}
```

### `clear_expired_cache() -> int`

**Description:** Remove expired cache entries.

**Returns:** `int` - Number of cache entries removed

---

## Stats Configuration API

**Module:** `src/config/stats_config.py`

Configuration module containing all 140+ stat definitions and helper functions.

### Constants

#### `STAT_GROUPS`
Dictionary mapping stat group codes to names:
```python
{
    'DIS': {'name': 'Discovery'},
    'BUI': {'name': 'Building'},
    'RES': {'name': 'Resource Gathering'},
    'COL': {'name': 'Collaboration'},
    'COM': {'name': 'Combat'},
    'MIN': {'name': 'Mind Control'},
    'DAY': {'name': 'Daily Bonus'},
    'ACH': {'name': 'Achievements'},
    'SPE': {'name': 'Special'}
}
```

#### `BADGE_LEVELS`
List of badge levels: `['Bronze', 'Silver', 'Gold', 'Platinum', 'Onyx']`

#### `STATS_DEFINITIONS`
List of 140+ stat definition dictionaries with structure:
```python
{
    'idx': int,              # Stat index
    'original_pos': int,     # Position in Ingress output
    'group': str,           # STAT_GROUPS code
    'type': str,            # 'N' for numeric, 'S' for string
    'name': str,            # Stat name
    'description': str      # Human-readable description
}
```

### Functions

#### `get_stat_by_idx(idx: int) -> Optional[Dict]`
Get stat definition by index.

#### `get_stat_by_name(name: str) -> Optional[Dict]`
Get stat definition by name (supports partial matching).

#### `get_badge_level(stat_idx: int, value: int) -> Tuple[str, int]`
Get badge level and progress percentage for a stat value.

#### `validate_faction(faction: str) -> bool`
Validate faction is 'Enlightened' or 'Resistance'.

#### `format_stat_value(value: int, stat_idx: int) -> str`
Format stat value with appropriate formatting (commas, units, etc.).

#### `get_leaderboard_stats() -> List[Dict]`
Get stats suitable for leaderboards (numeric, meaningful stats).

---

## Error Handling

All API methods follow consistent error handling patterns:

### Database Errors
- Wrapped in try-except blocks
- Logged with appropriate context
- Return error dictionaries or empty results

### Validation Errors
- Specific error codes and messages
- Input sanitization
- Business rule enforcement

### Performance Considerations
- Database connection pooling
- Query optimization with indexes
- Caching for expensive operations
- Pagination for large result sets

---

## Usage Examples

### Complete Stats Submission Workflow
```python
from src.parsers.stats_parser import StatsParser
from src.database.stats_database import StatsDatabase

# Parse stats
parser = StatsParser()
parsed = parser.parse(stats_text)

if 'error' not in parsed:
    # Save to database
    db = StatsDatabase(db_connection)
    result = db.save_stats(telegram_user_id, parsed, user_info)

    if result['success']:
        print(f"Saved stats for {result['agent_name']}")
    else:
        print(f"Save failed: {result['error']}")
```

### Progress Analysis
```python
from src.features.progress import ProgressTracker

tracker = ProgressTracker()
progress = tracker.calculate_progress('AgentName', 30)

if 'error' not in progress:
    report = tracker.format_progress_report(progress, 'AgentName', 30)
    # Send report to Telegram
```

### Leaderboard Generation
```python
from src.leaderboard.generator import LeaderboardGenerator

generator = LeaderboardGenerator(session)
leaderboard = generator.generate(
    stat_idx=6,  # Lifetime AP
    limit=20,
    faction='Enlightened',
    period='monthly'
)

# Format and send leaderboard
```

---

## Performance Notes

- **Caching:** Leaderboard results cached for 5 minutes by default
- **Database:** Uses connection pooling and efficient queries
- **Progress Tracking:** Leverages ProgressSnapshot table for performance
- **Parsing:** Handles both space and tab-separated formats efficiently

For detailed performance tuning, see the Development Guide.