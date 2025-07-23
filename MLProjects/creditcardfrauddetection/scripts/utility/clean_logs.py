#!/usr/bin/env python
"""
Script to clean up old log files
This script archives and removes log files older than a specified number of days
"""

import os
import sys
import argparse
import datetime
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def archive_old_logs(logs_dir, archive_dir, days_to_keep=30, dry_run=False):
    """
    Archive log files older than the specified number of days
    
    Args:
        logs_dir: Path to the logs directory
        archive_dir: Path to the archive directory
        days_to_keep: Number of days to keep logs before archiving
        dry_run: If True, only print what would be done without actually archiving
    """
    logs_path = Path(logs_dir)
    archive_path = Path(archive_dir)
    
    # Create archive directory if it doesn't exist
    if not archive_path.exists() and not dry_run:
        archive_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created archive directory: {archive_path}")
    
    # Get current date
    current_date = datetime.datetime.now()
    cutoff_date = current_date - datetime.timedelta(days=days_to_keep)
    
    # Find log files
    log_files = list(logs_path.glob('*.log'))
    old_logs = []
    
    for log_file in log_files:
        # Get file modification time
        mod_time = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
        
        # Check if file is older than cutoff date
        if mod_time < cutoff_date:
            old_logs.append((log_file, mod_time))
    
    if not old_logs:
        logger.info(f"No log files older than {days_to_keep} days found.")
        return
    
    # Sort logs by modification time (oldest first)
    old_logs.sort(key=lambda x: x[1])
    
    logger.info(f"Found {len(old_logs)} log files older than {days_to_keep} days:")
    for log_file, mod_time in old_logs:
        days_old = (current_date - mod_time).days
        action = "Would archive" if dry_run else "Archiving"
        logger.info(f"{action}: {log_file.name} ({days_old} days old)")
        
        if not dry_run:
            # Archive the file
            archive_file = archive_path / log_file.name
            shutil.copy2(log_file, archive_file)
            # Delete the original
            log_file.unlink()
    
    if not dry_run:
        logger.info(f"Archived {len(old_logs)} log files to {archive_path}")

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Clean up old log files')
    parser.add_argument('--days', type=int, default=30, help='Number of days to keep logs (default: 30)')
    parser.add_argument('--dry-run', action='store_true', help='Only print what would be done without actually archiving')
    args = parser.parse_args()
    
    # Get paths
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    project_dir = script_dir.parent.parent
    logs_dir = project_dir / 'logs'
    archive_dir = project_dir / 'scripts' / 'archive' / 'logs'
    
    # Archive old logs
    archive_old_logs(logs_dir, archive_dir, args.days, args.dry_run)

if __name__ == "__main__":
    main()
