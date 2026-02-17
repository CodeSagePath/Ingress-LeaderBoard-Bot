# Log Monitoring Guide

This guide helps you monitor bot logs during testing and production to debug issues and track bot activity.

## Quick Start

### Monitor all logs in real-time
```bash
tail -f bot.log
```

### Monitor only errors
```bash
tail -f bot.log | grep ERROR
```

### Monitor test results
```bash
tail -f test_results.log
```

## Log File Locations

| Environment | Log File | Description |
|-------------|----------|-------------|
| Production | `bot.log` | Main bot activity log |
| Testing | `test_results.log` | Test execution log |
| Development | `dev_bot.log` | Development environment log |

Logs are rotated when they exceed 10MB, keeping up to 5 backup files.

## Real-time Log Monitoring

### Basic monitoring
```bash
# Follow log as it grows
tail -f bot.log

# Show last 100 lines and follow
tail -n 100 -f bot.log

# Follow with timestamps highlighted
tail -f bot.log | grep --color=auto '.*'
```

### Filter by log level
```bash
# Only ERROR level
tail -f bot.log | grep ERROR

# ERROR and WARNING only
tail -f bot.log | grep -E '(ERROR|WARNING)'

# Everything except DEBUG
tail -f bot.log | grep -v DEBUG
```

## Filter by Component

### Bot command logs
```bash
# All bot commands
tail -f bot.log | grep "src.bot"

# Specific commands
tail -f bot.log | grep "/start"
tail -f bot.log | grep "/leaderboard"
tail -f bot.log | grep "/mystats"
```

### Database logs
```bash
# All database activity
tail -f bot.log | grep "src.database"

# Database errors only
tail -f bot.log | grep "src.database" | grep ERROR
```

### Parser logs
```bash
# Stats parsing activity
tail -f bot.log | grep "src.parsers"

# Parsing errors
tail -f bot.log | grep "parsing" | grep ERROR
```

## Filter with Context

### Show context around matches
```bash
# 3 lines before and after
tail -f bot.log | grep -C 3 "ERROR"

# 5 lines before, 2 after
tail -f bot.log | grep -A 2 -B 5 "Stats submitted"

# Only show lines after match (until next match)
tail -f bot.log | grep -A 10 "User.*started"
```

## Common Log Patterns

### Stats submission flow
```bash
# Watch for complete submission flow
tail -f bot.log | grep -E '(Stats submitted|Parser|Database.*saved)'
```

### Error tracking
```bash
# All errors with context
tail -f bot.log | grep -C 5 ERROR

# Count errors by type
grep ERROR bot.log | awk '{print $5}' | sort | uniq -c
```

### User activity
```bash
# Track specific user (replace USER_ID)
tail -f bot.log | grep "USER_ID"

# All leaderboard requests
tail -f bot.log | grep "leaderboard"
```

### Performance monitoring
```bash
# Slow operations (>1s)
tail -f bot.log | grep "Slow query"

# Performance metrics
tail -f bot.log | grep "Performance:"
```

## Troubleshooting

### Bot not responding
```bash
# Check for startup errors
head -50 bot.log

# Check for recent errors
tail -100 bot.log | grep ERROR

# Check if bot is running
ps aux | grep python | grep bot
```

### Stats parsing failures
```bash
# Find parsing errors
grep "parsing.*error" bot.log

# View specific error with context
grep -B 10 -A 5 "Invalid stats format" bot.log
```

### Database issues
```bash
# Check database connection
tail -f bot.log | grep "Database.*connection"

# View database errors
grep "Database.*error" bot.log -i

# Check for slow queries
grep "Slow query" bot.log
```

## Advanced Filtering

### Multiple patterns
```bash
# Match multiple patterns
tail -f bot.log | grep -E '(ERROR|WARNING|Stats submitted)'

# Exclude specific patterns
tail -f bot.log | grep -v '(DEBUG|INFO)'

# Chain multiple filters
tail -f bot.log | grep ERROR | grep -v 'telegram.ext'
```

### Time-based filtering
```bash
# Logs from last hour (with GNU date)
grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')" bot.log

# Logs from specific time range
sed -n '/2025-02-15 14:00/,/2025-02-15 15:00/p' bot.log
```

## Log Analysis Tools

### Error frequency
```bash
# Count errors by type
grep ERROR bot.log | awk -F': ' '{print $NF}' | sort | uniq -c | sort -rn
```

### Most active users
```bash
# Count commands per user
grep "command from user" bot.log | awk '{print $NF}' | sort | uniq -c | sort -rn
```

### Response time analysis
```bash
# Extract performance data
grep "Performance:" bot.log | awk '{print $NF}' | sort -n
```

## Testing with Logs

### Running tests with log monitoring
```bash
# In one terminal - run tests
python3 test_bot_interactively.py

# In another terminal - monitor logs
tail -f test_results.log
```

### Monitor specific test phases
```bash
# Parser tests
tail -f test_results.log | grep "TEST 1"

# Database tests
tail -f test_results.log | grep "TEST 2"

# Command tests
tail -f test_results.log | grep "TEST 4"
```

## Production Monitoring

### Essential production monitoring
```bash
# Always run in production
tail -f bot.log | grep -E '(ERROR|CRITICAL|Stats submitted)'
```

### Daily log review
```bash
# Yesterday's errors
grep "$(date -d yesterday '+%Y-%m-%d')" bot.log | grep ERROR

# Stats submission summary
grep "$(date '+%Y-%m-%d')" bot.log | grep "Stats submitted" | wc -l
```

## Log File Management

### Check log file size
```bash
ls -lh bot.log
du -h bot.log
```

### Compress old logs
```bash
gzip bot.log.1
gzip bot.log.2
```

### Clear log (careful!)
```bash
# Archive before clearing
cp bot.log bot.log.backup_$(date +%Y%m%d)
echo "" > bot.log
```

## Integration with System Tools

### Systemd journal integration
```bash
# If using systemd
journalctl -u ingress-bot -f
```

### Docker logs
```bash
# If running in Docker
docker logs -f ingress_bot

# Since timestamp
docker logs --since 1h ingress_bot
```

## Quick Reference

| Task | Command |
|------|---------|
| Follow logs | `tail -f bot.log` |
| Errors only | `tail -f bot.log \| grep ERROR` |
| With context | `tail -f bot.log \| grep -C 5 PATTERN` |
| Exclude noise | `tail -f bot.log \| grep -v DEBUG` |
| Count errors | `grep ERROR bot.log \| wc -l` |
| Search history | `grep "pattern" bot.log` |
