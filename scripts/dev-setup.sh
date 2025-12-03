#!/bin/bash
# Development Environment Setup Script
# This script sets up the development environment for the Ingress Leaderboard Bot

set -e

echo "🚀 Setting up Ingress Leaderboard Bot Development Environment"
echo "============================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.dev .env
    echo "⚠️  IMPORTANT: Edit .env file and add your TELEGRAM_BOT_TOKEN"
    echo "   Your bot will not work without a valid bot token from @BotFather"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/logs
mkdir -p data/uploads
mkdir -p data/backups

# Set proper permissions
echo "🔐 Setting permissions..."
chmod 755 scripts/*.sh 2>/dev/null || true

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Next Steps:"
echo "   1. Edit .env file and add your TELEGRAM_BOT_TOKEN"
echo "   2. Run: docker-compose -f docker-compose.dev.yml up"
echo "   3. Visit http://localhost:8080 for database admin (Adminer)"
echo ""
echo "🔧 Useful Commands:"
echo "   • Start services:     docker-compose -f docker-compose.dev.yml up"
echo "   • Stop services:      docker-compose -f docker-compose.dev.yml down"
echo "   • View logs:          docker-compose -f docker-compose.dev.yml logs -f"
echo "   • Restart services:   docker-compose -f docker-compose.dev.yml restart"
echo "   • Access bot shell:   docker-compose -f docker-compose.dev.yml exec bot bash"
echo "   • Access database:    docker-compose -f docker-compose.dev.yml exec db psql -U postgres -d ingress_leaderboard_dev"
echo ""
echo "📚 Documentation:"
echo "   • Bot commands:       /help in Telegram"
echo "   • Database admin:     http://localhost:8080"
echo "   • Development guide:  See README.md"
echo ""