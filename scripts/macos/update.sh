#!/bin/bash

# ============================================
# Lily Cafe POS - Update Script
# Checks for updates, builds, and installs
# ============================================

set -e  # Exit on error

# Get project root (2 levels up from scripts/macos/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create logs directory
mkdir -p logs

# Set log file with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/update_${TIMESTAMP}.log"

echo "" | tee -a "$LOG_FILE"
echo "============================================" | tee -a "$LOG_FILE"
echo "  Lily Cafe POS - Update System" | tee -a "$LOG_FILE"
echo "============================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

log_info() {
    echo "[INFO] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

# Check if git is installed
if ! command -v git &> /dev/null; then
    log_error "Git is not installed"
    exit 1
fi

log_info "[1/7] Checking for updates..."

# Fetch latest changes
if ! git fetch origin main >> "$LOG_FILE" 2>&1; then
    log_error "Failed to fetch updates from remote"
    exit 1
fi

# Check if there are updates
if git diff --quiet HEAD origin/main; then
    log_info "No updates available"
    log_info "System is up to date"
    echo ""
    exit 0
fi

log_info "Updates found! Installing..."
log_info "[2/7] Backing up database..."

# Store current commit for rollback
OLD_COMMIT=$(git rev-parse HEAD)
log_info "Current commit: $OLD_COMMIT"

# Create backup of database
if [ -f "backend/restaurant.db" ]; then
    mkdir -p backups
    cp "backend/restaurant.db" "backups/restaurant_pre_update_${TIMESTAMP}.db"
    log_success "Database backed up successfully"
else
    log_warning "No database found to backup"
fi

# Pull updates
log_info "[3/7] Pulling updates from server..."
if ! git pull origin main >> "$LOG_FILE" 2>&1; then
    log_error "Git pull failed! Rolling back..."
    git reset --hard "$OLD_COMMIT" >> "$LOG_FILE" 2>&1
    exit 1
fi

NEW_COMMIT=$(git rev-parse HEAD)
log_info "Updated to commit: $NEW_COMMIT"

# Update backend dependencies (including printer support)
log_info "[4/7] Updating backend dependencies and printer drivers..."
cd backend
if ! uv sync --extra printer >> "../$LOG_FILE" 2>&1; then
    log_error "Backend dependency update failed! Rolling back..."
    cd ..
    git reset --hard "$OLD_COMMIT" >> "$LOG_FILE" 2>&1
    exit 1
fi
cd ..
log_success "Backend dependencies updated (including pywin32 for printing)"

# Update frontend dependencies
log_info "[5/7] Updating frontend dependencies..."
cd frontend
if ! npm install >> "../$LOG_FILE" 2>&1; then
    log_warning "Frontend dependency update had issues"
else
    log_success "Frontend dependencies updated"
fi

# Build frontend for production
log_info "[6/7] Building frontend for production..."
if ! npm run build >> "../$LOG_FILE" 2>&1; then
    log_error "Frontend build failed! Rolling back..."
    cd ..
    git reset --hard "$OLD_COMMIT" >> "$LOG_FILE" 2>&1
    exit 1
fi
log_success "Frontend built successfully"
cd ..

log_info "[7/7] Finalizing update..."

echo "" | tee -a "$LOG_FILE"
echo "============================================" | tee -a "$LOG_FILE"
log_success "Update completed successfully!"
echo "============================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
log_info "Backend dependencies: Updated"
log_info "Printer drivers: Installed"
log_info "Frontend: Built and ready"
echo "" | tee -a "$LOG_FILE"
echo "Please restart the POS system:" | tee -a "$LOG_FILE"
echo "  ./scripts/macos/start.sh" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Keep only last 30 log files
ls -t logs/update_*.log 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true

exit 0
