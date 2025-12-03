# Ingress Prime Leaderboard Bot - Developer Guide

This comprehensive guide is for developers who want to understand, extend, or contribute to the Ingress Prime Leaderboard Bot codebase.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Getting Started](#getting-started)
- [Code Organization](#code-organization)
- [Database Schema](#database-schema)
- [Bot Command System](#bot-command-system)
- [Stats Processing Pipeline](#stats-processing-pipeline)
- [Adding New Features](#adding-new-features)
- [Testing Guidelines](#testing-guidelines)
- [Deployment Guide](#deployment-guide)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Architecture Overview

The bot follows a modular, layered architecture designed for scalability and maintainability:

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram API                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  Bot Handlers                               │
│  (commands, callbacks, message processing)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Business Logic                               │
│  (progress tracking, leaderboard generation, stats parsing) │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│               Data Access Layer                             │
│      (database models, connection management, queries)       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Database                                    │
│            (PostgreSQL/SQLite)                              │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

1. **Bot Framework** (`src/bot/`)
   - Command handlers and message processing
   - Inline keyboard interactions
   - User management and authentication

2. **Stats Processing** (`src/parsers/`)
   - Ingress stats parsing and validation
   - Format detection and normalization
   - Error handling and user feedback

3. **Database Layer** (`src/database/`)
   - SQLAlchemy models and migrations
   - Connection pooling and transaction management
   - Health monitoring and caching

4. **Business Logic** (`src/features/`, `src/leaderboard/`)
   - Progress tracking algorithms
   - Leaderboard generation and caching
   - Analytics and reporting

5. **Configuration** (`src/config/`)
   - Stats definitions and badge levels
   - Environment settings and validation
   - Feature flags and tuning parameters

---

## Getting Started

### Prerequisites

- **Python 3.8+** with pip
- **PostgreSQL 12+** (recommended) or SQLite (development)
- **Git** for version control
- **Docker** (optional but recommended)

### Development Setup

#### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/ingress-leaderboard-bot.git
cd ingress-leaderboard-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configuration
```bash
# Copy environment template
cp .env.example .env
nano .env  # Add your configuration
```

**Required Environment Variables:**
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
DB_PASSWORD=your_database_password
```

**Optional Development Variables:**
```bash
BOT_DEBUG=true
LOG_LEVEL=DEBUG
LEADERBOARD_CACHE_TIMEOUT=60
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ingress_leaderboard_dev
DB_USER=postgres
```

#### 3. Database Setup
```bash
# Using Docker (recommended for development)
docker-compose -f docker-compose.dev.yml up -d db

# Or setup PostgreSQL manually
sudo -u postgres psql
CREATE DATABASE ingress_leaderboard_dev;
CREATE USER ingress_bot WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ingress_leaderboard_dev TO ingress_bot;
```

#### 4. Run Migrations
```bash
# Initialize database schema
alembic upgrade head
```

#### 5. Start Development Server
```bash
# Run bot in development mode
python main.py

# Or use Docker Compose
docker-compose -f docker-compose.dev.yml up bot
```

### Development Tools

#### IDE Configuration (VSCode)
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true
}
```

#### Pre-commit Hooks
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Code Organization

### Directory Structure

```
src/
├── bot/                    # Telegram bot interface
│   ├── handlers.py        # Command handlers (/start, /help, etc.)
│   ├── callbacks.py       # Inline keyboard callbacks
│   ├── progress_handlers.py # Progress-related commands
│   └── bot_framework.py   # Bot framework abstraction
├── parsers/               # Stats parsing and validation
│   ├── stats_parser.py    # Core parsing logic
│   ├── validator.py       # Stats validation
│   └── business_rules_validator.py # Advanced validation
├── database/              # Database layer
│   ├── models.py          # SQLAlchemy models
│   ├── connection.py      # Database connection management
│   ├── stats_database.py  # High-level database operations
│   ├── migrations.py      # Migration management
│   └── health_monitor.py  # Database health monitoring
├── features/              # Business logic modules
│   └── progress.py        # Progress tracking system
├── leaderboard/           # Leaderboard system
│   ├── generator.py       # Leaderboard generation
│   └── formatters.py      # Leaderboard formatting
├── config/                # Configuration
│   ├── settings.py        # Application settings
│   └── stats_config.py    # Stats definitions (140+ stats)
├── utils/                 # Utilities
│   └── logger.py          # Logging configuration
└── monitoring/            # Health and monitoring
    ├── health_checker.py  # Health endpoints
    └── metrics.py         # Prometheus metrics
```

### Design Patterns

#### 1. Repository Pattern
The database layer uses the Repository pattern for clean data access:

```python
class StatsDatabase:
    def save_stats(self, user_id: int, parsed_stats: Dict) -> Dict:
        """High-level interface for saving stats"""
        # Handles transactions, validation, business logic

    def get_leaderboard_data(self, stat_idx: int, filters: Dict) -> List[Dict]:
        """High-level interface for leaderboard data"""
        # Handles caching, optimization, formatting
```

#### 2. Strategy Pattern
Stats parsing uses different strategies for different formats:

```python
class StatsParser:
    def parse(self, stats_text: str) -> Dict:
        if '\t' in stats_text:
            return self.parse_tabulated(stats_text)
        else:
            return self.parse_telegram(stats_text)
```

#### 3. Factory Pattern
Bot handlers are created based on command types:

```python
# In handlers.py
def setup_handlers(application):
    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(CommandHandler('help', help_handler))
    application.add_handler(CommandHandler('leaderboard', leaderboard_handler))
```

#### 4. Observer Pattern
Progress tracking observes stats submissions and updates snapshots:

```python
# Automatic progress snapshot creation in StatsDatabase.save_stats()
self._create_progress_snapshots(session, agent.id, submission_date, parsed_stats)
```

### Code Style Guidelines

#### 1. Python Standards
- **Type hints** for all function signatures
- **Docstrings** following Google or NumPy style
- **PEP 8** compliance with Black formatting
- **Error handling** with specific exception types

#### 2. Function Design
```python
def calculate_leaderboard(
    stat_idx: int,
    limit: int = 20,
    faction: Optional[str] = None,
    period: str = 'all_time'
) -> List[Dict]:
    """
    Generate leaderboard for a specific statistic.

    Args:
        stat_idx: Index of the statistic
        limit: Maximum number of entries
        faction: Optional faction filter
        period: Time period for calculation

    Returns:
        List of leaderboard entries sorted by rank

    Raises:
        ValueError: If stat_idx is invalid
        DatabaseError: If database query fails
    """
```

#### 3. Class Design
```python
class ProgressTracker:
    """
    Progress tracking and analysis system.

    Handles calculation of agent progress over time periods,
    generates progress reports, and manages progress data.
    """

    KEY_STATS = [6, 8, 11, 13, 14, 15, 16, 17, 20, 28]

    def __init__(self, session: Optional[Session] = None):
        """Initialize with optional database session."""

    def calculate_progress(self, agent_name: str, days: int = 30) -> Dict:
        """Public method with clear input/output."""
```

---

## Database Schema

### Core Tables

#### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Agents Table
```sql
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    agent_name VARCHAR(255) UNIQUE NOT NULL,
    faction VARCHAR(20) CHECK (faction IN ('Enlightened', 'Resistance')),
    level INTEGER CHECK (level >= 1 AND level <= 16),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Stats Submissions Table
```sql
CREATE TABLE stats_submissions (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    submission_date DATE NOT NULL,
    submission_time TIME,
    stats_type VARCHAR(20) DEFAULT 'ALL TIME',
    level INTEGER,
    lifetime_ap BIGINT,
    current_ap BIGINT,
    xm_collected BIGINT,
    parser_version VARCHAR(20),
    submission_format VARCHAR(20),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_id, submission_date, submission_time)
);
```

#### Agent Stats Table
```sql
CREATE TABLE agent_stats (
    id SERIAL PRIMARY KEY,
    submission_id INTEGER REFERENCES stats_submissions(id),
    stat_idx INTEGER NOT NULL,
    stat_name VARCHAR(255),
    stat_value BIGINT,
    stat_type VARCHAR(10), -- 'N' for numeric, 'S' for string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(submission_id, stat_idx)
);
```

#### Progress Snapshots Table
```sql
CREATE TABLE progress_snapshots (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    snapshot_date DATE NOT NULL,
    stat_idx INTEGER NOT NULL,
    stat_value BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_id, snapshot_date, stat_idx)
);
```

#### Leaderboard Cache Table
```sql
CREATE TABLE leaderboard_cache (
    id SERIAL PRIMARY KEY,
    stat_idx INTEGER NOT NULL,
    stat_name VARCHAR(255),
    period VARCHAR(20) NOT NULL,
    faction VARCHAR(20),
    cache_data JSONB,
    cache_size INTEGER,
    min_value BIGINT,
    max_value BIGINT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stat_idx, period, faction)
);
```

#### Faction Changes Table
```sql
CREATE TABLE faction_changes (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    old_faction VARCHAR(20),
    new_faction VARCHAR(20),
    change_reason VARCHAR(100),
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submission_count_before INTEGER DEFAULT 0
);
```

### Database Indexes

```sql
-- Performance indexes
CREATE INDEX idx_agents_name ON agents(agent_name);
CREATE INDEX idx_agents_faction ON agents(faction) WHERE is_active = TRUE;
CREATE INDEX idx_stats_submissions_agent_date ON stats_submissions(agent_id, submission_date DESC);
CREATE INDEX idx_agent_stats_submission_stat ON agent_stats(submission_id, stat_idx);
CREATE INDEX idx_progress_snapshots_agent_date_stat ON progress_snapshots(agent_id, snapshot_date, stat_idx);
CREATE INDEX idx_leaderboard_cache_expires ON leaderboard_cache(expires_at);

-- Unique constraints for data integrity
CREATE UNIQUE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE UNIQUE INDEX idx_agents_name ON agents(agent_name) WHERE is_active = TRUE;
```

### Database Migrations

Use Alembic for database schema management:

```bash
# Create new migration
alembic revision --autogenerate -m "Add new feature table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## Bot Command System

### Command Handler Structure

Commands are organized into logical groups in `src/bot/handlers.py`:

```python
# Core commands
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""

# Stats commands
async def submit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /submit command"""

async def mystats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mystats command"""

# Leaderboard commands
async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /leaderboard command with interactive keyboard"""
```

### Message Handling Flow

```
User Message → Bot Framework → Command Router → Handler Function → Business Logic → Database → Response
```

#### 1. Message Reception
```python
# In main.py or bot_framework.py
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
```

#### 2. Stats Processing
```python
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages (stats submissions)"""

    # Parse stats
    parser = StatsParser()
    parsed_stats = parser.parse(update.message.text)

    if 'error' in parsed_stats:
        await update.message.reply_text(f"❌ {parsed_stats['error']}")
        return

    # Save to database
    db = StatsDatabase(get_db_connection())
    result = db.save_stats(update.effective_user.id, parsed_stats)

    # Send response
    await send_stats_submission_response(update, result)
```

### Inline Keyboard System

Interactive menus use Telegram's inline keyboards:

```python
# Leaderboard category selection
async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard category selection"""

    keyboard = [
        [InlineKeyboardButton("🏆 Lifetime AP", callback_data='lb_6')],
        [InlineKeyboardButton("🔍 Unique Portals", callback_data='lb_8')],
        [InlineKeyboardButton("🔗 Links Created", callback_data='lb_15')],
        [InlineKeyboardButton("🧠 Control Fields", callback_data='lb_16')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📊 Select leaderboard category:", reply_markup=reply_markup)

# Callback handling
async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leaderboard category selection"""

    query = update.callback_query
    await query.answer()

    # Parse callback data: "lb_6" means leaderboard for stat 6 (Lifetime AP)
    _, stat_idx = query.data.split('_')

    # Generate leaderboard
    generator = LeaderboardGenerator(get_db_session())
    leaderboard = generator.generate(int(stat_idx))

    # Format and send
    message = format_leaderboard_message(leaderboard)
    await query.edit_message_text(message, parse_mode='HTML')
```

---

## Stats Processing Pipeline

The stats processing pipeline handles parsing, validation, storage, and analysis:

### 1. Input Reception
```
Telegram Message → Text Content → Initial Validation
```

### 2. Format Detection
```python
def parse(self, stats_text: str) -> Dict:
    """Detect format and route to appropriate parser"""

    if '\t' in stats_text:
        return self.parse_tabulated(stats_text)
    else:
        return self.parse_telegram(stats_text)
```

### 3. Parsing and Validation
```python
# Tab-separated format parsing
def parse_tabulated(self, stats_text: str) -> Dict:
    """Parse tab-separated stats from mobile copy"""

    lines = stats_text.strip().split('\n')
    headers = lines[0].split('\t')
    values = lines[1].split('\t')

    # Validate structure
    if values[0] != 'ALL TIME':
        return {'error': 'Not ALL TIME stats', 'error_code': 4}

    # Map headers to stat definitions
    for i, (header, value) in enumerate(zip(headers, values)):
        stat_def = self._find_stat_by_name(header.strip())
        if stat_def:
            result[stat_def['idx']] = {
                'idx': stat_def['idx'],
                'value': value.strip(),
                'name': stat_def['name'],
                'type': stat_def['type']
            }
```

### 4. Business Rules Validation
```python
def _validate_required_fields(self, result: Dict) -> Optional[Dict]:
    """Validate required fields and business rules"""

    # Check required indices
    required_indices = [1, 2, 3, 4]  # agent name, faction, date, time
    for idx in required_indices:
        if idx not in result:
            return {'error': f'Missing required field index {idx}'}

    # Validate faction
    faction = result[2]['value']
    if faction not in ['Enlightened', 'Resistance']:
        return {'error': f'Invalid faction: {faction}'}

    # Validate numeric fields
    for key, stat in result.items():
        if isinstance(key, int) and stat.get('type') == 'N':
            try:
                int(stat['value'])
            except ValueError:
                return {'error': f'Invalid numeric value: {stat["name"]}'}
```

### 5. Database Storage
```python
def save_stats(self, telegram_user_id: int, parsed_stats: Dict) -> Dict:
    """Complete stats saving workflow"""

    with self.db.session_scope() as session:
        # Get or create user and agent
        user = self._get_or_create_user(session, telegram_user_id, user_info)
        agent = self._get_or_create_agent(session, user.id, agent_name, faction, level)

        # Check for duplicates
        existing = self._check_duplicate_submission(session, agent.id, date, time)
        if existing:
            return {'success': False, 'duplicate': True}

        # Create main submission record
        submission = StatsSubmission(...)
        session.add(submission)
        session.flush()  # Get submission ID

        # Create individual stat records
        stats_count = self._create_individual_stats(session, submission.id, parsed_stats)

        # Create progress snapshots
        self._create_progress_snapshots(session, agent.id, date, parsed_stats)

        return {'success': True, 'submission_id': submission.id, 'stats_count': stats_count}
```

### 6. Progress Tracking
```python
def _create_progress_snapshots(self, session, agent_id: int, snapshot_date: date, parsed_stats: Dict):
    """Create automatic progress snapshots for key stats"""

    # Track key stats for progress leaderboards
    key_stats = [6, 8, 11, 13, 14, 15, 16, 17, 20, 28]

    for stat_idx in key_stats:
        if stat_idx in parsed_stats:
            stat_data = parsed_stats[stat_idx]
            snapshot = ProgressSnapshot(
                agent_id=agent_id,
                snapshot_date=snapshot_date,
                stat_idx=stat_idx,
                stat_value=int(stat_data['value'].replace(',', ''))
            )
            session.add(snapshot)
```

---

## Adding New Features

### Adding a New Bot Command

#### 1. Create Handler Function
```python
# In src/bot/handlers.py or create new file
async def mynewcommand_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mynewcommand command"""

    # Validate arguments if needed
    if context.args:
        # Process command arguments
        param = context.args[0]
    else:
        await update.message.reply_text("Usage: /mynewcommand <parameter>")
        return

    # Execute business logic
    result = await process_my_feature(param)

    # Send response
    await update.message.reply_text(f"✅ Result: {result}")
```

#### 2. Register Command
```python
# In main.py or bot setup
application.add_handler(CommandHandler('mynewcommand', mynewcommand_handler))
```

#### 3. Update Help System
```python
# In help_handler
help_text += """
/mynewcommand - Description of my new command
"""
```

### Adding a New Stat to Track

#### 1. Update Stats Configuration
```python
# In src/config/stats_config.py
STATS_DEFINITIONS.append({
    'idx': 143,  # Next available index
    'original_pos': 143,
    'group': 'SPECIAL',
    'type': 'N',
    'name': 'My New Stat',
    'description': 'Description of what this stat measures',
    'badges': {
        'name': 'New Badge Name',
        'levels': [10, 100, 1000, 10000, 50000]
    }
})
```

#### 2. Update Progress Tracking
```python
# In src/features/progress.py
class ProgressTracker:
    # Add to KEY_PROGRESS_STATS if important for progress
    KEY_PROGRESS_STATS = [6, 8, 11, 13, 14, 15, 16, 17, 20, 28, 143]  # Add new stat

    # Add to STAT_MAPPINGS for user-friendly references
    STAT_MAPPINGS = {
        'mystat': 143,  # Add mapping
        # ... existing mappings
    }
```

#### 3. Create Migration
```bash
alembic revision --autogenerate -m "Add support for new stat tracking"
alembic upgrade head
```

### Adding a New Leaderboard Type

#### 1. Extend Leaderboard Generator
```python
# In src/leaderboard/generator.py
class LeaderboardGenerator:
    def generate_custom_leaderboard(self, custom_params: Dict) -> Dict:
        """Generate custom leaderboard based on specific criteria"""

        # Build custom query
        query = self.session.query(...)  # Your custom query

        # Execute and format results
        results = query.all()
        entries = [format_entry(entry) for entry in results]

        return {
            'entries': entries,
            'count': len(entries),
            'custom_data': custom_params
        }
```

#### 2. Add Command Handler
```python
async def custom_leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom leaderboard command"""

    generator = LeaderboardGenerator(get_db_session())
    leaderboard = generator.generate_custom_leaderboard({
        'param1': context.args[0] if context.args else None
    })

    message = format_custom_leaderboard(leaderboard)
    await update.message.reply_text(message)
```

### Adding Database Models

#### 1. Define SQLAlchemy Model
```python
# In src/database/models.py
class NewModel(Base):
    """New database table for custom feature"""
    __tablename__ = 'new_table'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    custom_field = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship('User', backref='new_records')
```

#### 2. Create Migration
```bash
alembic revision --autogenerate -m "Add new_table"
alembic upgrade head
```

#### 3. Add Database Operations
```python
# In src/database/stats_database.py or create new module
class CustomDatabase:
    def save_custom_data(self, user_id: int, data: Dict) -> bool:
        """Save custom data to database"""
        try:
            with self.db.session_scope() as session:
                record = NewModel(user_id=user_id, custom_field=data['value'])
                session.add(record)
                return True
        except Exception as e:
            logger.error(f"Error saving custom data: {e}")
            return False
```

---

## Testing Guidelines

### Test Structure

```
tests/
├── conftest.py             # Shared test fixtures and utilities
├── test_database.py        # Database operations tests
├── test_parsers.py         # Stats parsing tests
├── test_progress.py        # Progress tracking tests
├── test_stats_workflow.py  # End-to-end workflow tests
└── test_bot_commands.py    # Bot command integration tests
```

### Test Database Setup

```python
# tests/conftest.py
import pytest
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.connection import Base
from src.database.stats_database import StatsDatabase

@pytest.fixture
def test_db():
    """Create temporary test database"""
    # Use in-memory SQLite for tests
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()

@pytest.fixture
def stats_db(test_db):
    """Create StatsDatabase instance with test session"""
    from src.database.connection import DatabaseConnection
    mock_connection = type('MockConnection', (), {'session_scope': lambda self: test_db})()
    return StatsDatabase(mock_connection)
```

### Unit Testing Example

```python
# tests/test_parsers.py
import pytest
from src.parsers.stats_parser import StatsParser

class TestStatsParser:

    @pytest.fixture
    def parser(self):
        return StatsParser()

    def test_parse_telegram_format_success(self, parser):
        """Test successful parsing of telegram format"""
        stats_text = """Time Span Agent Name Agent Faction Date (yyyy-mm-dd) Time (hh:mm:ss) Level Lifetime AP Current AP
ALL TIME TestAgent Enlightened 2024-01-15 10:30:00 16 50000000 45000000"""

        result = parser.parse(stats_text)

        assert 'error' not in result
        assert result[1]['value'] == 'TestAgent'
        assert result[2]['value'] == 'Enlightened'
        assert result[5]['value'] == '16'

    def test_parse_invalid_faction(self, parser):
        """Test rejection of invalid faction"""
        stats_text = """Time Span Agent Name Agent Faction Date
ALL TIME TestAgent InvalidFaction 2024-01-15 10:30:00"""

        result = parser.parse(stats_text)

        assert 'error' in result
        assert result['error_code'] == 9  # Invalid faction error

    def test_parse_not_all_time(self, parser):
        """Test rejection of non-ALL TIME stats"""
        stats_text = """Time Span Agent Name Agent Faction Date
MONTHLY TestAgent Enlightened 2024-01-15 10:30:00"""

        result = parser.parse(stats_text)

        assert 'error' in result
        assert result['error_code'] == 4  # Not ALL TIME error
```

### Integration Testing Example

```python
# tests/test_stats_workflow.py
import pytest
from src.parsers.stats_parser import StatsParser
from src.database.stats_database import StatsDatabase

class TestStatsWorkflow:

    def test_complete_stats_submission_workflow(self, stats_db):
        """Test complete workflow from parsing to database storage"""

        # 1. Parse stats
        parser = StatsParser()
        stats_text = """Time Span Agent Name Agent Faction Date (yyyy-mm-dd) Time (hh:mm:ss) Level Lifetime AP Current AP
ALL TIME WorkflowTest Enlightened 2024-01-15 10:30:00 8 1000000 500000"""

        parsed_stats = parser.parse(stats_text)
        assert 'error' not in parsed_stats

        # 2. Save to database
        result = stats_db.save_stats(12345, parsed_stats)
        assert result['success'] is True
        assert result['agent_name'] == 'WorkflowTest'

        # 3. Retrieve and verify
        latest = stats_db.get_agent_latest_stats('WorkflowTest')
        assert latest is not None
        assert latest['lifetime_ap'] == 1000000
        assert latest['level'] == 8
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_database.py -v

# Run specific test method
pytest tests/test_parsers.py::TestStatsParser::test_parse_telegram_format_success -v
```

### Test Data Generation

```python
# tests/test_data.py
class TestDataGenerator:
    """Generate realistic test data"""

    def generate_valid_submission(self, agent_name='TestAgent', faction='Enlightened'):
        """Generate valid stats submission data"""
        return {
            1: {'idx': 1, 'name': 'Agent Name', 'value': agent_name, 'type': 'S'},
            2: {'idx': 2, 'name': 'Agent Faction', 'value': faction, 'type': 'S'},
            3: {'idx': 3, 'name': 'Date', 'value': '2024-01-15', 'type': 'S'},
            4: {'idx': 4, 'name': 'Time', 'value': '10:30:00', 'type': 'S'},
            5: {'idx': 5, 'name': 'Level', 'value': '8', 'type': 'N'},
            6: {'idx': 6, 'name': 'Lifetime AP', 'value': '1000000', 'type': 'N'},
            8: {'idx': 8, 'name': 'Unique Portals Visited', 'value': '500', 'type': 'N'},
        }

    def generate_telegram_stats_text(self, agent_name='TestAgent', faction='Enlightened'):
        """Generate realistic Telegram stats text"""
        return f"""Time Span Agent Name Agent Faction Date (yyyy-mm-dd) Time (hh:mm:ss) Level Lifetime AP Current AP XM Collected Unique Portals Visited Resonators Deployed
ALL TIME {agent_name} {faction} 2024-01-15 10:30:00 8 1000000 500000 2500000 500 1200"""
```

---

## Deployment Guide

### Production Environment Setup

#### 1. Environment Configuration
```bash
# Production .env file
TELEGRAM_BOT_TOKEN=production_bot_token
DB_HOST=your-production-db-host
DB_PORT=5432
DB_NAME=ingress_leaderboard_prod
DB_USER=ingress_bot
DB_PASSWORD=strong_production_password
BOT_DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production
```

#### 2. Database Setup
```sql
-- Production PostgreSQL setup
CREATE DATABASE ingress_leaderboard_prod;
CREATE USER ingress_bot WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE ingress_leaderboard_prod TO ingress_bot;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

#### 3. SSL Certificate
```bash
# Set up SSL for Telegram webhook
openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout key.pem -out cert.pem
```

### Docker Deployment

#### 1. Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

# Create non-root user
RUN useradd -m -u 1000 botuser
USER botuser

# Expose port for webhook (if needed)
EXPOSE 8443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Start command
CMD ["python", "main.py"]
```

#### 2. Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  bot:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - DB_HOST=postgres
      - DB_PASSWORD=${DB_PASSWORD}
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=ingress_leaderboard_prod
      - POSTGRES_USER=ingress_bot
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ingress_bot"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
```

### Cloud Deployment

#### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables
railway variables set TELEGRAM_BOT_TOKEN=your_token
railway variables set DB_PASSWORD=your_db_password
```

#### Heroku
```bash
# Create Heroku app
heroku create ingress-leaderboard-bot

# Set environment variables
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set DB_URL=your_database_url

# Deploy
git push heroku main
```

### Monitoring and Health Checks

#### Health Check Endpoint
```python
# src/monitoring/health_checker.py
from flask import Flask, jsonify
from src.database.health_monitor import DatabaseHealthMonitor

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Health check endpoint for load balancers"""

    try:
        db_health = DatabaseHealthMonitor.check_connection()
        return jsonify({
            'status': 'healthy',
            'database': db_health,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    # Return metrics in Prometheus format
    return generate_prometheus_metrics()
```

#### Log Monitoring
```python
# src/utils/logger.py
import logging
import logging.handlers

def setup_logging():
    """Configure production logging"""

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        'bot.log', maxBytes=10*1024*1024, backupCount=5
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(file_formatter)
    logger.addHandler(console_handler)
```

---

## Performance Optimization

### Database Optimization

#### 1. Query Optimization
```python
# Efficient leaderboard query with proper indexing
def get_optimized_leaderboard(self, stat_idx: int, limit: int = 20):
    """Optimized leaderboard query using subqueries"""

    # Use window functions for better performance
    query = """
    WITH latest_submissions AS (
        SELECT DISTINCT ON (agent_id) *
        FROM stats_submissions
        ORDER BY agent_id, submission_date DESC
    ),
    ranked_stats AS (
        SELECT
            a.agent_name,
            a.faction,
            as_.stat_value,
            RANK() OVER (ORDER BY as_.stat_value DESC) as rank
        FROM latest_submissions ls
        JOIN agent_stats as_ ON ls.id = as_.submission_id
        JOIN agents a ON ls.agent_id = a.id
        WHERE as_.stat_idx = %s
    )
    SELECT * FROM ranked_stats
    ORDER BY rank
    LIMIT %s
    """

    return self.session.execute(query, (stat_idx, limit)).fetchall()
```

#### 2. Connection Pooling
```python
# src/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

def create_optimized_connection(database_url: str):
    """Create database connection with optimized pooling"""

    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600
    )

    return engine
```

#### 3. Caching Strategy
```python
# src/leaderboard/generator.py
class LeaderboardGenerator:
    def __init__(self, session):
        self.session = session
        self.cache_timeout = 300  # 5 minutes

    def generate_with_cache(self, stat_idx: int, cache_key: str):
        """Generate leaderboard with intelligent caching"""

        # Check Redis cache first
        cached_result = redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)

        # Generate fresh leaderboard
        leaderboard = self.generate(stat_idx)

        # Cache with expiration
        redis_client.setex(
            cache_key,
            self.cache_timeout,
            json.dumps(leaderboard)
        )

        return leaderboard
```

### Memory Optimization

#### 1. Lazy Loading
```python
# Use generators for large result sets
def get_all_agents_progress(self, days: int = 30):
    """Generator that yields agent progress data"""

    query = self.session.query(ProgressSnapshot).filter(
        ProgressSnapshot.snapshot_date >= datetime.utcnow() - timedelta(days=days)
    ).yield_per(1000)  # Process 1000 records at a time

    for snapshot in query:
        yield snapshot
```

#### 2. Resource Management
```python
# Use context managers for resource cleanup
class ProgressTracker:
    def calculate_batch_progress(self, agent_names: List[str]) -> List[Dict]:
        """Process multiple agents efficiently"""

        results = []

        # Use session with proper cleanup
        with self.db.session_scope() as session:
            for agent_name in agent_names:
                try:
                    progress = self.calculate_progress_for_agent(session, agent_name)
                    results.append(progress)
                except Exception as e:
                    logger.error(f"Error calculating progress for {agent_name}: {e}")
                    continue

        return results
```

### Background Tasks

#### 1. Progress Calculation
```python
# src/tasks/background_tasks.py
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def update_progress_snapshots():
    """Background task to update progress snapshots"""

    with get_db_session() as session:
        # Process agents that haven't been updated recently
        agents = session.query(Agent).filter(
            Agent.updated_at < datetime.utcnow() - timedelta(hours=1)
        ).all()

        for agent in agents:
            try:
                # Calculate and save progress
                tracker = ProgressTracker(session)
                progress = tracker.calculate_progress(agent.agent_name, 30)
                await process_progress_result(agent, progress)
            except Exception as e:
                logger.error(f"Error updating progress for {agent.agent_name}: {e}")

# Schedule background task
scheduler.add_job(
    update_progress_snapshots,
    'interval',
    hours=1,
    id='progress_updates'
)
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```python
# Symptoms: Connection timeouts, pool exhaustion
# Solutions: Check connection string, increase pool size, verify network connectivity

def debug_database_connection():
    """Debug database connection issues"""

    try:
        # Test basic connection
        engine = create_engine(database_url)
        connection = engine.connect()
        connection.execute("SELECT 1")
        connection.close()
        print("✅ Database connection successful")

    except OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("Check:")
        print("- Database server is running")
        print("- Connection string is correct")
        print("- Network connectivity")
        print("- Firewall settings")
```

#### 2. Memory Issues
```python
# Symptoms: High memory usage, slow response times
# Solutions: Optimize queries, use pagination, implement caching

def diagnose_memory_issues():
    """Diagnose memory usage issues"""

    import psutil
    import tracemalloc

    # Start memory tracing
    tracemalloc.start()

    # Check current memory usage
    process = psutil.Process()
    memory_info = process.memory_info()

    print(f"RSS Memory: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS Memory: {memory_info.vms / 1024 / 1024:.2f} MB")

    # Get memory allocation snapshot
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    print("\nTop memory allocations:")
    for stat in top_stats[:10]:
        print(stat)
```

#### 3. Telegram Bot Issues
```python
# Symptoms: Bot not responding, webhook errors
# Solutions: Check bot token, webhook URL, SSL certificates

async def test_bot_connection():
    """Test bot connectivity"""

    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        bot_info = await bot.get_me()
        print(f"✅ Bot connected: @{bot_info.username}")

    except Exception as e:
        print(f"❌ Bot connection failed: {e}")
        print("Check:")
        print("- Bot token is correct")
        print("- Bot hasn't been blocked by Telegram")
        print("- Network connectivity to Telegram API")
```

### Performance Monitoring

#### 1. Response Time Monitoring
```python
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Log performance metrics
            logger.info(f"{func.__name__} executed in {execution_time:.2f}s")

            # Alert on slow performance
            if execution_time > 5.0:
                logger.warning(f"Slow execution detected for {func.__name__}: {execution_time:.2f}s")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f}s: {e}")
            raise

    return wrapper

# Usage
@monitor_performance
async def handle_leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leaderboard command with performance monitoring"""
    # Command implementation
    pass
```

#### 2. Database Performance Monitoring
```python
def monitor_database_performance():
    """Monitor database query performance"""

    # Enable query logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    # Monitor slow queries
    logger.info("Database performance monitoring enabled")
```

### Debug Mode

#### 1. Enable Debug Logging
```python
# Set environment variables
BOT_DEBUG=true
LOG_LEVEL=DEBUG

# Or programmatically
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. Development Tools
```python
# src/utils/debug.py
import asyncio
from pprint import pprint

async def debug_stats_parsing(stats_text: str):
    """Debug stats parsing with detailed output"""

    parser = StatsParser()

    print("🔍 Debug Stats Parsing")
    print("=" * 50)
    print(f"Input text:\n{stats_text}\n")

    result = parser.parse(stats_text)

    if 'error' in result:
        print(f"❌ Parsing failed: {result}")
    else:
        print("✅ Parsing successful:")
        pprint(result)

    return result

# Usage in development
if __name__ == "__main__":
    asyncio.run(debug_stats_parsing(your_stats_text))
```

---

## Contributing

### Development Workflow

#### 1. Fork and Clone
```bash
git clone https://github.com/yourusername/ingress-leaderboard-bot.git
cd ingress-leaderboard-bot
```

#### 2. Create Feature Branch
```bash
git checkout -b feature/my-new-feature
```

#### 3. Make Changes
- Follow code style guidelines
- Add tests for new functionality
- Update documentation

#### 4. Test Your Changes
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Check code style
black src/ tests/
pylint src/
```

#### 5. Commit Changes
```bash
git add .
git commit -m "Add my new feature

- Implement new leaderboard type
- Add comprehensive tests
- Update documentation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### 6. Push and Create Pull Request
```bash
git push origin feature/my-new-feature
# Create pull request on GitHub
```

### Code Review Guidelines

#### 1. Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are comprehensive and pass
- [ ] Documentation is updated
- [ ] No hardcoded secrets or configuration
- [ ] Error handling is appropriate
- [ ] Performance considerations addressed
- [ ] Security implications considered

#### 2. Review Process
1. **Automated Checks**: CI/CD pipeline runs tests and code quality checks
2. **Peer Review**: Another developer reviews the changes
3. **Testing**: Changes tested in development environment
4. **Deployment**: Merged and deployed to production

### Release Process

#### 1. Version Bumping
```bash
# Update version in setup.py or pyproject.toml
bump2version patch  # or minor, major
```

#### 2. Changelog
```markdown
# CHANGELOG.md

## [1.2.0] - 2024-01-15

### Added
- New progress tracking feature
- Custom leaderboard support

### Changed
- Improved database query performance
- Updated UI for better user experience

### Fixed
- Bug in stats parsing for special characters
- Memory leak in background tasks
```

#### 3. Release
```bash
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0
```

This comprehensive developer guide provides everything needed to understand, extend, and maintain the Ingress Prime Leaderboard Bot. Follow the patterns and guidelines outlined here to ensure high-quality contributions and smooth development workflows.