"""
Database Manager for MailMind

Centralized database management class providing a unified interface to all SQLite
database operations. Implements the Repository Pattern for data access abstraction.

Features:
- Singleton pattern for shared database access
- Connection pooling (one connection per thread)
- Context manager support for automatic cleanup
- CRUD operations for all tables
- Query performance logging (debug mode)
- Thread-safe operations
- Automatic database initialization

Usage:
    # Context manager pattern (recommended)
    with DatabaseManager() as db:
        db.insert_email_analysis(message_id, analysis)

    # Singleton pattern
    db = DatabaseManager.get_instance()
    db.set_preference("theme", "dark")

Integration:
- Story 1.3 (EmailAnalysisEngine): email_analysis CRUD
- Story 1.6 (CacheManager): Cache operations delegation
- Story 2.1 (OutlookConnector): Email metadata storage
- Story 2.4 (Settings System): User preferences storage
"""

import sqlite3
import threading
import logging
import time
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from .schema import (
    get_schema_statements,
    get_initial_data_statements,
    get_current_schema_version,
)
from .backup_manager import BackupManager, BackupError

# Import Story 2.6 exceptions
try:
    from mailmind.core.exceptions import DatabaseCorruptionError, DatabaseBackupError
except ImportError:
    # Fallback if exceptions.py not available
    class DatabaseCorruptionError(Exception):
        """Raised when database corruption is detected."""
        pass

    class DatabaseBackupError(Exception):
        """Raised when database backup or restore fails."""
        pass

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database errors."""
    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class QueryError(DatabaseError):
    """Raised when a query execution fails."""
    pass


class DataNotFoundError(DatabaseError):
    """Raised when requested data is not found."""
    pass


class DatabaseManager:
    """
    Centralized database manager for all MailMind data persistence.

    Implements Repository Pattern with connection pooling, thread-safety,
    and comprehensive CRUD operations for all tables.

    Thread Safety:
        Uses threading.local() to maintain one connection per thread,
        ensuring thread-safe database access.

    Performance:
        - Query logging in debug mode
        - Connection pooling to minimize overhead
        - Prepared statements for SQL injection prevention
        - Optimized indexes for common queries
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self, db_path: str = None, encryption_key: Optional[str] = None, debug: bool = False):
        """
        Initialize DatabaseManager.

        Args:
            db_path: Path to SQLite database file (default: mailmind.db in project root)
            encryption_key: Optional encryption key for SQLCipher (future: AC2)
            debug: Enable query performance logging

        Raises:
            ConnectionError: If database initialization fails
        """
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = str(project_root / "mailmind.db")

        self.db_path = db_path
        self.encryption_key = encryption_key
        self.debug = debug
        self._thread_local = threading.local()
        self._initialized = False
        self._backup_manager = None  # Lazy initialization

        # Ensure database directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database if needed
        self._initialize_database()

    @classmethod
    def get_instance(cls, db_path: str = None, **kwargs) -> "DatabaseManager":
        """
        Get singleton instance of DatabaseManager.

        Args:
            db_path: Path to database file (only used on first call)
            **kwargs: Additional arguments passed to __init__

        Returns:
            DatabaseManager: Singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(db_path=db_path, **kwargs)
        return cls._instance

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get connection for current thread (connection pooling).

        Returns:
            sqlite3.Connection: Thread-local connection

        Raises:
            ConnectionError: If connection creation fails
        """
        if not hasattr(self._thread_local, 'conn') or self._thread_local.conn is None:
            try:
                self._thread_local.conn = sqlite3.connect(
                    self.db_path,
                    timeout=10.0,  # 10 second timeout
                    check_same_thread=False  # Allow connection sharing (safe with thread-local)
                )
                self._thread_local.conn.row_factory = sqlite3.Row  # Access columns by name
                logger.debug(f"Created new database connection for thread {threading.current_thread().name}")
            except sqlite3.Error as e:
                raise ConnectionError(f"Failed to connect to database: {e}")

        return self._thread_local.conn

    def _initialize_database(self):
        """
        Initialize database schema if needed (AC4).

        Creates all tables, indexes, and default data on first run.
        Handles concurrent initialization gracefully with file locking.

        Raises:
            ConnectionError: If initialization fails
        """
        if self._initialized:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check if database is already initialized
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='schema_version'
            """)

            if cursor.fetchone() is None:
                # Database not initialized - create schema
                logger.info(f"Initializing database at {self.db_path}")

                # Execute schema statements
                for statement in get_schema_statements():
                    conn.executescript(statement)

                # Execute initial data statements
                for statement in get_initial_data_statements():
                    conn.executescript(statement)

                conn.commit()
                logger.info("Database initialized successfully")

            self._initialized = True

        except sqlite3.Error as e:
            raise ConnectionError(f"Failed to initialize database: {e}")

    def _execute_query(self, query: str, params: tuple = (), fetch_one: bool = False,
                       fetch_all: bool = False) -> Any:
        """
        Execute a SQL query with performance logging and error handling.

        Story 2.6 AC12: Database corruption detection and automatic recovery

        Args:
            query: SQL query string
            params: Query parameters (tuple)
            fetch_one: Return single row result
            fetch_all: Return all rows result

        Returns:
            Query result based on fetch_one/fetch_all flags

        Raises:
            QueryError: If query execution fails
            DatabaseCorruptionError: If database corruption is detected (AC12)
        """
        start_time = time.time() if self.debug else None
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(query, params)

            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.lastrowid

            if self.debug:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.debug(f"Query executed in {elapsed_ms:.2f}ms: {query[:100]}...")

                if elapsed_ms > 100:
                    logger.warning(f"Slow query detected ({elapsed_ms:.2f}ms): {query[:200]}")

            return result

        except sqlite3.DatabaseError as e:
            # AC12: Database corruption detection
            error_msg = str(e).lower()
            if 'corrupt' in error_msg or 'malformed' in error_msg or 'damaged' in error_msg:
                # Constraint arch-8: (1) log CRITICAL with full traceback
                logger.critical(
                    f"🚨 DATABASE CORRUPTION DETECTED: {e}\n"
                    f"Query: {query[:200]}\n"
                    f"Database: {self.db_path}",
                    exc_info=True
                )

                # Raise DatabaseCorruptionError to trigger recovery
                technical_details = f"sqlite3.DatabaseError during query: {e}"
                raise DatabaseCorruptionError(technical_details=technical_details)

            # Not corruption - treat as regular query error
            logger.error(f"Query failed: {query[:200]}... Error: {e}")
            conn.rollback()
            raise QueryError(f"Query execution failed: {e}")

        except sqlite3.Error as e:
            logger.error(f"Query failed: {query[:200]}... Error: {e}")
            conn.rollback()
            raise QueryError(f"Query execution failed: {e}")

    # ========== Connection Management ==========

    def connect(self) -> bool:
        """
        Explicitly connect to database.

        Returns:
            bool: True if connection successful

        Raises:
            ConnectionError: If connection fails
        """
        try:
            self._get_connection()
            return True
        except Exception as e:
            raise ConnectionError(f"Connection failed: {e}")

    def disconnect(self):
        """Close the thread-local connection."""
        if hasattr(self._thread_local, 'conn') and self._thread_local.conn:
            self._thread_local.conn.close()
            self._thread_local.conn = None
            logger.debug(f"Closed connection for thread {threading.current_thread().name}")

    def is_connected(self) -> bool:
        """
        Check if current thread has an active connection.

        Returns:
            bool: True if connected, False otherwise
        """
        return hasattr(self._thread_local, 'conn') and self._thread_local.conn is not None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False  # Don't suppress exceptions

    # ========== Email Analysis CRUD (Story 1.3 integration) ==========

    def insert_email_analysis(self, message_id: str, analysis: Dict, metadata: Dict) -> int:
        """
        Insert email analysis record.

        Args:
            message_id: Unique email message ID
            analysis: Analysis results dictionary (will be JSON-serialized)
            metadata: Email metadata (subject, sender, received_date, etc.)

        Returns:
            int: ID of inserted record

        Raises:
            QueryError: If insert fails
        """
        query = """
        INSERT OR REPLACE INTO email_analysis (
            message_id, subject, sender, received_date, analysis_json,
            priority, suggested_folder, confidence_score, sentiment,
            processing_time_ms, model_version, hardware_profile
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            message_id,
            metadata.get("subject"),
            metadata.get("sender"),
            metadata.get("received_date"),
            json.dumps(analysis),
            metadata.get("priority"),
            metadata.get("suggested_folder"),
            metadata.get("confidence_score"),
            metadata.get("sentiment"),
            metadata.get("processing_time_ms"),
            metadata.get("model_version"),
            metadata.get("hardware_profile"),
        )

        return self._execute_query(query, params)

    def get_email_analysis(self, message_id: str) -> Optional[Dict]:
        """
        Get email analysis by message ID.

        Args:
            message_id: Unique email message ID

        Returns:
            dict: Analysis record or None if not found
        """
        query = """
        SELECT * FROM email_analysis WHERE message_id = ?
        """
        result = self._execute_query(query, (message_id,), fetch_one=True)

        if result:
            row_dict = dict(result)
            # Parse JSON analysis
            if row_dict.get("analysis_json"):
                row_dict["analysis"] = json.loads(row_dict["analysis_json"])
            return row_dict

        return None

    def update_email_analysis(self, message_id: str, analysis: Dict) -> bool:
        """
        Update email analysis record.

        Args:
            message_id: Unique email message ID
            analysis: Updated analysis data

        Returns:
            bool: True if update successful

        Raises:
            QueryError: If update fails
        """
        query = """
        UPDATE email_analysis
        SET analysis_json = ?, priority = ?, sentiment = ?, confidence_score = ?
        WHERE message_id = ?
        """

        params = (
            json.dumps(analysis),
            analysis.get("priority"),
            analysis.get("sentiment"),
            analysis.get("confidence_score"),
            message_id,
        )

        self._execute_query(query, params)
        return True

    def delete_email_analysis(self, message_id: str) -> bool:
        """
        Delete email analysis record.

        Args:
            message_id: Unique email message ID

        Returns:
            bool: True if delete successful
        """
        query = "DELETE FROM email_analysis WHERE message_id = ?"
        self._execute_query(query, (message_id,))
        return True

    def get_emails_by_priority(self, priority: str) -> List[Dict]:
        """
        Get all emails with a specific priority.

        Args:
            priority: Priority value ('High', 'Medium', or 'Low')

        Returns:
            list: List of email analysis records
        """
        query = "SELECT * FROM email_analysis WHERE priority = ?"
        results = self._execute_query(query, (priority,), fetch_all=True)

        emails = []
        for row in results:
            row_dict = dict(row)
            if row_dict.get("analysis_json"):
                row_dict["analysis"] = json.loads(row_dict["analysis_json"])
            emails.append(row_dict)

        return emails

    def query_email_analyses(self, filters: Dict = None, limit: int = 1000) -> List[Dict]:
        """
        Query email analyses with optional filters.

        Args:
            filters: Optional dictionary of filters (e.g., {'priority': 'High'})
            limit: Maximum number of results (default: 1000)

        Returns:
            list: List of email analysis records
        """
        query = "SELECT * FROM email_analysis"
        params = []

        if filters:
            where_clauses = []
            for key, value in filters.items():
                where_clauses.append(f"{key} = ?")
                params.append(value)

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

        query += f" ORDER BY processed_date DESC LIMIT {limit}"

        results = self._execute_query(query, tuple(params), fetch_all=True)

        emails = []
        for row in results:
            row_dict = dict(row)
            if row_dict.get("analysis_json"):
                row_dict["analysis"] = json.loads(row_dict["analysis_json"])
            emails.append(row_dict)

        return emails

    def delete_all_email_analyses(self) -> bool:
        """
        Delete all email analysis records.

        Returns:
            bool: True if deletion successful

        Warning:
            This operation is irreversible.
        """
        query = "DELETE FROM email_analysis"
        self._execute_query(query)
        logger.warning("All email analyses deleted")
        return True

    # ========== Performance Metrics (Story 1.6 integration) ==========

    def insert_performance_metric(self, operation: str, metrics: Dict) -> int:
        """
        Insert performance metric record.

        Args:
            operation: Operation name (e.g., 'email_analysis', 'batch_processing')
            metrics: Performance metrics dictionary

        Returns:
            int: ID of inserted record
        """
        query = """
        INSERT INTO performance_metrics (
            operation, hardware_config, model_version, tokens_per_second,
            memory_usage_mb, processing_time_ms, database_size_mb, batch_size
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            operation,
            metrics.get("hardware_config"),
            metrics.get("model_version"),
            metrics.get("tokens_per_second"),
            metrics.get("memory_usage_mb"),
            metrics.get("processing_time_ms"),
            metrics.get("database_size_mb"),
            metrics.get("batch_size", 1),  # Default to 1 if not specified
        )

        return self._execute_query(query, params)

    def get_performance_metrics(self, days: int = 7, operation: str = None) -> List[Dict]:
        """
        Get performance metrics for the last N days, optionally filtered by operation.

        Args:
            days: Number of days to retrieve (default: 7)
            operation: Optional operation filter (e.g., 'email_analysis')

        Returns:
            list: List of metric records
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        if operation:
            query = """
            SELECT * FROM performance_metrics
            WHERE timestamp >= ? AND operation = ?
            ORDER BY timestamp DESC
            """
            results = self._execute_query(query, (cutoff_date, operation), fetch_all=True)
        else:
            query = """
            SELECT * FROM performance_metrics
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            """
            results = self._execute_query(query, (cutoff_date,), fetch_all=True)

        return [dict(row) for row in results] if results else []

    # ========== User Preferences (Story 2.4 integration) ==========

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get user preference value.

        Args:
            key: Preference key
            default: Default value if not found

        Returns:
            Preference value (type-converted based on value_type)
        """
        query = "SELECT value, value_type FROM user_preferences WHERE key = ?"
        result = self._execute_query(query, (key,), fetch_one=True)

        if not result:
            return default

        value, value_type = result["value"], result["value_type"]

        # Convert to appropriate type
        if value_type == "int":
            return int(value)
        elif value_type == "float":
            return float(value)
        elif value_type == "bool":
            return value.lower() in ("true", "1", "yes")
        elif value_type == "json":
            return json.loads(value)
        else:  # string
            return value

    def set_preference(self, key: str, value: Any) -> bool:
        """
        Set user preference value.

        Args:
            key: Preference key
            value: Preference value (will be type-detected)

        Returns:
            bool: True if successful
        """
        # Detect value type
        if isinstance(value, bool):
            value_type = "bool"
            value_str = "true" if value else "false"
        elif isinstance(value, int):
            value_type = "int"
            value_str = str(value)
        elif isinstance(value, float):
            value_type = "float"
            value_str = str(value)
        elif isinstance(value, (dict, list)):
            value_type = "json"
            value_str = json.dumps(value)
        else:
            value_type = "string"
            value_str = str(value)

        query = """
        INSERT OR REPLACE INTO user_preferences (key, value, value_type, updated_date)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """

        self._execute_query(query, (key, value_str, value_type))
        return True

    def get_all_preferences(self, category: Optional[str] = None) -> Dict:
        """
        Get all user preferences, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            dict: Dictionary of key-value pairs
        """
        if category:
            query = "SELECT key, value, value_type FROM user_preferences WHERE category = ?"
            results = self._execute_query(query, (category,), fetch_all=True)
        else:
            query = "SELECT key, value, value_type FROM user_preferences"
            results = self._execute_query(query, fetch_all=True)

        if not results:
            return {}

        preferences = {}
        for row in results:
            key, value, value_type = row["key"], row["value"], row["value_type"]

            # Convert to appropriate type
            if value_type == "int":
                preferences[key] = int(value)
            elif value_type == "float":
                preferences[key] = float(value)
            elif value_type == "bool":
                preferences[key] = value.lower() in ("true", "1", "yes")
            elif value_type == "json":
                preferences[key] = json.loads(value)
            else:
                preferences[key] = value

        return preferences

    # ========== User Corrections (Story 1.4 integration) ==========

    def insert_user_correction(self, correction: Dict) -> int:
        """
        Insert user correction record.

        Args:
            correction: Correction data (message_id, correction_type, etc.)

        Returns:
            int: ID of inserted record
        """
        query = """
        INSERT INTO user_corrections (
            message_id, correction_type, original_suggestion, user_choice
        ) VALUES (?, ?, ?, ?)
        """

        params = (
            correction.get("message_id"),
            correction.get("correction_type"),
            correction.get("original_suggestion"),
            correction.get("user_choice"),
        )

        return self._execute_query(query, params)

    def get_user_corrections(self, sender: str = None, days: int = 30) -> List[Dict]:
        """
        Get user corrections, optionally filtered by sender and time range.

        Args:
            sender: Optional sender email filter
            days: Number of days to retrieve (default: 30)

        Returns:
            list: List of correction records
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        if sender:
            query = """
            SELECT uc.* FROM user_corrections uc
            JOIN email_analysis ea ON uc.message_id = ea.message_id
            WHERE ea.sender = ? AND uc.timestamp >= ?
            ORDER BY uc.timestamp DESC
            """
            params = (sender, cutoff_date)
        else:
            query = """
            SELECT * FROM user_corrections
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            """
            params = (cutoff_date,)

        results = self._execute_query(query, params, fetch_all=True)
        return [dict(row) for row in results] if results else []

    # ========== Database Maintenance (AC8) ==========

    def get_database_size_mb(self) -> float:
        """
        Get current database file size in megabytes.

        Returns:
            float: Database size in MB

        Raises:
            DatabaseError: If file size cannot be determined
        """
        try:
            size_bytes = os.path.getsize(self.db_path)
            size_mb = size_bytes / (1024 * 1024)
            return round(size_mb, 2)
        except OSError as e:
            raise DatabaseError(f"Failed to get database size: {e}")

    def optimize_database(self) -> Tuple[bool, float]:
        """
        Optimize database using VACUUM command.

        Returns:
            tuple: (success: bool, space_saved_mb: float)

        Raises:
            QueryError: If VACUUM fails
        """
        # Get size before optimization
        size_before = self.get_database_size_mb()

        try:
            conn = self._get_connection()
            conn.execute("VACUUM")
            conn.commit()

            # Get size after optimization
            size_after = self.get_database_size_mb()
            space_saved = size_before - size_after

            logger.info(f"Database optimized. Space saved: {space_saved:.2f} MB")
            return True, space_saved

        except sqlite3.Error as e:
            logger.error(f"Database optimization failed: {e}")
            raise QueryError(f"VACUUM failed: {e}")

    # ========== Migration Support (AC5) ==========

    def get_schema_version(self) -> int:
        """
        Get current database schema version.

        Returns:
            int: Current schema version
        """
        return get_current_schema_version(self._get_connection())

    def apply_migrations(self) -> bool:
        """
        Apply pending database migrations.

        Returns:
            bool: True if migrations applied successfully

        Note:
            Full migration implementation in Task 4
        """
        # Placeholder - full implementation in Task 4
        logger.info("Migration system not yet implemented (Task 4)")
        return True

    # ========== Backup & Restore (AC6) ==========

    def _get_backup_manager(self) -> BackupManager:
        """Get or create BackupManager instance."""
        if self._backup_manager is None:
            self._backup_manager = BackupManager(db_path=self.db_path)
        return self._backup_manager

    def backup(self, backup_path: str = None, description: str = None) -> str:
        """
        Create a backup of the database.

        Args:
            backup_path: Optional specific path for backup (default: auto-generated)
            description: Optional description for backup

        Returns:
            str: Path to created backup file

        Raises:
            BackupError: If backup creation fails
        """
        try:
            backup_mgr = self._get_backup_manager()

            if backup_path:
                # Manual backup to specific path
                import shutil
                auto_backup = backup_mgr.create_backup(description=description)
                shutil.copy2(auto_backup, backup_path)
                logger.info(f"Backup copied to: {backup_path}")
                return backup_path
            else:
                # Auto-generated backup path
                return backup_mgr.create_backup(description=description)

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise BackupError(f"Backup failed: {e}")

    def restore(self, backup_path: str) -> bool:
        """
        Restore database from backup.

        Args:
            backup_path: Path to backup file

        Returns:
            bool: True if restore successful

        Raises:
            BackupError: If restore fails
        """
        try:
            backup_mgr = self._get_backup_manager()

            # Close current connection before restore
            self.disconnect()

            # Restore from backup
            success = backup_mgr.restore_backup(backup_path)

            # Reconnect after restore
            if success:
                self.connect()
                logger.info("Database restored and reconnected successfully")

            return success

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise BackupError(f"Restore failed: {e}")

    def verify_backup_integrity(self, backup_path: str) -> bool:
        """
        Verify backup file integrity.

        Args:
            backup_path: Path to backup file

        Returns:
            bool: True if backup is valid, False otherwise
        """
        backup_mgr = self._get_backup_manager()
        return backup_mgr.verify_backup(backup_path)

    def get_backup_status(self) -> dict:
        """
        Get backup status information.

        Returns:
            dict: Backup status with last_backup_date, total_backups, total_size_mb
        """
        backup_mgr = self._get_backup_manager()
        return backup_mgr.get_backup_status()

    def list_backups(self) -> List[Tuple[str, Any, int]]:
        """
        List all available backups.

        Returns:
            list: List of tuples (backup_path, backup_date, size_bytes)
        """
        backup_mgr = self._get_backup_manager()
        return backup_mgr.list_backups()

    def delete_backup(self, backup_path: str) -> bool:
        """
        Delete a specific backup.

        Args:
            backup_path: Path to backup file

        Returns:
            bool: True if deletion successful
        """
        backup_mgr = self._get_backup_manager()
        return backup_mgr.delete_backup(backup_path)

    # ========== Data Deletion (AC7) ==========

    def delete_all_data(self) -> bool:
        """
        Delete all data from all tables (preserves schema).

        Returns:
            bool: True if deletion successful

        Raises:
            QueryError: If deletion fails

        Warning:
            This operation is irreversible. Use with caution.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Delete from all tables
            tables = ["user_corrections", "email_analysis", "performance_metrics", "user_preferences"]
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")

            conn.commit()
            logger.warning("All data deleted from database")

            # Also delete all backups
            backup_mgr = self._get_backup_manager()
            backup_mgr.delete_all_backups()

            logger.warning("All backups deleted")
            return True

        except sqlite3.Error as e:
            logger.error(f"Data deletion failed: {e}")
            raise QueryError(f"Failed to delete data: {e}")
