# Ingress Prime Leaderboard Bot

A Telegram bot for tracking and comparing Ingress Prime player statistics with comprehensive leaderboards and progress tracking.

## Features

- 📊 **Stats Parsing** - Parses both tab-separated and space-separated stats from Ingress Prime
- 🏆 **Multiple Leaderboards** - 25+ stat categories with different time periods
- 👤 **Personal Stats** - Track your progress and submission history
- 💚 **Faction Support** - Separate leaderboards for Enlightened and Resistance
- 📈 **Progress Tracking** - Monthly, weekly, and daily progress leaderboards
- 🏅 **Badge Levels** - Track badge progress for all major stats
- ⚡ **Performance** - Fast leaderboard generation with caching
- 🛡️ **Validation** - Comprehensive stats validation with helpful error messages

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ingress-leaderboard-bot.git
cd ingress-leaderboard-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Required settings:
- `TELEGRAM_BOT_TOKEN` - Get from [@BotFather](https://t.me/botfather)
- `DB_PASSWORD` - PostgreSQL database password

### 3. Database Setup

Create a PostgreSQL database:
```sql
CREATE DATABASE ingress_leaderboard;
CREATE USER ingress_bot WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ingress_leaderboard TO ingress_bot;
```

### 4. Run the Bot

```bash
python main.py
```

## Commands

### Core Commands
- `/start` - Welcome message and getting started guide
- `/help` - Detailed help with all features
- `/submit` - Instructions for submitting stats
- `/leaderboard` - Browse leaderboard categories
- `/mystats` - View your personal stats and progress

### Stats Submission

Simply copy your **ALL TIME** stats from Ingress Prime and paste them in chat:

1. Open Ingress Prime 📱
2. Go to your Agent Profile 👤
3. Tap on "ALL TIME" stats 📊
4. Copy the stats text 📋
5. Paste them in the chat with the bot 💬

### Leaderboard Categories

**Core Stats:**
- 🏆 Lifetime AP (Access Points)
- 🔍 Unique Portals Visited (Explorer badge)
- 🔗 Links Created (Connector badge)
- 🧠 Control Fields Created (Mind Controller badge)
- ⚡ XM Recharged (Recharger badge)
- 🔨 Resonators Deployed (Builder badge)
- 👟 Distance Walked (Trekker badge)
- 💬 Hacks (Hacker badge)

**Progress-Based:**
- 📈 Monthly progress (last 30 days)
- 📅 Weekly progress (last 7 days)
- 📊 Daily submissions

**Faction-Specific:**
- 💚 Enlightened leaderboards
- 💙 Resistance leaderboards
- 🌐 All factions combined

## Architecture

### Project Structure
```
ingress-leaderboard-bot/
├── src/
│   ├── bot/              # Telegram bot handlers and commands
│   ├── parsers/           # Stats parsing and validation
│   ├── database/          # Database models and connections
│   ├── leaderboard/        # Leaderboard generation and formatting
│   ├── config/            # Settings and stats configuration
│   └── utils/             # Utilities (logging, helpers)
├── tests/                  # Unit tests
├── data/                   # Sample data and migrations
├── main.py                 # Bot entry point
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── README.md               # This file
```

### Key Components

**Stats Parser** (`src/parsers/stats_parser.py`)
- Handles both tab-separated and space-separated formats
- Validates stats completeness and correctness
- Supports all 140+ Ingress statistics
- Comprehensive error handling

**Database Models** (`src/database/models.py`)
- SQLAlchemy models for users, agents, submissions
- Optimized queries for leaderboard generation
- Support for progress tracking and caching
- Faction change tracking

**Leaderboard Generator** (`src/leaderboard/generator.py`)
- Multiple time periods (all-time, monthly, weekly, daily)
- Faction filtering and caching
- Performance-optimized queries
- Badge level calculations

**Bot Handlers** (`src/bot/handlers.py`)
- Comprehensive command handling
- Interactive inline keyboards
- Rich HTML formatting with emojis
- Error handling and user guidance

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|-----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | - | Telegram bot token from @BotFather |
| `DB_HOST` | ❌ | localhost | PostgreSQL database host |
| `DB_PORT` | ❌ | 5432 | PostgreSQL database port |
| `DB_NAME` | ❌ | ingress_leaderboard | Database name |
| `DB_USER` | ❌ | postgres | Database username |
| `DB_PASSWORD` | ✅ | - | Database password |
| `BOT_DEBUG` | ❌ | false | Enable debug logging |
| `LEADERBOARD_CACHE_TIMEOUT` | ❌ | 300 | Cache timeout in seconds |

### Telegram Bot Setup

1. Create a new bot with [@BotFather](https://t.me/botfather)
2. Get the bot token (starts with numbers like `123456789:ABC...`)
3. Set the bot to private if needed (recommended for testing)
4. Add the bot token to your `.env` file

### Database Setup

**PostgreSQL (Recommended)**
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE ingress_leaderboard;
CREATE USER ingress_bot WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ingress_leaderboard TO ingress_bot;
```

**Alternative Databases**
- SQLite (for development)
- Docker PostgreSQL (for production)
- Cloud PostgreSQL (Heroku, Railway, etc.)

## Development

### 🐳 Local Development with Docker (Recommended)

The easiest way to set up a local development environment is using Docker Compose. This includes:

- 🤖 **Bot service** with hot reload
- 🗄️ **PostgreSQL database** with sample data
- 🔧 **Adminer** for database management
- 📊 **Development tools** and utilities

#### Quick Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ingress-leaderboard-bot.git
cd ingress-leaderboard-bot

# 2. Run the development setup script
./scripts/dev-setup.sh

# 3. Edit .env file with your bot token
nano .env
# Add your TELEGRAM_BOT_TOKEN from @BotFather

# 4. Start the development environment
docker-compose -f docker-compose.dev.yml up
```

#### Development Services

When you start the development environment, these services are available:

- **🤖 Bot**: `http://localhost:8443` (webhook port)
- **🗄️ Database**: `localhost:5432`
- **🔧 Adminer**: `http://localhost:8080` (database admin interface)

#### Development Commands

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up

# Start in detached mode
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# View specific service logs
./scripts/logs.sh bot -f  # Follow bot logs
./scripts/logs.sh db -n 100  # Show last 100 DB logs

# Stop services
docker-compose -f docker-compose.dev.yml down

# Restart services
docker-compose -f docker-compose.dev.yml restart

# Access bot container shell
docker-compose -f docker-compose.dev.yml exec bot bash

# Access database directly
docker-compose -f docker-compose.dev.yml exec db psql -U postgres -d ingress_leaderboard_dev

# Seed database with sample data
docker-compose -f docker-compose.dev.yml exec bot python scripts/db-seed.py
```

#### File Structure for Development

```
ingress-leaderboard-bot/
├── docker-compose.dev.yml      # Development Docker configuration
├── .env.dev                    # Development environment template
├── scripts/                    # Development utilities
│   ├── dev-setup.sh           # Environment setup script
│   ├── logs.sh                # Log viewing utility
│   ├── db-init.sql            # Database initialization
│   └── db-seed.py             # Sample data generator
├── data/                       # Development data (persisted)
│   ├── logs/
│   ├── uploads/
│   └── backups/
└── src/                        # Source code (mounted as volume)
```

#### Development Features

- **🔄 Hot Reload**: Code changes are automatically reflected
- **📊 Database Admin**: Adminer available at `http://localhost:8080`
- **🐛 Debug Mode**: Enhanced logging and error reporting
- **📝 Sample Data**: Pre-populated database for testing
- **🛠️ Development Tools**: Additional debugging and monitoring tools

#### Environment Configuration

The development environment uses these default settings:

```bash
# Development Database (configured in docker-compose.dev.yml)
DB_HOST=db
DB_PORT=5432
DB_NAME=ingress_leaderboard_dev
DB_USER=postgres
DB_PASSWORD=dev_password

# Development Settings
DEBUG=true
LOG_LEVEL=DEBUG
BOT_DEBUG=true
LEADERBOARD_CACHE_TIMEOUT=60  # Shorter cache for testing
BOT_RATE_LIMIT_PER_MINUTE=30  # Relaxed rate limiting
```

### Running in Development Mode (Manual)

If you prefer to run without Docker:

```bash
# 1. Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up database manually
# (See Database Setup section below)

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Enable debug mode
export BOT_DEBUG=true
export LOG_LEVEL=DEBUG

# 6. Run migrations (if using Alembic)
alembic upgrade head

# 7. Run bot
python main.py
```

### Running Tests

#### 1. Automated Tests (Unit Tests)
Deeply tests database logic, validation, and parsing.

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_database.py
```

#### 2. Manual/Interactive Testing
Test the bot logic without connecting to Telegram (safe for dev).

```bash
# Run the interactive simulator
python test_bot_interactively.py
```
This script mimics a user sending stats to the bot and shows you the response.

### Code Style

The project follows these conventions:
- Python type hints for all functions
- Comprehensive docstrings
- Error handling with detailed messages
- Database transactions and connection pooling
- Structured logging with performance monitoring

## Deployment to Termux

This bot is designed to run on **Termux (Android)** using a shared server configuration.

### Quick Setup

1.  **Set up the Server Manager:**
    Follow the guide in the `termux-server-config` repository.
    
2.  **Deploy this Bot:**
    Clone this into `~/projects/ingress_bot` on your phone.

3.  **Start:**
    Run `bash ~/projects/termux-server-config/start-bots.sh`

For full instructions, see the **[Termux Deployment Manual](https://github.com/CodeSagePath/termux-server-config)** in your server config repo.

## Stats Format

The bot accepts stats in two formats:

### Space-Separated (from Telegram)
```
Time Span Agent Name Agent Faction Date (yyyy-mm-dd) Time (hh:mm:ss) Level Lifetime AP Current AP
ALL TIME TestAgent Enlightened 2024-01-15 10:30:00 16 50000000 45000000 ...
```

### Tab-Separated
```
Time Span	Agent Name	Agent Faction	Date (yyyy-mm-dd)	Time (hh:mm:ss)	Level	Lifetime AP	Current AP
ALL TIME	TestAgent	Enlightened	2024-01-15	10:30:00	16	50000000	45000000	...
```

**Important:**
- Only **ALL TIME** stats are accepted
- Complete stats text must be copied
- Agent name must match exactly
- Faction must be "Enlightened" or "Resistance"

## Troubleshooting

### Common Issues

**"This doesn't look like Ingress stats"**
- Ensure you're copying ALL TIME stats
- Check that text starts with "Time Span"
- Copy the complete stats text

**"Invalid faction"**
- Make sure your faction is exactly "Enlightened" or "Resistance"
- Check for typos in the faction field

**"Database error"**
- Verify database connection settings
- Check if database is running
- Ensure database tables were created

**Bot doesn't respond**
- Check if bot token is valid
- Verify bot has internet access
- Check logs for error messages

### Getting Help

1. Check the logs: `tail -f bot.log`
2. Use `/help` in Telegram for guidance
3. Review this README for common issues
4. Open an issue on GitHub with error details

## Performance

### Optimization Features

- **Database indexing** - Optimized for leaderboard queries
- **Caching** - Leaderboards cached for 5 minutes
- **Connection pooling** - Efficient database connections
- **Rate limiting** - Prevents spam and API abuse
- **Background tasks** - Async processing for better response times

### Scaling Considerations

- PostgreSQL recommended for production
- Configure cache timeout based on user activity
- Monitor database query performance
- Use webhooks for high-traffic deployments
- Consider read replicas for heavy leaderboard usage

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with tests
4. Commit changes: `git commit -m "Add feature"`
5. Push to branch: `git push origin feature-name`
6. Open a Pull Request

### Development Guidelines

- Follow existing code style and patterns
- Add comprehensive tests for new features
- Update documentation for any changes
- Use type hints throughout
- Include error handling for all external operations

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: support@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/ingress-leaderboard-bot/issues)
- 💬 Telegram: [@SupportBot](https://t.me/supportbot)

## Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram bot framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM and database toolkit
- [psycopg2](https://www.psycopg.org/docs/) - PostgreSQL adapter
- Ingress Prime community for feature requests and feedback

---

Made with ❤️ for the Ingress community