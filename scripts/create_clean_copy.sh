#!/bin/bash
# Script to create a clean copy of bot for Termux deployment

SOURCE_DIR="/home/codesagepath/Documents/TGBot/ingress_leaderboard"
DEST_DIR="/tmp/ingress_leaderboard_clean"

echo "Creating clean bot copy for Termux..."

# Remove old clean copy if exists
rm -rf "$DEST_DIR"

# Create destination directory
mkdir -p "$DEST_DIR"

# Copy only necessary files using rsync with exclusions
rsync -av --progress \
  --exclude='.git' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.pyo' \
  --exclude='.pytest_cache' \
  --exclude='*.log' \
  --exclude='*.db' \
  --exclude='.claude' \
  --exclude='.github' \
  --exclude='docker' \
  --exclude='docker-compose*.yml' \
  --exclude='Dockerfile' \
  --exclude='.dockerignore' \
  --exclude='kubernetes' \
  --exclude='terraform' \
  --exclude='alembic' \
  --exclude='alembic.ini' \
  --exclude='tests' \
  --exclude='docs' \
  --exclude='guides' \
  --exclude='sample_data' \
  --exclude='.env.dev' \
  --exclude='.env.production' \
  --exclude='.env.staging' \
  --exclude='test_*.py' \
  --exclude='validation_demo.py' \
  --exclude='example_logging.py' \
  --exclude='project.txt' \
  --exclude='roadmap.txt' \
  --exclude='u0_a101@192.168.68.53' \
  "$SOURCE_DIR/" "$DEST_DIR/"

echo ""
echo "✓ Clean copy created at: $DEST_DIR"
echo ""
echo "Files included:"
du -sh "$DEST_DIR"
echo ""
echo "Now copy to Termux using:"
echo "  scp -P 8022 -r $DEST_DIR u0_a101@192.168.68.53:~/"
echo ""
echo "Or via USB:"
echo "  1. Copy $DEST_DIR to phone storage"
echo "  2. In Termux: cp -r ~/storage/shared/ingress_leaderboard_clean ~/ingress_leaderboard"
