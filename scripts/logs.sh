#!/bin/bash
# Development Log Viewing Script
# This script provides easy access to various logs during development

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help function
show_help() {
    echo "📋 Development Log Viewer"
    echo "========================"
    echo ""
    echo "Usage: $0 [service] [options]"
    echo ""
    echo "Services:"
    echo "  bot       Show bot logs (default)"
    echo "  db        Show database logs"
    echo "  adminer   Show Adminer logs"
    echo "  all       Show all logs"
    echo ""
    echo "Options:"
    echo "  -f, --follow     Follow log output (live tail)"
    echo "  -n, --lines N    Show last N lines (default: 50)"
    echo "  -h, --help       Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                Show last 50 lines of bot logs"
    echo "  $0 bot -f         Follow bot logs live"
    echo "  $0 db -n 100      Show last 100 lines of database logs"
    echo "  $0 all -f         Follow all logs live"
    echo ""
}

# Default values
SERVICE="bot"
FOLLOW=false
LINES=50

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        bot|db|adminer|all)
            SERVICE="$1"
            shift
            ;;
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Check if docker-compose is running
if ! docker-compose -f docker-compose.dev.yml ps -q | head -1 | grep -q .; then
    echo -e "${YELLOW}⚠️  Development services are not running.${NC}"
    echo "   Start them with: docker-compose -f docker-compose.dev.yml up"
    exit 1
fi

# Build docker-compose command
DCOMMAND="docker-compose -f docker-compose.dev.yml logs"

if [ "$FOLLOW" = true ]; then
    DCOMMAND="$DCOMMAND -f"
fi

if [ "$LINES" != "all" ]; then
    DCOMMAND="$DCOMMAND --tail=$LINES"
fi

# Show logs based on service
echo -e "${BLUE}📊 Showing logs for: ${SERVICE}${NC}"
echo -e "${BLUE}🔢 Lines: ${LINES}${NC}"
echo -e "${BLUE}🔄 Follow: ${FOLLOW}${NC}"
echo ""

case $SERVICE in
    bot)
        echo -e "${GREEN}🤖 Bot Logs:${NC}"
        $DCOMMAND bot
        ;;
    db)
        echo -e "${GREEN}🗄️ Database Logs:${NC}"
        $DCOMMAND db
        ;;
    adminer)
        echo -e "${GREEN}🔧 Adminer Logs:${NC}"
        $DCOMMAND adminer
        ;;
    all)
        echo -e "${GREEN}📋 All Logs:${NC}"
        $DCOMMAND
        ;;
esac