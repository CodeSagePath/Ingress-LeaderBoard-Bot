# Ingress Leaderboard Bot - Database Tests

This directory contains comprehensive unit tests for the StatsDatabase class that handles Ingress Prime leaderboard operations.

## Test Coverage

The test suite covers all major StatsDatabase functionality:

### Core Database Operations
- **save_stats()**: Complete stats submission workflow
  - New user and agent creation
  - Duplicate submission detection
  - Faction change tracking
  - Data validation and error handling

### Retrieval Operations
- **get_agent_history()**: Agent submission history
  - Chronological ordering
  - Pagination with limit parameters
  - Non-existent agent handling

- **get_agent_latest_stats()**: Latest submission retrieval
  - Most recent stats per agent
  - Individual stat record fetching

- **get_leaderboard_data()**: Leaderboard generation
  - Stat ranking and ordering
  - Faction filtering (Enlightened/Resistance)
  - Performance for large datasets

### User Management
- **get_user_agents()**: User-agent relationships
  - Multi-agent user support
  - Active agent filtering

- **get_database_stats()**: Overall database statistics
  - User/agent/submission counts
  - Faction breakdown statistics

## Test Architecture

### Database Setup
- Uses **SQLite in-memory** for fast, isolated testing
- Fresh database per test method to ensure isolation
- Proper teardown with SQLAlchemy table dropping

### Data Generation
- **TestDataGenerator** class for realistic test data
- Valid stats structure with required fields:
  - 1: Agent Name
  - 2: Agent Faction
  - 3: Date
  - 4: Time
  - 5-140+: Various Ingress stats

### Mock Strategy
- Mock external dependencies where appropriate
- Real SQLAlchemy operations for core functionality
- Isolated test database per test case

## Running Tests

### Prerequisites
```bash
# Ensure you're in the project root
cd /home/codesagepath/Documents/TGBot/ingress_leaderboard

# Install dependencies (if not already installed)
pip install -r requirements.txt
```

### Run All Tests
```bash
# Run complete test suite
python -m pytest tests/test_database.py -v

# Or using unittest
python -m unittest tests.test_database -v
```

### Run Specific Test Categories
```bash
# Test stats saving functionality
python -m pytest tests/test_database.py::TestStatsDatabase::test_save_and_retrieve_stats -v

# Test retrieval operations
python -m pytest tests/test_database.py::TestStatsDatabase::test_agent_history_retrieval -v

# Test leaderboard generation
python -m pytest tests/test_database.py::TestStatsDatabase::test_leaderboard_data_generation -v
```

### Test Coverage Report
```bash
# Generate coverage report
python -m pytest tests/test_database.py --cov=src.database --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

## Test Data Structure

### Valid Submission Format
```python
{
    1: {'idx': 1, 'name': 'Agent Name', 'value': 'TestAgent', 'type': 'S'},
    2: {'idx': 2, 'name': 'Agent Faction', 'value': 'Enlightened', 'type': 'S'},
    3: {'idx': 3, 'name': 'Date', 'value': '2024-01-15', 'type': 'S'},
    4: {'idx': 4, 'name': 'Time', 'value': '10:30:00', 'type': 'S'},
    5: {'idx': 5, 'name': 'Level', 'value': '8', 'type': 'N'},
    6: {'idx': 6, 'name': 'Lifetime AP', 'value': '1000000', 'type': 'N'},
    # ... additional stats up to index 140+
}
```

### Required Header Fields
- **1**: Agent Name (string)
- **2**: Agent Faction ('Enlightened' or 'Resistance')
- **3**: Date (YYYY-MM-DD format)
- **4**: Time (HH:MM:SS format)

### Stats Types
- **S**: String values (names, dates, times)
- **N**: Numeric values (AP, counts, levels)

## Test Patterns

### Test Structure
```python
class TestStatsDatabase(unittest.TestCase):
    def setUp(self):
        # Create isolated SQLite test database
        # Initialize StatsDatabase with test connection
        # Create test data generator

    def test_specific_functionality(self):
        # Generate test data
        # Execute database operation
        # Verify expected results
        # Clean up database connection

    def tearDown(self):
        # Remove temporary database file
        # Close database connections
```

### Data Generation
```python
# Generate valid submission
parsed_stats = self.data_gen.generate_valid_submission('TestAgent', 'Enlightened')

# Generate edge cases
invalid_stats = self.data_gen.generate_submission_with_missing_fields()

# Test different scenarios
duplicate_stats = self.data_gen.generate_valid_submission('ExistingAgent', 'Resistance')
```

## Validation Testing

### Business Rules
- **Faction validation**: Only 'Enlightened' or 'Resistance' allowed
- **Level constraints**: Agent levels 1-16
- **AP consistency**: Current AP cannot exceed Lifetime AP
- **Required fields**: All header fields must be present

### Edge Cases
- **New users**: First-time submissions
- **Duplicate detection**: Identical submissions rejected
- **Invalid data**: Malformed stat structures
- **Missing fields**: Incomplete submissions
- **Level mismatches**: AP doesn't match level expectations

### Error Conditions
- **Database errors**: Connection failures, constraint violations
- **Validation errors**: Invalid stat values, missing required data
- **Format errors**: Wrong data types, malformed timestamps

## Performance Considerations

### Test Isolation
- Each test gets fresh database
- No state sharing between tests
- Proper cleanup prevents memory leaks

### Efficient Testing
- Use in-memory SQLite for speed
- Generate minimal realistic test data
- Mock expensive external operations

### Coverage Targets
- **Line coverage**: 95%+ for StatsDatabase class
- **Branch coverage**: 90%+ for conditional logic
- **Method coverage**: 100% for all public methods

## Integration Points

### Database Connection
- Tests use **SQLite** while production uses **PostgreSQL**
- Same SQLAlchemy ORM ensures compatibility
- Connection pooling and session management tested

### Data Validation
- Comprehensive validation of parsed stats
- Business rules enforcement
- Data integrity constraints

### External Dependencies
- Telegram bot integration (mocked)
- Stats parser integration (tested)
- User management system integration

## Troubleshooting

### Common Test Failures
1. **Import errors**: Check Python path and module structure
2. **Database errors**: Ensure temporary file permissions
3. **Data generation**: Verify TestDataGenerator is working correctly

### Debug Tips
```bash
# Run with verbose output
python -m pytest tests/test_database.py -v -s

# Stop on first failure for debugging
python -m pytest tests/test_database.py -x --pdb

# Run specific failing test
python -m pytest tests/test_database.py::TestStatsDatabase::test_failing_test -v
```

### Test Environment
- Ensure `/tmp` directory is writable for temporary databases
- Python 3.8+ required for SQLite in-memory databases
- Sufficient memory for test database creation and cleanup

This test suite provides comprehensive validation of the StatsDatabase class and ensures reliable operation of the Ingress Prime leaderboard bot's core data persistence functionality.