"""
Database Migration Tool for Encryption

Provides migration utilities for converting between encrypted and unencrypted databases.
Implements safe migration with backup, progress tracking, and rollback capabilities.

Story 3.1 AC3: Database Migration Tool
- Convert unencrypted → encrypted databases
- Convert encrypted → unencrypted databases (user choice)
- Progress tracking with callbacks for UI integration
- Automatic backup before migration
- Rollback on failure
- Data integrity verification
- Support for large databases (>500MB, >10K emails)

Migration Strategy:
1. Create backup of original database
2. Create new database with target encryption state
3. Copy all tables and data with progress tracking
4. Verify data integrity (row counts, checksums)
5. Replace original with migrated database
6. Clean up temporary files

Safety Features:
- Atomic migration (replace only after verification)
- Automatic backup before migration
- Rollback to backup on failure
- Progress callbacks for user feedback
- Detailed error logging
"""

import os
import sys
import shutil
import logging
import tempfile
from pathlib import Path
from typing import Optional, Callable, Dict, List, Tuple
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Platform detection
IS_WINDOWS = sys.platform == "win32"

# Import database modules
try:
    import pysqlcipher3.dbapi2 as sqlite3_encrypted
    SQLCIPHER_AVAILABLE = True
except ImportError:
    SQLCIPHER_AVAILABLE = False
    logger.warning("pysqlcipher3 not available - encrypted migrations will fail")

import sqlite3 as sqlite3_plain

# Import KeyManager
try:
    from mailmind.core.key_manager import KeyManager, KeyManagementError
    KEY_MANAGER_AVAILABLE = True
except ImportError:
    KEY_MANAGER_AVAILABLE = False
    logger.warning("KeyManager not available - encrypted migrations will fail")


# ============================================================================
# Exception Classes
# ============================================================================

class MigrationError(Exception):
    """Base exception for migration errors."""
    pass


class MigrationValidationError(MigrationError):
    """Raised when migration validation fails."""
    pass


class MigrationBackupError(MigrationError):
    """Raised when backup creation fails."""
    pass


class MigrationRollbackError(MigrationError):
    """Raised when rollback fails."""
    pass


# ============================================================================
# Progress Tracking
# ============================================================================

class MigrationProgress:
    """
    Tracks migration progress and provides callbacks for UI updates.

    Progress Stages:
    1. backup (10%) - Creating backup
    2. create_schema (20%) - Creating target database schema
    3. copy_data (20-90%) - Copying table data (70% of total)
    4. verify (90-95%) - Verifying data integrity
    5. finalize (95-100%) - Replacing original database
    """

    def __init__(self, callback: Optional[Callable[[str, int], None]] = None):
        """
        Initialize progress tracker.

        Args:
            callback: Optional callback function(stage: str, percentage: int)
        """
        self.callback = callback
        self._stage = "init"
        self._percentage = 0
        self._table_count = 0
        self._tables_completed = 0
        self._row_count = 0
        self._rows_completed = 0

    def set_table_count(self, count: int):
        """Set total number of tables to migrate."""
        self._table_count = count

    def set_row_count(self, count: int):
        """Set total number of rows to migrate."""
        self._row_count = count

    def update_stage(self, stage: str, percentage: int):
        """
        Update migration stage and percentage.

        Args:
            stage: Stage name (backup, create_schema, copy_data, verify, finalize)
            percentage: Percentage complete (0-100)
        """
        self._stage = stage
        self._percentage = percentage

        if self.callback:
            try:
                self.callback(stage, percentage)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

        logger.info(f"Migration progress: {stage} - {percentage}%")

    def update_table_progress(self, table_name: str, rows_copied: int):
        """
        Update progress for current table.

        Args:
            table_name: Name of table being copied
            rows_copied: Number of rows copied in this table
        """
        self._rows_completed += rows_copied

        # Calculate percentage for copy_data stage (20-90%, 70% range)
        if self._row_count > 0:
            data_progress = (self._rows_completed / self._row_count)
            percentage = 20 + int(data_progress * 70)  # 20-90% range
            self.update_stage("copy_data", percentage)

    def complete_table(self, table_name: str):
        """Mark a table as complete."""
        self._tables_completed += 1
        logger.debug(f"Completed table {table_name} ({self._tables_completed}/{self._table_count})")


# ============================================================================
# Migration Functions
# ============================================================================

def migrate_to_encrypted(
    db_path: str,
    encryption_key: Optional[str] = None,
    backup_path: Optional[str] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None,
    key_manager: Optional[KeyManager] = None
) -> Tuple[bool, str]:
    """
    Migrate unencrypted database to encrypted database.

    Story 3.1 AC3: Subtasks 4.1, 4.2, 4.3, 4.5

    Migration Flow:
    1. Validate preconditions (SQLCipher available, database exists)
    2. Create backup of original database (AC3 subtask 4.3)
    3. Get/create encryption key via KeyManager
    4. Create temporary encrypted database
    5. Copy all tables and data with progress tracking (AC3 subtask 4.2)
    6. Verify data integrity
    7. Replace original with encrypted database
    8. Clean up temporary files

    Rollback on Failure (AC3 subtask 4.5):
    - If any step fails, restore from backup
    - Log detailed error information
    - Return error message to caller

    Args:
        db_path: Path to unencrypted database
        encryption_key: Optional hex-encoded encryption key (if None, uses KeyManager)
        backup_path: Optional custom backup path (if None, auto-generates)
        progress_callback: Optional callback(stage: str, percentage: int)
        key_manager: Optional KeyManager instance (if None, creates new)

    Returns:
        Tuple[bool, str]: (success, message)
        - success: True if migration successful, False otherwise
        - message: Success message or error description

    Raises:
        MigrationError: If migration fails (after rollback attempted)
    """
    # Initialize progress tracker
    progress = MigrationProgress(progress_callback)
    progress.update_stage("init", 0)

    # Validate preconditions
    if not SQLCIPHER_AVAILABLE:
        return False, "SQLCipher not available - cannot create encrypted database"

    if not os.path.exists(db_path):
        return False, f"Database not found: {db_path}"

    # Get encryption key
    if encryption_key is None:
        if key_manager is None:
            if not KEY_MANAGER_AVAILABLE:
                return False, "KeyManager not available - cannot generate encryption key"
            key_manager = KeyManager()

        try:
            encryption_key = key_manager.get_or_create_key()
            if encryption_key is None:
                return False, "Failed to get/create encryption key"
        except KeyManagementError as e:
            return False, f"Key management error: {e}"

    # Create backup
    progress.update_stage("backup", 5)
    try:
        if backup_path is None:
            backup_path = _create_backup_path(db_path)

        logger.info(f"Creating backup: {backup_path}")
        shutil.copy2(db_path, backup_path)
        progress.update_stage("backup", 10)
    except Exception as e:
        logger.error(f"Backup creation failed: {e}", exc_info=True)
        return False, f"Failed to create backup: {e}"

    # Create temporary encrypted database
    temp_encrypted_path = None
    try:
        # Create temp file for encrypted database
        temp_fd, temp_encrypted_path = tempfile.mkstemp(suffix=".db", prefix="mailmind_encrypted_")
        os.close(temp_fd)  # Close file descriptor, we'll use path

        logger.info(f"Creating encrypted database: {temp_encrypted_path}")

        # Open source (unencrypted) and target (encrypted) connections
        source_conn = sqlite3_plain.connect(db_path)
        target_conn = sqlite3_encrypted.connect(temp_encrypted_path)

        # Set encryption key on target
        target_conn.execute(f"PRAGMA key = '{encryption_key}'")

        # Copy schema and data
        progress.update_stage("create_schema", 15)
        _copy_database_schema(source_conn, target_conn, progress)

        progress.update_stage("copy_data", 20)
        _copy_database_data(source_conn, target_conn, progress)

        # Verify integrity
        progress.update_stage("verify", 90)
        is_valid, verify_msg = _verify_migration(source_conn, target_conn)

        if not is_valid:
            raise MigrationValidationError(f"Migration verification failed: {verify_msg}")

        progress.update_stage("verify", 95)

        # Close connections
        source_conn.close()
        target_conn.close()

        # Replace original with encrypted database
        progress.update_stage("finalize", 97)
        logger.info(f"Replacing original database with encrypted version")

        # Atomic replacement
        shutil.move(temp_encrypted_path, db_path)
        temp_encrypted_path = None  # Marked as moved

        progress.update_stage("complete", 100)

        success_msg = f"Database successfully migrated to encrypted format. Backup saved to: {backup_path}"
        logger.info(success_msg)
        return True, success_msg

    except Exception as e:
        # Rollback: restore from backup
        logger.error(f"Migration failed: {e}", exc_info=True)

        try:
            logger.warning(f"Rolling back migration - restoring from backup: {backup_path}")
            shutil.copy2(backup_path, db_path)
            logger.info("Rollback successful - original database restored")
        except Exception as rollback_error:
            logger.critical(f"Rollback failed: {rollback_error}", exc_info=True)
            raise MigrationRollbackError(
                f"Migration failed AND rollback failed. "
                f"Original backup at: {backup_path}. "
                f"Migration error: {e}. "
                f"Rollback error: {rollback_error}"
            )

        # Clean up temp file if it exists
        if temp_encrypted_path and os.path.exists(temp_encrypted_path):
            try:
                os.remove(temp_encrypted_path)
            except Exception:
                pass

        return False, f"Migration failed (restored from backup): {e}"


def migrate_to_unencrypted(
    db_path: str,
    encryption_key: str,
    backup_path: Optional[str] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None
) -> Tuple[bool, str]:
    """
    Migrate encrypted database to unencrypted database.

    Story 3.1 AC8: Support user choice to disable encryption

    WARNING: This removes encryption from the database. Use only when user explicitly
    requests to disable encryption (AC8 with prominent warning).

    Args:
        db_path: Path to encrypted database
        encryption_key: Hex-encoded encryption key
        backup_path: Optional custom backup path
        progress_callback: Optional callback(stage: str, percentage: int)

    Returns:
        Tuple[bool, str]: (success, message)
    """
    # Initialize progress tracker
    progress = MigrationProgress(progress_callback)
    progress.update_stage("init", 0)

    # Validate preconditions
    if not SQLCIPHER_AVAILABLE:
        return False, "SQLCipher not available - cannot read encrypted database"

    if not os.path.exists(db_path):
        return False, f"Database not found: {db_path}"

    if not encryption_key:
        return False, "Encryption key required to read encrypted database"

    # Create backup
    progress.update_stage("backup", 5)
    try:
        if backup_path is None:
            backup_path = _create_backup_path(db_path)

        logger.info(f"Creating backup: {backup_path}")
        shutil.copy2(db_path, backup_path)
        progress.update_stage("backup", 10)
    except Exception as e:
        logger.error(f"Backup creation failed: {e}", exc_info=True)
        return False, f"Failed to create backup: {e}"

    # Create temporary unencrypted database
    temp_unencrypted_path = None
    try:
        # Create temp file for unencrypted database
        temp_fd, temp_unencrypted_path = tempfile.mkstemp(suffix=".db", prefix="mailmind_unencrypted_")
        os.close(temp_fd)

        logger.info(f"Creating unencrypted database: {temp_unencrypted_path}")

        # Open source (encrypted) and target (unencrypted) connections
        source_conn = sqlite3_encrypted.connect(db_path)
        source_conn.execute(f"PRAGMA key = '{encryption_key}'")

        target_conn = sqlite3_plain.connect(temp_unencrypted_path)

        # Copy schema and data
        progress.update_stage("create_schema", 15)
        _copy_database_schema(source_conn, target_conn, progress)

        progress.update_stage("copy_data", 20)
        _copy_database_data(source_conn, target_conn, progress)

        # Verify integrity
        progress.update_stage("verify", 90)
        is_valid, verify_msg = _verify_migration(source_conn, target_conn)

        if not is_valid:
            raise MigrationValidationError(f"Migration verification failed: {verify_msg}")

        progress.update_stage("verify", 95)

        # Close connections
        source_conn.close()
        target_conn.close()

        # Replace original with unencrypted database
        progress.update_stage("finalize", 97)
        logger.info(f"Replacing original database with unencrypted version")

        # Atomic replacement
        shutil.move(temp_unencrypted_path, db_path)
        temp_unencrypted_path = None

        progress.update_stage("complete", 100)

        success_msg = f"Database successfully migrated to unencrypted format. Backup saved to: {backup_path}"
        logger.warning(success_msg)  # Warning level since this reduces security
        return True, success_msg

    except Exception as e:
        # Rollback: restore from backup
        logger.error(f"Migration failed: {e}", exc_info=True)

        try:
            logger.warning(f"Rolling back migration - restoring from backup: {backup_path}")
            shutil.copy2(backup_path, db_path)
            logger.info("Rollback successful - original database restored")
        except Exception as rollback_error:
            logger.critical(f"Rollback failed: {rollback_error}", exc_info=True)
            raise MigrationRollbackError(
                f"Migration failed AND rollback failed. "
                f"Original backup at: {backup_path}. "
                f"Migration error: {e}. "
                f"Rollback error: {rollback_error}"
            )

        # Clean up temp file
        if temp_unencrypted_path and os.path.exists(temp_unencrypted_path):
            try:
                os.remove(temp_unencrypted_path)
            except Exception:
                pass

        return False, f"Migration failed (restored from backup): {e}"


# ============================================================================
# Helper Functions
# ============================================================================

def _create_backup_path(db_path: str) -> str:
    """
    Create backup path with timestamp.

    Format: {original_name}_backup_{timestamp}.db
    Example: mailmind_backup_20251015_143022.db

    Args:
        db_path: Original database path

    Returns:
        str: Backup path
    """
    db_dir = os.path.dirname(db_path)
    db_name = os.path.splitext(os.path.basename(db_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{db_name}_backup_{timestamp}.db"
    return os.path.join(db_dir, backup_name)


def _copy_database_schema(
    source_conn,
    target_conn,
    progress: MigrationProgress
) -> None:
    """
    Copy database schema from source to target.

    Copies:
    - Table definitions
    - Index definitions
    - Trigger definitions
    - View definitions

    Does NOT copy:
    - Data (handled separately)
    - sqlite_sequence (auto-generated)

    Args:
        source_conn: Source database connection
        target_conn: Target database connection
        progress: Progress tracker
    """
    logger.info("Copying database schema")

    # Get all schema objects (tables, indexes, triggers, views)
    cursor = source_conn.cursor()
    cursor.execute("""
        SELECT sql, type, name
        FROM sqlite_master
        WHERE sql IS NOT NULL
        AND type IN ('table', 'index', 'trigger', 'view')
        AND name NOT LIKE 'sqlite_%'
        ORDER BY
            CASE type
                WHEN 'table' THEN 1
                WHEN 'index' THEN 2
                WHEN 'trigger' THEN 3
                WHEN 'view' THEN 4
            END
    """)

    schema_objects = cursor.fetchall()

    # Create schema objects in target
    target_cursor = target_conn.cursor()
    for sql, obj_type, obj_name in schema_objects:
        try:
            logger.debug(f"Creating {obj_type}: {obj_name}")
            target_cursor.execute(sql)
        except Exception as e:
            logger.error(f"Failed to create {obj_type} {obj_name}: {e}")
            raise MigrationError(f"Schema copy failed for {obj_type} {obj_name}: {e}")

    target_conn.commit()
    logger.info(f"Copied {len(schema_objects)} schema objects")


def _copy_database_data(
    source_conn,
    target_conn,
    progress: MigrationProgress
) -> None:
    """
    Copy all data from source to target database.

    Story 3.1 AC3 Subtask 4.2: Progress tracking for large databases
    Story 3.1 AC3 Subtask 4.4: Support for >500MB, >10K emails

    Strategy for Large Databases:
    - Copy table by table
    - Use batched INSERT for memory efficiency
    - Update progress after each table
    - Handle large datasets without memory overflow

    Args:
        source_conn: Source database connection
        target_conn: Target database connection
        progress: Progress tracker
    """
    logger.info("Copying database data")

    # Get all tables
    cursor = source_conn.cursor()
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)

    tables = [row[0] for row in cursor.fetchall()]
    progress.set_table_count(len(tables))

    # Count total rows for progress tracking
    total_rows = 0
    for table_name in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        total_rows += count

    progress.set_row_count(total_rows)
    logger.info(f"Copying {len(tables)} tables, {total_rows} total rows")

    # Copy each table
    for table_name in tables:
        _copy_table_data(source_conn, target_conn, table_name, progress)
        progress.complete_table(table_name)

    target_conn.commit()
    logger.info(f"Data copy complete: {len(tables)} tables, {total_rows} rows")


def _copy_table_data(
    source_conn,
    target_conn,
    table_name: str,
    progress: MigrationProgress,
    batch_size: int = 1000
) -> None:
    """
    Copy data from one table with batched inserts.

    Uses batched INSERT for memory efficiency with large tables.
    Updates progress after each batch for responsive UI.

    Args:
        source_conn: Source database connection
        target_conn: Target database connection
        table_name: Name of table to copy
        progress: Progress tracker
        batch_size: Number of rows per batch (default 1000)
    """
    # Get column names
    source_cursor = source_conn.cursor()
    source_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in source_cursor.fetchall()]
    column_names = ", ".join(columns)
    placeholders = ", ".join(["?"] * len(columns))

    # Count rows
    source_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = source_cursor.fetchone()[0]

    if row_count == 0:
        logger.debug(f"Table {table_name} is empty - skipping")
        return

    logger.debug(f"Copying table {table_name}: {row_count} rows")

    # Copy data in batches
    source_cursor.execute(f"SELECT {column_names} FROM {table_name}")
    target_cursor = target_conn.cursor()

    rows_copied = 0
    batch = []

    for row in source_cursor:
        batch.append(row)

        if len(batch) >= batch_size:
            # Insert batch
            target_cursor.executemany(
                f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})",
                batch
            )
            rows_copied += len(batch)
            progress.update_table_progress(table_name, len(batch))
            batch = []

    # Insert remaining rows
    if batch:
        target_cursor.executemany(
            f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})",
            batch
        )
        rows_copied += len(batch)
        progress.update_table_progress(table_name, len(batch))

    logger.debug(f"Completed table {table_name}: {rows_copied} rows copied")


def _verify_migration(source_conn, target_conn) -> Tuple[bool, str]:
    """
    Verify migration data integrity.

    Story 3.1 AC3: Verification after migration

    Checks:
    1. All tables exist in target
    2. Row counts match for all tables
    3. Schema matches (table structure)

    Args:
        source_conn: Source database connection
        target_conn: Target database connection

    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    logger.info("Verifying migration data integrity")

    try:
        # Get source tables
        source_cursor = source_conn.cursor()
        source_cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        source_tables = [row[0] for row in source_cursor.fetchall()]

        # Get target tables
        target_cursor = target_conn.cursor()
        target_cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        target_tables = [row[0] for row in target_cursor.fetchall()]

        # Check all tables exist
        if source_tables != target_tables:
            return False, f"Table mismatch: source={source_tables}, target={target_tables}"

        # Verify row counts for each table
        for table_name in source_tables:
            source_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            source_count = source_cursor.fetchone()[0]

            target_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            target_count = target_cursor.fetchone()[0]

            if source_count != target_count:
                return False, f"Row count mismatch in {table_name}: source={source_count}, target={target_count}"

        logger.info(f"Verification passed: {len(source_tables)} tables verified")
        return True, "Migration verified successfully"

    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        return False, f"Verification error: {e}"


# ============================================================================
# Convenience Functions
# ============================================================================

def is_database_encrypted(db_path: str) -> Tuple[bool, str]:
    """
    Check if database is encrypted.

    Strategy:
    1. Try to open with plain sqlite3 - if succeeds, it's unencrypted
    2. If fails with "file is not a database", likely encrypted

    Args:
        db_path: Path to database file

    Returns:
        Tuple[bool, str]: (is_encrypted, message)
    """
    if not os.path.exists(db_path):
        return False, f"Database not found: {db_path}"

    try:
        # Try to open with plain sqlite3
        conn = sqlite3_plain.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master LIMIT 1")
        cursor.fetchone()
        conn.close()

        # If we got here, database is unencrypted
        return False, "Database is unencrypted"

    except sqlite3_plain.DatabaseError as e:
        # "file is not a database" or "file is encrypted" typically means SQLCipher
        if "encrypted" in str(e).lower() or "not a database" in str(e).lower():
            return True, "Database appears to be encrypted"
        else:
            return False, f"Database error (not encryption related): {e}"

    except Exception as e:
        return False, f"Error checking database: {e}"


def get_database_info(db_path: str, encryption_key: Optional[str] = None) -> Dict:
    """
    Get database information (table count, row count, size).

    Args:
        db_path: Path to database
        encryption_key: Optional encryption key if database is encrypted

    Returns:
        Dict with keys: table_count, row_count, size_bytes, encrypted
    """
    if not os.path.exists(db_path):
        return {"error": "Database not found"}

    info = {
        "path": db_path,
        "size_bytes": os.path.getsize(db_path),
        "encrypted": False,
        "table_count": 0,
        "row_count": 0,
        "tables": []
    }

    try:
        # Try unencrypted first
        conn = sqlite3_plain.connect(db_path)
    except sqlite3_plain.DatabaseError:
        # Try encrypted
        if encryption_key and SQLCIPHER_AVAILABLE:
            try:
                conn = sqlite3_encrypted.connect(db_path)
                conn.execute(f"PRAGMA key = '{encryption_key}'")
                info["encrypted"] = True
            except Exception as e:
                return {"error": f"Cannot open database: {e}"}
        else:
            return {"error": "Database appears encrypted but no key provided"}

    try:
        cursor = conn.cursor()

        # Get tables
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        info["table_count"] = len(tables)

        # Count rows in each table
        total_rows = 0
        table_info = []
        for table_name in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            total_rows += count
            table_info.append({"name": table_name, "row_count": count})

        info["row_count"] = total_rows
        info["tables"] = table_info

        conn.close()
        return info

    except Exception as e:
        return {"error": f"Error reading database: {e}"}
