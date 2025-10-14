"""
Backup Manager for MailMind Database

Provides backup and restore functionality with integrity checking, automatic
cleanup, and support for scheduled backups.

Features:
- Manual backup to timestamped files
- Automatic daily backups (keep last 7 days)
- Checksum validation for integrity verification
- Backup status tracking
- Graceful error handling

Usage:
    backup_mgr = BackupManager(db_path="mailmind.db")

    # Manual backup
    backup_path = backup_mgr.create_backup()

    # Restore from backup
    backup_mgr.restore_backup(backup_path)

    # Check backup integrity
    is_valid = backup_mgr.verify_backup(backup_path)
"""

import os
import shutil
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


class BackupError(Exception):
    """Base exception for backup operations."""
    pass


class BackupManager:
    """
    Manages database backups with integrity checking and automatic cleanup.

    Attributes:
        db_path: Path to database file
        backup_dir: Directory for backup storage
        max_backups: Maximum number of backups to retain
    """

    def __init__(self, db_path: str, backup_dir: str = None, max_backups: int = 7):
        """
        Initialize BackupManager.

        Args:
            db_path: Path to database file
            backup_dir: Directory for backups (default: {project-root}/backups/)
            max_backups: Maximum backups to retain (default: 7)
        """
        self.db_path = Path(db_path)

        if backup_dir is None:
            project_root = self.db_path.parent
            backup_dir = str(project_root / "backups")

        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups

        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, description: str = None) -> str:
        """
        Create a backup of the database with timestamp.

        Args:
            description: Optional description for backup

        Returns:
            str: Path to created backup file

        Raises:
            BackupError: If backup creation fails
        """
        try:
            # Verify database file exists
            if not self.db_path.exists():
                raise BackupError(f"Database file not found: {self.db_path}")

            # Generate timestamped filename with microseconds for uniqueness
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
            db_name = self.db_path.stem
            backup_filename = f"{db_name}-backup-{timestamp}.db"
            backup_path = self.backup_dir / backup_filename

            logger.info(f"Creating backup: {backup_path}")

            # Copy database file
            shutil.copy2(self.db_path, backup_path)

            # Create checksum file for integrity verification
            checksum = self._calculate_checksum(backup_path)
            checksum_path = backup_path.with_suffix(".db.sha256")
            checksum_path.write_text(checksum)

            # Create metadata file
            metadata = {
                "original_path": str(self.db_path),
                "backup_date": datetime.now().isoformat(),
                "description": description or "Manual backup",
                "checksum": checksum
            }

            metadata_path = backup_path.with_suffix(".db.meta")
            import json
            metadata_path.write_text(json.dumps(metadata, indent=2))

            logger.info(f"Backup created successfully: {backup_path}")

            # Cleanup old backups
            self._cleanup_old_backups()

            return str(backup_path)

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            raise BackupError(f"Failed to create backup: {e}")

    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore database from backup file.

        Args:
            backup_path: Path to backup file

        Returns:
            bool: True if restore successful

        Raises:
            BackupError: If restore fails
        """
        try:
            backup_path = Path(backup_path)

            # Verify backup file exists
            if not backup_path.exists():
                raise BackupError(f"Backup file not found: {backup_path}")

            # Verify backup integrity
            if not self.verify_backup(str(backup_path)):
                raise BackupError("Backup integrity check failed - file may be corrupted")

            logger.info(f"Restoring database from: {backup_path}")

            # Create backup of current database before restoring
            if self.db_path.exists():
                current_backup = self.create_backup(description="Pre-restore backup")
                logger.info(f"Current database backed up to: {current_backup}")

            # Restore from backup
            shutil.copy2(backup_path, self.db_path)

            logger.info(f"Database restored successfully from: {backup_path}")
            return True

        except BackupError:
            raise
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise BackupError(f"Failed to restore backup: {e}")

    def verify_backup(self, backup_path: str) -> bool:
        """
        Verify backup file integrity using checksum.

        Args:
            backup_path: Path to backup file

        Returns:
            bool: True if backup is valid, False otherwise
        """
        try:
            backup_path = Path(backup_path)
            checksum_path = backup_path.with_suffix(".db.sha256")

            # Check if backup and checksum files exist
            if not backup_path.exists():
                logger.warning(f"Backup file not found: {backup_path}")
                return False

            if not checksum_path.exists():
                logger.warning(f"Checksum file not found: {checksum_path}")
                return False

            # Calculate current checksum
            current_checksum = self._calculate_checksum(backup_path)

            # Read stored checksum
            stored_checksum = checksum_path.read_text().strip()

            # Compare checksums
            is_valid = current_checksum == stored_checksum

            if is_valid:
                logger.info(f"Backup integrity verified: {backup_path}")
            else:
                logger.warning(f"Backup integrity check FAILED: {backup_path}")

            return is_valid

        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False

    def list_backups(self) -> List[Tuple[str, datetime, int]]:
        """
        List all available backups with metadata.

        Returns:
            list: List of tuples (backup_path, backup_date, size_bytes)
        """
        backups = []

        try:
            for backup_file in sorted(self.backup_dir.glob("*.db"), reverse=True):
                # Get file stats
                stat = backup_file.stat()
                size_bytes = stat.st_size
                backup_date = datetime.fromtimestamp(stat.st_mtime)

                backups.append((str(backup_file), backup_date, size_bytes))

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")

        return backups

    def get_latest_backup(self) -> Optional[str]:
        """
        Get path to the most recent backup.

        Returns:
            str: Path to latest backup, or None if no backups exist
        """
        backups = self.list_backups()

        if backups:
            return backups[0][0]  # First item (most recent)

        return None

    def get_backup_status(self) -> dict:
        """
        Get backup status information.

        Returns:
            dict: Backup status with last_backup_date, total_backups, total_size_mb
        """
        backups = self.list_backups()

        if not backups:
            return {
                "last_backup_date": None,
                "total_backups": 0,
                "total_size_mb": 0.0
            }

        last_backup_path, last_backup_date, _ = backups[0]
        total_size_bytes = sum(size for _, _, size in backups)
        total_size_mb = total_size_bytes / (1024 * 1024)

        return {
            "last_backup_date": last_backup_date.isoformat(),
            "last_backup_path": last_backup_path,
            "total_backups": len(backups),
            "total_size_mb": round(total_size_mb, 2)
        }

    def delete_backup(self, backup_path: str) -> bool:
        """
        Delete a specific backup and its associated files.

        Args:
            backup_path: Path to backup file

        Returns:
            bool: True if deletion successful
        """
        try:
            backup_path = Path(backup_path)

            # Delete backup file
            if backup_path.exists():
                backup_path.unlink()

            # Delete checksum file
            checksum_path = backup_path.with_suffix(".db.sha256")
            if checksum_path.exists():
                checksum_path.unlink()

            # Delete metadata file
            metadata_path = backup_path.with_suffix(".db.meta")
            if metadata_path.exists():
                metadata_path.unlink()

            logger.info(f"Backup deleted: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False

    def delete_all_backups(self) -> bool:
        """
        Delete all backups in the backup directory.

        Returns:
            bool: True if all backups deleted successfully

        Warning:
            This operation is irreversible.
        """
        try:
            backups = self.list_backups()

            for backup_path, _, _ in backups:
                self.delete_backup(backup_path)

            logger.warning(f"All backups deleted from: {self.backup_dir}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete all backups: {e}")
            return False

    def _cleanup_old_backups(self):
        """
        Delete old backups, keeping only the most recent max_backups.
        """
        try:
            backups = self.list_backups()

            if len(backups) > self.max_backups:
                # Delete oldest backups
                backups_to_delete = backups[self.max_backups:]

                for backup_path, backup_date, _ in backups_to_delete:
                    self.delete_backup(backup_path)
                    logger.info(f"Deleted old backup: {backup_path}")

        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")

    def _calculate_checksum(self, file_path: Path) -> str:
        """
        Calculate SHA-256 checksum for file.

        Args:
            file_path: Path to file

        Returns:
            str: Hex-encoded SHA-256 checksum
        """
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()
