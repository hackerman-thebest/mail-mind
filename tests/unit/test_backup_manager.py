"""
Unit Tests for BackupManager

Tests backup creation, restore, integrity checking, and automatic cleanup.

Test Coverage:
- AC6: Backup and restore functionality
- Checksum validation
- Automatic backup cleanup (keep last 7)
- Error handling
"""

import pytest
import tempfile
import os
import sqlite3
from pathlib import Path
from datetime import datetime

from mailmind.database.backup_manager import BackupManager, BackupError


@pytest.fixture
def test_db():
    """Create a test database."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name

    # Create a simple database with data
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)")
    conn.execute("INSERT INTO test_table (data) VALUES ('test data')")
    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def backup_dir():
    """Create a temporary backup directory."""
    import tempfile
    backup_dir = tempfile.mkdtemp()
    yield backup_dir

    # Cleanup
    import shutil
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)


@pytest.fixture
def backup_mgr(test_db, backup_dir):
    """Create BackupManager instance."""
    return BackupManager(db_path=test_db, backup_dir=backup_dir, max_backups=7)


class TestBackupCreation:
    """Test backup creation functionality."""

    def test_create_backup(self, backup_mgr):
        """Test creating a backup."""
        backup_path = backup_mgr.create_backup(description="Test backup")

        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert backup_path.endswith(".db")

    def test_backup_includes_checksum(self, backup_mgr):
        """Test that backup creates checksum file."""
        backup_path = backup_mgr.create_backup()

        checksum_path = Path(backup_path).with_suffix(".db.sha256")
        assert checksum_path.exists()

    def test_backup_includes_metadata(self, backup_mgr):
        """Test that backup creates metadata file."""
        backup_path = backup_mgr.create_backup(description="Test metadata")

        metadata_path = Path(backup_path).with_suffix(".db.meta")
        assert metadata_path.exists()

        # Verify metadata content
        import json
        metadata = json.loads(metadata_path.read_text())
        assert "backup_date" in metadata
        assert "description" in metadata
        assert metadata["description"] == "Test metadata"

    def test_backup_data_integrity(self, backup_mgr, test_db):
        """Test that backup contains correct data."""
        backup_path = backup_mgr.create_backup()

        # Verify backup contains same data as original
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM test_table")
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "test data"


class TestBackupRestore:
    """Test backup restore functionality."""

    def test_restore_backup(self, backup_mgr, test_db):
        """Test restoring from backup."""
        # Create backup
        backup_path = backup_mgr.create_backup()

        # Modify original database
        conn = sqlite3.connect(test_db)
        conn.execute("UPDATE test_table SET data = 'modified data'")
        conn.commit()
        conn.close()

        # Restore from backup
        success = backup_mgr.restore_backup(backup_path)
        assert success is True

        # Verify data was restored
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM test_table")
        result = cursor.fetchone()
        conn.close()

        assert result[0] == "test data"  # Original data restored

    def test_restore_creates_pre_restore_backup(self, backup_mgr):
        """Test that restore creates a backup of current database first."""
        backup_path = backup_mgr.create_backup()

        initial_backup_count = len(backup_mgr.list_backups())

        # Restore (should create pre-restore backup)
        backup_mgr.restore_backup(backup_path)

        # Should have one additional backup
        assert len(backup_mgr.list_backups()) > initial_backup_count

    def test_restore_invalid_path_raises_error(self, backup_mgr):
        """Test that restoring from invalid path raises error."""
        with pytest.raises(BackupError):
            backup_mgr.restore_backup("/nonexistent/backup.db")


class TestBackupVerification:
    """Test backup integrity verification."""

    def test_verify_valid_backup(self, backup_mgr):
        """Test verifying a valid backup."""
        backup_path = backup_mgr.create_backup()

        is_valid = backup_mgr.verify_backup(backup_path)
        assert is_valid is True

    def test_verify_corrupted_backup(self, backup_mgr):
        """Test verifying a corrupted backup fails."""
        backup_path = backup_mgr.create_backup()

        # Corrupt the backup file
        with open(backup_path, "a") as f:
            f.write("CORRUPTED DATA")

        is_valid = backup_mgr.verify_backup(backup_path)
        assert is_valid is False

    def test_verify_missing_checksum(self, backup_mgr):
        """Test verifying backup without checksum fails."""
        backup_path = backup_mgr.create_backup()

        # Delete checksum file
        checksum_path = Path(backup_path).with_suffix(".db.sha256")
        checksum_path.unlink()

        is_valid = backup_mgr.verify_backup(backup_path)
        assert is_valid is False


class TestBackupListing:
    """Test backup listing functionality."""

    def test_list_backups(self, backup_mgr):
        """Test listing all backups."""
        # Create multiple backups
        for i in range(3):
            backup_mgr.create_backup(description=f"Backup {i}")

        backups = backup_mgr.list_backups()

        assert len(backups) == 3
        # Should be sorted by date (most recent first)
        assert all(isinstance(b, tuple) for b in backups)

    def test_get_latest_backup(self, backup_mgr):
        """Test getting latest backup."""
        backup1 = backup_mgr.create_backup()
        import time
        time.sleep(0.1)  # Ensure different timestamps
        backup2 = backup_mgr.create_backup()

        latest = backup_mgr.get_latest_backup()

        assert latest == backup2

    def test_get_backup_status(self, backup_mgr):
        """Test getting backup status."""
        backup_mgr.create_backup()

        status = backup_mgr.get_backup_status()

        assert "last_backup_date" in status
        assert "total_backups" in status
        assert "total_size_mb" in status
        assert status["total_backups"] == 1


class TestBackupCleanup:
    """Test automatic backup cleanup."""

    def test_cleanup_old_backups(self, backup_mgr):
        """Test that old backups are deleted when max_backups is exceeded."""
        # Create more backups than max_backups
        for i in range(10):
            backup_mgr.create_backup()
            import time
            time.sleep(0.05)  # Ensure different timestamps

        backups = backup_mgr.list_backups()

        # Should only keep max_backups (7)
        assert len(backups) == 7

    def test_delete_backup(self, backup_mgr):
        """Test deleting a specific backup."""
        backup_path = backup_mgr.create_backup()

        success = backup_mgr.delete_backup(backup_path)
        assert success is True

        # Backup should be deleted
        assert not os.path.exists(backup_path)

        # Associated files should also be deleted
        checksum_path = Path(backup_path).with_suffix(".db.sha256")
        metadata_path = Path(backup_path).with_suffix(".db.meta")
        assert not checksum_path.exists()
        assert not metadata_path.exists()

    def test_delete_all_backups(self, backup_mgr):
        """Test deleting all backups."""
        # Create multiple backups
        for i in range(5):
            backup_mgr.create_backup()

        success = backup_mgr.delete_all_backups()
        assert success is True

        backups = backup_mgr.list_backups()
        assert len(backups) == 0


class TestErrorHandling:
    """Test error handling in backup operations."""

    def test_backup_nonexistent_database(self, backup_dir):
        """Test backing up nonexistent database raises error."""
        mgr = BackupManager(db_path="/nonexistent/db.db", backup_dir=backup_dir)

        with pytest.raises(BackupError):
            mgr.create_backup()

    def test_restore_nonexistent_backup(self, backup_mgr):
        """Test restoring from nonexistent backup raises error."""
        with pytest.raises(BackupError):
            backup_mgr.restore_backup("/nonexistent/backup.db")
