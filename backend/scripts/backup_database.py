"""
Automated Database Backup Script for Lily Cafe POS

This script creates timestamped backups of your restaurant.db file
and can optionally upload to cloud storage (Google Drive, Dropbox, AWS S3, etc.)

USAGE:
    # Local backup only
    uv run python scripts/backup_database.py

    # Backup + upload to cloud (configure cloud settings below)
    uv run python scripts/backup_database.py --upload

SETUP CLOUD SYNC (Choose one):
    1. Google Drive: Use rclone (recommended - free unlimited storage)
    2. Dropbox: Use rclone
    3. AWS S3: Use boto3
    4. Any cloud: Use rclone

AUTOMATION:
    Add to crontab for automatic daily backups:

    # Backup every day at 2 AM
    0 2 * * * cd /path/to/lily-cafe-pos/backend && /path/to/uv run python scripts/backup_database.py --upload

    # Backup every 6 hours
    0 */6 * * * cd /path/to/lily-cafe-pos/backend && /path/to/uv run python scripts/backup_database.py --upload
"""

import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

# Local backup settings
BACKUP_DIR = Path(__file__).parent.parent / "backups"
DATABASE_FILE = Path(__file__).parent.parent / "restaurant.db"
MAX_LOCAL_BACKUPS = 30  # Keep last 30 backups locally (e.g., 30 days if daily backup)

# Cloud upload settings (configure based on your chosen service)
CLOUD_ENABLED = False  # Set to True after configuring cloud settings

# For rclone (Google Drive, Dropbox, OneDrive, etc.)
# Install: https://rclone.org/install/
# Setup: rclone config
RCLONE_REMOTE = "gdrive"  # Name you gave during rclone config
RCLONE_PATH = "lily-cafe-backups"  # Folder in cloud storage

# For AWS S3 (if you prefer S3)
AWS_S3_BUCKET = "lily-cafe-backups"
AWS_S3_PREFIX = "database/"


# ════════════════════════════════════════════════════════════════════════════
# BACKUP FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def create_backup_filename():
    """Generate timestamped backup filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"restaurant_backup_{timestamp}.db"


def create_local_backup():
    """Create a local backup of the database."""
    # Ensure backup directory exists
    BACKUP_DIR.mkdir(exist_ok=True)

    # Check if database exists
    if not DATABASE_FILE.exists():
        print(f"❌ Database file not found: {DATABASE_FILE}")
        return None

    # Create backup
    backup_filename = create_backup_filename()
    backup_path = BACKUP_DIR / backup_filename

    try:
        # Use SQLite's built-in backup command for safe backup
        # This ensures backup even if database is in use
        import sqlite3
        source = sqlite3.connect(str(DATABASE_FILE))
        backup = sqlite3.connect(str(backup_path))
        source.backup(backup)
        backup.close()
        source.close()

        file_size = backup_path.stat().st_size / (1024 * 1024)  # MB
        print(f"✅ Local backup created: {backup_filename} ({file_size:.2f} MB)")
        return backup_path

    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return None


def cleanup_old_backups():
    """Remove old backups, keeping only MAX_LOCAL_BACKUPS most recent."""
    if not BACKUP_DIR.exists():
        return

    # Get all backup files sorted by modification time (newest first)
    backups = sorted(
        BACKUP_DIR.glob("restaurant_backup_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    # Remove old backups
    removed_count = 0
    for backup in backups[MAX_LOCAL_BACKUPS:]:
        try:
            backup.unlink()
            removed_count += 1
        except Exception as e:
            print(f"⚠️  Failed to remove old backup {backup.name}: {e}")

    if removed_count > 0:
        print(f"🗑️  Removed {removed_count} old backup(s), kept {MAX_LOCAL_BACKUPS} most recent")


def upload_to_rclone(backup_path):
    """Upload backup to cloud storage using rclone."""
    if not CLOUD_ENABLED:
        print("ℹ️  Cloud upload disabled (set CLOUD_ENABLED=True to enable)")
        return False

    # Check if rclone is installed
    try:
        subprocess.run(["rclone", "version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ rclone not found. Install from: https://rclone.org/install/")
        return False

    # Upload to cloud
    remote_path = f"{RCLONE_REMOTE}:{RCLONE_PATH}/{backup_path.name}"

    print(f"☁️  Uploading to {remote_path}...")

    try:
        result = subprocess.run(
            ["rclone", "copy", str(backup_path), f"{RCLONE_REMOTE}:{RCLONE_PATH}"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ Uploaded to cloud: {remote_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Cloud upload failed: {e.stderr}")
        return False


def upload_to_s3(backup_path):
    """Upload backup to AWS S3."""
    if not CLOUD_ENABLED:
        return False

    try:
        import boto3
        s3 = boto3.client('s3')

        key = f"{AWS_S3_PREFIX}{backup_path.name}"
        print(f"☁️  Uploading to S3: s3://{AWS_S3_BUCKET}/{key}")

        s3.upload_file(str(backup_path), AWS_S3_BUCKET, key)
        print(f"✅ Uploaded to S3: s3://{AWS_S3_BUCKET}/{key}")
        return True
    except ImportError:
        print("❌ boto3 not installed. Run: uv pip install boto3")
        return False
    except Exception as e:
        print(f"❌ S3 upload failed: {e}")
        return False


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Backup Lily Cafe POS database")
    parser.add_argument("--upload", action="store_true", help="Upload backup to cloud storage")
    parser.add_argument("--cloud", choices=["rclone", "s3"], default="rclone", help="Cloud provider")
    args = parser.parse_args()

    print("=" * 80)
    print("  Lily Cafe POS - Database Backup")
    print("=" * 80)
    print(f"Database: {DATABASE_FILE}")
    print(f"Backup directory: {BACKUP_DIR}")
    print()

    # Create local backup
    backup_path = create_local_backup()
    if not backup_path:
        sys.exit(1)

    # Cleanup old backups
    cleanup_old_backups()

    # Upload to cloud if requested
    if args.upload:
        if args.cloud == "rclone":
            upload_to_rclone(backup_path)
        elif args.cloud == "s3":
            upload_to_s3(backup_path)

    print()
    print("=" * 80)
    print("✅ Backup completed successfully!")
    print()
    print("Local backups stored in:", BACKUP_DIR)

    if args.upload and CLOUD_ENABLED:
        print("Cloud backups available at:", f"{RCLONE_REMOTE}:{RCLONE_PATH}")

    print()
    print("To restore from backup:")
    print(f"  cp {backup_path} {DATABASE_FILE}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
