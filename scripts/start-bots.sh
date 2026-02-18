#!/data/data/com.termux/files/usr/bin/bash
# =============================================================
#  Termux Boot Script — Start All Bots
#  Run on every phone restart (via Termux:Boot) or manually.
#  Usage: bash scripts/start-bots.sh
# =============================================================

set -euo pipefail

# ─── Configuration ───────────────────────────────────────────
# Add bot directories here. Each entry is an absolute path.
# The script will set up venv + deps + start PM2 for each one.
BOT_DIRS=(
    "$HOME/Ingress-LeaderBoard-Bot"
    # "$HOME/my-other-bot"        # ← Uncomment to add more bots
)

REQUIREMENTS_FILE="requirements-termux.txt"   # Fallback: requirements.txt
LOG_FILE="$HOME/bot-startup.log"

# ─── Helpers ─────────────────────────────────────────────────
timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

log() {
    echo "[$(timestamp)] $1" | tee -a "$LOG_FILE"
}

separator() {
    log "──────────────────────────────────────────────"
}

# ─── Pre-flight checks ──────────────────────────────────────
log "🚀 Bot startup script initiated"
separator

# Acquire wake-lock so Termux doesn't get killed by Android
if command -v termux-wake-lock &>/dev/null; then
    termux-wake-lock
    log "🔒 Wake lock acquired"
fi

# Ensure PM2 is installed
if ! command -v pm2 &>/dev/null; then
    log "📦 PM2 not found, installing..."
    npm install -g pm2
    log "✅ PM2 installed"
fi

# Ensure Python is available
if ! command -v python3 &>/dev/null; then
    log "❌ Python3 not found. Install it with: pkg install python"
    exit 1
fi

# ─── Process each bot ───────────────────────────────────────
for BOT_DIR in "${BOT_DIRS[@]}"; do
    separator
    log "📂 Processing: $BOT_DIR"

    # Check if directory exists
    if [ ! -d "$BOT_DIR" ]; then
        log "⚠️  Directory not found: $BOT_DIR — skipping"
        continue
    fi

    cd "$BOT_DIR"

    # ── Git pull (update code) ──
    if [ -d ".git" ]; then
        log "🔄 Pulling latest changes..."
        git pull origin master 2>&1 | tee -a "$LOG_FILE" || log "⚠️  Git pull failed (non-fatal)"
    else
        log "⚠️  Not a git repo, skipping pull"
    fi

    # ── Virtual environment ──
    if [ ! -d "venv" ]; then
        log "🐍 Creating virtual environment..."
        python3 -m venv venv
        log "✅ venv created"
    else
        log "✅ venv already exists"
    fi

    # Activate venv
    source venv/bin/activate

    # ── Install / update dependencies ──
    if [ -f "$REQUIREMENTS_FILE" ]; then
        REQ="$REQUIREMENTS_FILE"
    elif [ -f "requirements.txt" ]; then
        REQ="requirements.txt"
    else
        log "⚠️  No requirements file found — skipping deps"
        REQ=""
    fi

    if [ -n "$REQ" ]; then
        log "📦 Installing dependencies from $REQ..."
        pip install --upgrade pip -q 2>&1 | tail -1 | tee -a "$LOG_FILE"
        pip install -r "$REQ" -q 2>&1 | tail -1 | tee -a "$LOG_FILE"
        log "✅ Dependencies installed"
    fi

    # Deactivate (PM2 will use the venv python directly)
    deactivate

    # ── Start with PM2 ──
    if [ -f "ecosystem.config.js" ]; then
        log "🤖 Starting bot via ecosystem.config.js..."
        # Use the venv's python interpreter
        VENV_PYTHON="$BOT_DIR/venv/bin/python3"
        pm2 start ecosystem.config.js --interpreter "$VENV_PYTHON" 2>&1 | tee -a "$LOG_FILE"
    elif [ -f "main.py" ]; then
        BOT_NAME=$(basename "$BOT_DIR")
        VENV_PYTHON="$BOT_DIR/venv/bin/python3"
        log "🤖 Starting $BOT_NAME via main.py..."
        pm2 start main.py --name "$BOT_NAME" --interpreter "$VENV_PYTHON" 2>&1 | tee -a "$LOG_FILE"
    else
        log "⚠️  No main.py or ecosystem.config.js found — skipping"
    fi

    log "✅ Done processing: $(basename "$BOT_DIR")"
done

# ─── Finalize ────────────────────────────────────────────────
separator
log "💾 Saving PM2 process list..."
pm2 save 2>&1 | tee -a "$LOG_FILE"

log "📊 PM2 Status:"
pm2 list 2>&1 | tee -a "$LOG_FILE"

separator
log "🎉 All bots started! Logs at: $LOG_FILE"
log "   View live logs: pm2 logs"
log "   Monitor:        pm2 monit"
