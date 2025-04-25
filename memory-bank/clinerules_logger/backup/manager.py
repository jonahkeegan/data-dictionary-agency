#!/usr/bin/env python3
"""
Backup manager for .clinerules logger database.
"""

import os
import time
import shutil
import sqlite3
import zipfile
import threading
import schedule
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.config import config

class BackupManager:
    """Manages database backups, rotation, and recovery."""
    
    _instance = None
    _lock = threading.Lock()
    _scheduler_thread = None
    _running = False
    
    def __new__(cls):
        """Singleton pattern to ensure only one backup manager instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BackupManager, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        """Initialize the backup manager."""
        self._db_path = config.get('database', 'path')
        self._backup_dir = Path(config.get('database', 'backup_dir'))
        self._retention_days = config.get('database', 'backup_retention_days')
        self._interval_hours = config.get('database', 'backup_interval_hours')
        self._prefix = config.get('database', 'backup_prefix')
        
        # Ensure backup directory exists
        os.makedirs(self._backup_dir, exist_ok=True)
    
    def create_backup(self, backup_name=None):
        """Create a new backup of the database."""
        if not os.path.exists(self._db_path):
            print(f"Warning: Database file not found at {self._db_path}")
            return False
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = backup_name or f"{self._prefix}{timestamp}.db"
        backup_path = self._backup_dir / backup_name
        
        try:
            # Connect to source database
            conn = sqlite3.connect(self._db_path)
            
            # Create a backup using sqlite3's backup API
            with sqlite3.connect(str(backup_path)) as bck:
                conn.backup(bck)
            
            conn.close()
            
            print(f"Database backup created at {backup_path}")
            
            # Create compressed backup
            self._compress_backup(backup_path)
            
            # Apply retention policy
            self._apply_retention_policy()
            
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def _compress_backup(self, backup_path):
        """Compress a backup file to save space."""
        try:
            zip_path = str(backup_path) + '.zip'
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_path, arcname=os.path.basename(backup_path))
            
            # Remove the uncompressed backup file
            os.remove(backup_path)
            
            print(f"Backup compressed to {zip_path}")
            return True
            
        except Exception as e:
            print(f"Error compressing backup: {e}")
            return False
    
    def _apply_retention_policy(self):
        """Apply retention policy by removing old backups."""
        try:
            if self._retention_days <= 0:
                return  # No retention policy
                
            cutoff_date = datetime.now() - timedelta(days=self._retention_days)
            
            for file_path in self._backup_dir.glob(f"{self._prefix}*.zip"):
                try:
                    # Extract timestamp from filename
                    timestamp_str = file_path.stem.replace(self._prefix, '')
                    if '_' in timestamp_str:
                        timestamp_str = timestamp_str.split('_')[0]
                    
                    file_date = datetime.strptime(timestamp_str, '%Y%m%d')
                    
                    # Check if file is older than retention period
                    if file_date < cutoff_date:
                        os.remove(file_path)
                        print(f"Removed old backup: {file_path}")
                        
                except (ValueError, Exception) as e:
                    print(f"Error processing backup file {file_path}: {e}")
                    continue
                    
            return True
            
        except Exception as e:
            print(f"Error applying retention policy: {e}")
            return False
    
    def restore_from_backup(self, backup_path):
        """Restore database from a backup file."""
        try:
            # Check if backup is compressed
            if str(backup_path).endswith('.zip'):
                # Extract the backup file
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    # Get the first file in the archive
                    backup_filename = zipf.namelist()[0]
                    temp_dir = self._backup_dir / 'temp'
                    os.makedirs(temp_dir, exist_ok=True)
                    zipf.extract(backup_filename, temp_dir)
                    
                    # Set the path to the extracted file
                    extracted_path = temp_dir / backup_filename
                    
                    # Perform the restore
                    success = self._perform_restore(extracted_path)
                    
                    # Clean up
                    os.remove(extracted_path)
                    try:
                        os.rmdir(temp_dir)
                    except:
                        pass
                        
                    return success
            else:
                # Direct restore from uncompressed backup
                return self._perform_restore(backup_path)
                
        except Exception as e:
            print(f"Error restoring from backup: {e}")
            return False
    
    def _perform_restore(self, backup_path):
        """Perform the actual restore operation."""
        try:
            # Create a backup of the current database first
            self.create_backup(f"{self._prefix}pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            
            # Connect to backup database
            conn = sqlite3.connect(backup_path)
            
            # Create a new target database
            with sqlite3.connect(self._db_path) as target:
                conn.backup(target)
            
            conn.close()
            
            print(f"Database restored from {backup_path}")
            return True
            
        except Exception as e:
            print(f"Error during restore: {e}")
            return False
    
    def list_available_backups(self):
        """List all available backup files."""
        backups = []
        
        for file_path in sorted(self._backup_dir.glob(f"{self._prefix}*.zip")):
            try:
                stat = os.stat(file_path)
                size_mb = stat.st_size / (1024 * 1024)
                
                backups.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'size_mb': round(size_mb, 2)
                })
                
            except Exception as e:
                print(f"Error processing backup file {file_path}: {e}")
                continue
                
        return backups
    
    def start_scheduler(self):
        """Start the backup scheduler thread."""
        if self._running:
            return
            
        self._running = True
        
        # Schedule backup at specified interval
        hours = self._interval_hours
        if hours <= 0:
            hours = 24  # Default to daily backups
            
        # Schedule the first backup
        schedule.every(hours).hours.do(self.create_backup)
        
        # Also do an immediate backup
        self.create_backup()
        
        # Start the scheduler thread
        def run_scheduler():
            while self._running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        self._scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self._scheduler_thread.start()
        
        print(f"Backup scheduler started, running every {hours} hours")
        return True
    
    def stop_scheduler(self):
        """Stop the backup scheduler thread."""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=2)
            self._scheduler_thread = None
            
        print("Backup scheduler stopped")
        return True

# Create singleton instance
backup_manager = BackupManager()
