"""
Unit Tests for Database Schema

Tests database schema creation, validation, indexes, constraints, and initialization.

Test Coverage:
- AC1: Complete database schema with 5 tables and indexes
- Schema version tracking
- CHECK constraints validation
- Foreign key constraints
- Index creation and optimization
- Default user preferences initialization
- WAL mode configuration
"""

import sqlite3
import pytest
from pathlib import Path
import tempfile
import os

from mailmind.database.schema import (
    get_schema_statements,
    get_initial_data_statements,
    validate_schema_version,
    get_current_schema_version,
    DEFAULT_PREFERENCES,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def initialized_db(temp_db):
    """Create and initialize a test database with schema."""
    conn = sqlite3.connect(temp_db)

    # Execute schema statements
    for statement in get_schema_statements():
        conn.executescript(statement)

    # Execute initial data statements
    for statement in get_initial_data_statements():
        conn.executescript(statement)

    conn.commit()
    yield conn
    conn.close()


class TestSchemaCreation:
    """Test database schema creation and structure."""

    def test_all_tables_created(self, initialized_db):
        """Test that all 5 core tables are created."""
        cursor = initialized_db.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "email_analysis",
            "performance_metrics",
            "schema_version",
            "user_corrections",
            "user_preferences",
        ]

        assert set(tables) == set(expected_tables), \
            f"Expected tables {expected_tables}, got {tables}"

    def test_email_analysis_structure(self, initialized_db):
        """Test email_analysis table has correct columns."""
        cursor = initialized_db.cursor()
        cursor.execute("PRAGMA table_info(email_analysis)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type

        expected_columns = {
            "id", "message_id", "subject", "sender", "received_date",
            "analysis_json", "priority", "suggested_folder", "confidence_score",
            "sentiment", "processing_time_ms", "model_version", "hardware_profile",
            "processed_date", "user_feedback"
        }

        assert set(columns.keys()) == expected_columns

    def test_performance_metrics_structure(self, initialized_db):
        """Test performance_metrics table has correct columns."""
        cursor = initialized_db.cursor()
        cursor.execute("PRAGMA table_info(performance_metrics)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            "id", "operation", "hardware_config", "model_version",
            "tokens_per_second", "memory_usage_mb", "processing_time_ms",
            "database_size_mb", "timestamp"
        }

        assert set(columns.keys()) == expected_columns

    def test_user_preferences_structure(self, initialized_db):
        """Test user_preferences table has correct columns."""
        cursor = initialized_db.cursor()
        cursor.execute("PRAGMA table_info(user_preferences)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            "key", "value", "default_value", "value_type", "category", "updated_date"
        }

        assert set(columns.keys()) == expected_columns

    def test_user_corrections_structure(self, initialized_db):
        """Test user_corrections table has correct columns."""
        cursor = initialized_db.cursor()
        cursor.execute("PRAGMA table_info(user_corrections)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            "id", "message_id", "correction_type", "original_suggestion",
            "user_choice", "timestamp"
        }

        assert set(columns.keys()) == expected_columns

    def test_schema_version_structure(self, initialized_db):
        """Test schema_version table has correct columns."""
        cursor = initialized_db.cursor()
        cursor.execute("PRAGMA table_info(schema_version)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {"version", "applied_date", "description"}

        assert set(columns.keys()) == expected_columns


class TestIndexes:
    """Test that indexes are created correctly."""

    def test_email_analysis_indexes(self, initialized_db):
        """Test email_analysis table has all required indexes."""
        cursor = initialized_db.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='email_analysis'
            AND name NOT LIKE 'sqlite_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = [
            "idx_email_message_id",
            "idx_email_priority",
            "idx_email_received_date",
            "idx_email_processed_date",
        ]

        assert set(indexes) == set(expected_indexes), \
            f"Expected indexes {expected_indexes}, got {indexes}"

    def test_performance_metrics_indexes(self, initialized_db):
        """Test performance_metrics table has all required indexes."""
        cursor = initialized_db.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='performance_metrics'
            AND name NOT LIKE 'sqlite_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = ["idx_perf_operation", "idx_perf_timestamp"]

        assert set(indexes) == set(expected_indexes)

    def test_user_preferences_indexes(self, initialized_db):
        """Test user_preferences table has all required indexes."""
        cursor = initialized_db.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='user_preferences'
            AND name NOT LIKE 'sqlite_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = ["idx_pref_category"]

        assert set(indexes) == set(expected_indexes)

    def test_user_corrections_indexes(self, initialized_db):
        """Test user_corrections table has all required indexes."""
        cursor = initialized_db.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='user_corrections'
            AND name NOT LIKE 'sqlite_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = [
            "idx_corr_message_id",
            "idx_corr_correction_type",
            "idx_corr_timestamp",
        ]

        assert set(indexes) == set(expected_indexes)


class TestConstraints:
    """Test CHECK and FOREIGN KEY constraints."""

    def test_priority_check_constraint(self, initialized_db):
        """Test priority CHECK constraint enforces valid values."""
        cursor = initialized_db.cursor()

        # Valid priority should succeed
        cursor.execute("""
            INSERT INTO email_analysis (message_id, analysis_json, priority, model_version)
            VALUES ('test-1', '{}', 'High', 'v1.0')
        """)

        # Invalid priority should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO email_analysis (message_id, analysis_json, priority, model_version)
                VALUES ('test-2', '{}', 'Invalid', 'v1.0')
            """)

    def test_sentiment_check_constraint(self, initialized_db):
        """Test sentiment CHECK constraint enforces valid values."""
        cursor = initialized_db.cursor()

        # Valid sentiment should succeed
        cursor.execute("""
            INSERT INTO email_analysis (message_id, analysis_json, sentiment, model_version)
            VALUES ('test-3', '{}', 'positive', 'v1.0')
        """)

        # Invalid sentiment should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO email_analysis (message_id, analysis_json, sentiment, model_version)
                VALUES ('test-4', '{}', 'invalid', 'v1.0')
            """)

    def test_confidence_score_check_constraint(self, initialized_db):
        """Test confidence_score CHECK constraint enforces 0.0-1.0 range."""
        cursor = initialized_db.cursor()

        # Valid confidence score (0.0-1.0) should succeed
        cursor.execute("""
            INSERT INTO email_analysis (message_id, analysis_json, confidence_score, model_version)
            VALUES ('test-5', '{}', 0.85, 'v1.0')
        """)

        # Confidence score > 1.0 should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO email_analysis (message_id, analysis_json, confidence_score, model_version)
                VALUES ('test-6', '{}', 1.5, 'v1.0')
            """)

        # Confidence score < 0.0 should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO email_analysis (message_id, analysis_json, confidence_score, model_version)
                VALUES ('test-7', '{}', -0.1, 'v1.0')
            """)

    def test_value_type_check_constraint(self, initialized_db):
        """Test user_preferences value_type CHECK constraint."""
        cursor = initialized_db.cursor()

        # Valid value_type should succeed
        cursor.execute("""
            INSERT INTO user_preferences (key, value, value_type)
            VALUES ('test_key', 'test_value', 'string')
        """)

        # Invalid value_type should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO user_preferences (key, value, value_type)
                VALUES ('test_key_2', 'test_value', 'invalid_type')
            """)

    def test_foreign_key_constraint(self, initialized_db):
        """Test foreign key constraint on user_corrections.message_id."""
        cursor = initialized_db.cursor()

        # Insert parent record first
        cursor.execute("""
            INSERT INTO email_analysis (message_id, analysis_json, model_version)
            VALUES ('parent-msg-1', '{}', 'v1.0')
        """)

        # Child record with valid FK should succeed
        cursor.execute("""
            INSERT INTO user_corrections (message_id, correction_type, user_choice)
            VALUES ('parent-msg-1', 'priority', 'High')
        """)

        # Child record with invalid FK should fail (if FK enforcement is on)
        # Note: SQLite FK enforcement must be enabled via PRAGMA foreign_keys=ON
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO user_corrections (message_id, correction_type, user_choice)
                VALUES ('nonexistent-msg', 'priority', 'High')
            """)


class TestUniqueConstraints:
    """Test UNIQUE constraints."""

    def test_message_id_unique_constraint(self, initialized_db):
        """Test message_id UNIQUE constraint in email_analysis."""
        cursor = initialized_db.cursor()

        # First insert should succeed
        cursor.execute("""
            INSERT INTO email_analysis (message_id, analysis_json, model_version)
            VALUES ('unique-msg-1', '{}', 'v1.0')
        """)

        # Duplicate message_id should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO email_analysis (message_id, analysis_json, model_version)
                VALUES ('unique-msg-1', '{}', 'v1.0')
            """)

    def test_preference_key_unique_constraint(self, initialized_db):
        """Test key UNIQUE constraint (PRIMARY KEY) in user_preferences."""
        cursor = initialized_db.cursor()

        # First insert should succeed
        cursor.execute("""
            INSERT INTO user_preferences (key, value, value_type)
            VALUES ('unique_pref_1', 'value1', 'string')
        """)

        # Duplicate key should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO user_preferences (key, value, value_type)
                VALUES ('unique_pref_1', 'value2', 'string')
            """)


class TestSchemaVersion:
    """Test schema version tracking."""

    def test_schema_version_initialized(self, initialized_db):
        """Test that schema version is initialized to 1."""
        assert validate_schema_version(initialized_db)

        version = get_current_schema_version(initialized_db)
        assert version == 1

    def test_schema_version_table_structure(self, initialized_db):
        """Test schema_version table has correct structure."""
        cursor = initialized_db.cursor()
        cursor.execute("SELECT version, description FROM schema_version WHERE version = 1")
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == 1
        assert "Initial schema" in result[1]


class TestDefaultPreferences:
    """Test default user preferences initialization."""

    def test_default_preferences_inserted(self, initialized_db):
        """Test that all default preferences are inserted."""
        cursor = initialized_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_preferences")
        count = cursor.fetchone()[0]

        expected_count = len(DEFAULT_PREFERENCES)
        assert count == expected_count, \
            f"Expected {expected_count} default preferences, got {count}"

    def test_default_preference_values(self, initialized_db):
        """Test that default preference values are correct."""
        cursor = initialized_db.cursor()

        for key, expected_value, expected_default, expected_type, expected_category in DEFAULT_PREFERENCES:
            cursor.execute("""
                SELECT value, default_value, value_type, category
                FROM user_preferences
                WHERE key = ?
            """, (key,))
            result = cursor.fetchone()

            assert result is not None, f"Preference '{key}' not found"
            assert result[0] == expected_value, f"Wrong value for '{key}'"
            assert result[1] == expected_default, f"Wrong default for '{key}'"
            assert result[2] == expected_type, f"Wrong type for '{key}'"
            assert result[3] == expected_category, f"Wrong category for '{key}'"


class TestWALMode:
    """Test WAL mode configuration."""

    def test_wal_mode_enabled(self, initialized_db):
        """Test that WAL mode is enabled."""
        cursor = initialized_db.cursor()
        cursor.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]

        assert mode.upper() == "WAL", f"Expected WAL mode, got {mode}"

    def test_foreign_keys_enabled(self, initialized_db):
        """Test that foreign key enforcement is enabled."""
        cursor = initialized_db.cursor()
        cursor.execute("PRAGMA foreign_keys")
        enabled = cursor.fetchone()[0]

        assert enabled == 1, "Foreign keys should be enabled"


class TestIdempotency:
    """Test that schema creation is idempotent."""

    def test_schema_creation_idempotent(self, temp_db):
        """Test that creating schema twice doesn't cause errors."""
        conn = sqlite3.connect(temp_db)

        # Create schema first time
        for statement in get_schema_statements():
            conn.executescript(statement)

        # Create schema second time (should not raise errors)
        for statement in get_schema_statements():
            conn.executescript(statement)

        # Verify tables still exist
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        count = cursor.fetchone()[0]

        assert count == 5  # 5 core tables

        conn.close()
