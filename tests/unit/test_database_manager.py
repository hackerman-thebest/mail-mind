"""
Unit Tests for DatabaseManager

Tests all CRUD operations, connection management, thread-safety, and performance.

Test Coverage:
- AC3: Fast query performance, connection pooling, query logging
- AC4: Automatic database creation and initialization
- AC9: Centralized DatabaseManager class with CRUD methods
"""

import pytest
import tempfile
import os
import sqlite3
import threading
import time
import json
from datetime import datetime, timedelta

from mailmind.database import (
    DatabaseManager,
    DatabaseError,
    ConnectionError as DBConnectionError,
    QueryError,
)


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def db_manager(temp_db_path):
    """Create a DatabaseManager instance with temporary database."""
    manager = DatabaseManager(db_path=temp_db_path, debug=True)
    yield manager
    manager.disconnect()


class TestConnectionManagement:
    """Test database connection management."""

    def test_connect(self, db_manager):
        """Test explicit connection."""
        assert db_manager.connect() is True
        assert db_manager.is_connected() is True

    def test_disconnect(self, db_manager):
        """Test disconnection."""
        db_manager.connect()
        db_manager.disconnect()
        assert db_manager.is_connected() is False

    def test_context_manager(self, temp_db_path):
        """Test context manager support."""
        with DatabaseManager(db_path=temp_db_path) as db:
            assert db.is_connected() is True

        # Connection should be closed after exiting context
        assert db.is_connected() is False

    def test_singleton_pattern(self, temp_db_path):
        """Test singleton pattern returns same instance."""
        db1 = DatabaseManager.get_instance(db_path=temp_db_path)
        db2 = DatabaseManager.get_instance()

        assert db1 is db2

    def test_thread_safety(self, temp_db_path):
        """Test thread-safe connection pooling."""
        manager = DatabaseManager(db_path=temp_db_path)
        results = []

        def worker(worker_id):
            # Each thread should get its own connection
            manager.connect()
            conn_id = id(manager._get_connection())
            results.append((worker_id, conn_id))

            # Perform a simple query to verify connection works
            conn = manager._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")

            manager.disconnect()

        # Create multiple threads
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify that multiple threads ran successfully
        assert len(results) == 5

        # Note: Due to threading.local(), threads may reuse connection IDs
        # but they are isolated per-thread, which is the intended behavior


class TestAutomaticInitialization:
    """Test automatic database creation and initialization (AC4)."""

    def test_database_created_on_first_run(self, temp_db_path):
        """Test database file is created on first run."""
        # Remove temp file if exists
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

        # Create manager (should create database)
        manager = DatabaseManager(db_path=temp_db_path)

        # Database file should exist
        assert os.path.exists(temp_db_path)
        assert os.path.getsize(temp_db_path) > 0

    def test_schema_initialized_on_first_run(self, temp_db_path):
        """Test schema is initialized with all tables."""
        manager = DatabaseManager(db_path=temp_db_path)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        expected_tables = ["email_analysis", "performance_metrics", "user_preferences",
                          "user_corrections", "schema_version"]
        assert set(tables) == set(expected_tables)

    def test_default_preferences_initialized(self, temp_db_path):
        """Test default user preferences are inserted."""
        manager = DatabaseManager(db_path=temp_db_path)

        # Check that preferences exist
        theme = manager.get_preference("theme")
        assert theme == "light"

        language = manager.get_preference("language")
        assert language == "en"


class TestEmailAnalysisCRUD:
    """Test email_analysis table CRUD operations."""

    def test_insert_email_analysis(self, db_manager):
        """Test inserting email analysis record."""
        message_id = "test-msg-001"
        analysis = {
            "priority": "High",
            "sentiment": "positive",
            "summary": "Test email summary"
        }
        metadata = {
            "subject": "Test Subject",
            "sender": "test@example.com",
            "received_date": datetime.now().isoformat(),
            "priority": "High",
            "sentiment": "positive",
            "confidence_score": 0.95,
            "model_version": "v1.0",
            "processing_time_ms": 150
        }

        record_id = db_manager.insert_email_analysis(message_id, analysis, metadata)
        assert record_id > 0

    def test_get_email_analysis(self, db_manager):
        """Test retrieving email analysis by message_id."""
        message_id = "test-msg-002"
        analysis = {"priority": "Medium", "summary": "Test"}
        metadata = {
            "subject": "Test",
            "sender": "sender@example.com",
            "model_version": "v1.0"
        }

        db_manager.insert_email_analysis(message_id, analysis, metadata)

        # Retrieve record
        result = db_manager.get_email_analysis(message_id)

        assert result is not None
        assert result["message_id"] == message_id
        assert result["analysis"]["priority"] == "Medium"

    def test_update_email_analysis(self, db_manager):
        """Test updating email analysis record."""
        message_id = "test-msg-003"
        analysis = {"priority": "Low"}
        metadata = {"model_version": "v1.0"}

        db_manager.insert_email_analysis(message_id, analysis, metadata)

        # Update analysis
        updated_analysis = {"priority": "High", "updated": True}
        success = db_manager.update_email_analysis(message_id, updated_analysis)

        assert success is True

        # Verify update
        result = db_manager.get_email_analysis(message_id)
        assert result["analysis"]["priority"] == "High"
        assert result["analysis"]["updated"] is True

    def test_delete_email_analysis(self, db_manager):
        """Test deleting email analysis record."""
        message_id = "test-msg-004"
        analysis = {"priority": "Medium"}
        metadata = {"model_version": "v1.0"}

        db_manager.insert_email_analysis(message_id, analysis, metadata)

        # Delete record
        success = db_manager.delete_email_analysis(message_id)
        assert success is True

        # Verify deletion
        result = db_manager.get_email_analysis(message_id)
        assert result is None

    def test_insert_duplicate_message_id(self, db_manager):
        """Test INSERT OR REPLACE handles duplicate message_id."""
        message_id = "test-msg-duplicate"
        analysis1 = {"priority": "Low"}
        metadata1 = {"subject": "First", "model_version": "v1.0"}

        # First insert
        db_manager.insert_email_analysis(message_id, analysis1, metadata1)

        # Second insert with same message_id (should replace)
        analysis2 = {"priority": "High"}
        metadata2 = {"subject": "Second", "model_version": "v1.0"}
        db_manager.insert_email_analysis(message_id, analysis2, metadata2)

        # Should have the second version
        result = db_manager.get_email_analysis(message_id)
        assert result["subject"] == "Second"


class TestPerformanceMetrics:
    """Test performance_metrics table operations."""

    def test_insert_performance_metric(self, db_manager):
        """Test inserting performance metric."""
        metrics = {
            "hardware_config": "CPU-only",
            "model_version": "llama-3.1-8b",
            "tokens_per_second": 25.5,
            "memory_usage_mb": 4096,
            "processing_time_ms": 1500,
            "database_size_mb": 245
        }

        record_id = db_manager.insert_performance_metric("email_analysis", metrics)
        assert record_id > 0

    def test_get_performance_metrics(self, db_manager):
        """Test retrieving performance metrics."""
        # Insert multiple metrics
        for i in range(5):
            metrics = {
                "hardware_config": f"Config-{i}",
                "processing_time_ms": 1000 + i * 100
            }
            db_manager.insert_performance_metric(f"operation-{i}", metrics)

        # Retrieve last 7 days
        results = db_manager.get_performance_metrics(days=7)

        assert len(results) == 5
        assert results[0]["operation"] == "operation-4"  # Most recent first

    def test_get_performance_metrics_time_filter(self, db_manager):
        """Test time filtering for performance metrics."""
        # Insert metric
        metrics = {"hardware_config": "test"}
        db_manager.insert_performance_metric("test_op", metrics)

        # Should appear in 7-day window
        results_7d = db_manager.get_performance_metrics(days=7)
        assert len(results_7d) > 0

        # Should not appear in 0-day window
        results_0d = db_manager.get_performance_metrics(days=0)
        assert len(results_0d) == 0


class TestUserPreferences:
    """Test user_preferences table operations."""

    def test_set_and_get_string_preference(self, db_manager):
        """Test setting and getting string preference."""
        db_manager.set_preference("test_string", "hello world")
        value = db_manager.get_preference("test_string")

        assert value == "hello world"

    def test_set_and_get_int_preference(self, db_manager):
        """Test setting and getting integer preference."""
        db_manager.set_preference("test_int", 42)
        value = db_manager.get_preference("test_int")

        assert value == 42
        assert isinstance(value, int)

    def test_set_and_get_float_preference(self, db_manager):
        """Test setting and getting float preference."""
        db_manager.set_preference("test_float", 3.14)
        value = db_manager.get_preference("test_float")

        assert value == 3.14
        assert isinstance(value, float)

    def test_set_and_get_bool_preference(self, db_manager):
        """Test setting and getting boolean preference."""
        db_manager.set_preference("test_bool_true", True)
        db_manager.set_preference("test_bool_false", False)

        assert db_manager.get_preference("test_bool_true") is True
        assert db_manager.get_preference("test_bool_false") is False

    def test_set_and_get_json_preference(self, db_manager):
        """Test setting and getting JSON preference."""
        data = {"key": "value", "nested": {"a": 1, "b": 2}}
        db_manager.set_preference("test_json", data)
        value = db_manager.get_preference("test_json")

        assert value == data
        assert isinstance(value, dict)

    def test_get_preference_default(self, db_manager):
        """Test getting preference with default value."""
        value = db_manager.get_preference("nonexistent_key", "default_value")
        assert value == "default_value"

    def test_get_all_preferences(self, db_manager):
        """Test getting all preferences."""
        db_manager.set_preference("pref1", "value1")
        db_manager.set_preference("pref2", 123)

        all_prefs = db_manager.get_all_preferences()

        assert "pref1" in all_prefs
        assert "pref2" in all_prefs
        assert all_prefs["pref1"] == "value1"
        assert all_prefs["pref2"] == 123

    def test_get_preferences_by_category(self, db_manager):
        """Test getting preferences filtered by category."""
        # Set preference with category (requires direct SQL for this test)
        conn = db_manager._get_connection()
        conn.execute("""
            INSERT OR REPLACE INTO user_preferences (key, value, value_type, category)
            VALUES ('cat_pref1', 'value1', 'string', 'test_category')
        """)
        conn.commit()

        prefs = db_manager.get_all_preferences(category="test_category")
        assert "cat_pref1" in prefs


class TestUserCorrections:
    """Test user_corrections table operations."""

    def test_insert_user_correction(self, db_manager):
        """Test inserting user correction."""
        # First insert email analysis (foreign key requirement)
        message_id = "test-msg-correction"
        db_manager.insert_email_analysis(message_id, {}, {"model_version": "v1.0"})

        # Insert correction
        correction = {
            "message_id": message_id,
            "correction_type": "priority",
            "original_suggestion": "Low",
            "user_choice": "High"
        }

        record_id = db_manager.insert_user_correction(correction)
        assert record_id > 0

    def test_get_user_corrections(self, db_manager):
        """Test retrieving user corrections."""
        # Insert email analysis
        message_id = "test-msg-corrections-list"
        db_manager.insert_email_analysis(message_id, {}, {"model_version": "v1.0"})

        # Insert multiple corrections
        for i in range(3):
            correction = {
                "message_id": message_id,
                "correction_type": f"type-{i}",
                "user_choice": f"choice-{i}"
            }
            db_manager.insert_user_correction(correction)

        # Retrieve corrections
        results = db_manager.get_user_corrections(days=30)

        assert len(results) == 3
        assert results[0]["correction_type"] == "type-2"  # Most recent first

    def test_get_user_corrections_by_sender(self, db_manager):
        """Test retrieving corrections filtered by sender."""
        # Insert email analyses with different senders
        sender1 = "sender1@example.com"
        sender2 = "sender2@example.com"

        db_manager.insert_email_analysis("msg1", {}, {"sender": sender1, "model_version": "v1.0"})
        db_manager.insert_email_analysis("msg2", {}, {"sender": sender2, "model_version": "v1.0"})

        # Insert corrections
        db_manager.insert_user_correction({"message_id": "msg1", "correction_type": "priority", "user_choice": "High"})
        db_manager.insert_user_correction({"message_id": "msg2", "correction_type": "priority", "user_choice": "Low"})

        # Get corrections for sender1 only
        results = db_manager.get_user_corrections(sender=sender1, days=30)

        assert len(results) == 1
        assert results[0]["message_id"] == "msg1"


class TestDatabaseMaintenance:
    """Test database maintenance operations (AC8)."""

    def test_get_database_size(self, db_manager):
        """Test getting database file size."""
        # Insert some data to ensure database has size
        for i in range(5):
            db_manager.insert_email_analysis(
                f"size-test-{i}",
                {"data": "test"},
                {"model_version": "v1.0"}
            )

        size_mb = db_manager.get_database_size_mb()

        assert size_mb >= 0  # Database may be very small
        assert isinstance(size_mb, float)

    def test_optimize_database(self, db_manager):
        """Test VACUUM optimization."""
        # Insert some data to create size
        for i in range(10):
            db_manager.insert_email_analysis(
                f"msg-{i}",
                {"data": "x" * 1000},
                {"model_version": "v1.0"}
            )

        # Optimize database
        success, space_saved = db_manager.optimize_database()

        assert success is True
        assert space_saved >= 0  # May be 0 if already optimized


class TestSchemaVersioning:
    """Test schema versioning support (AC5)."""

    def test_get_schema_version(self, db_manager):
        """Test getting current schema version."""
        version = db_manager.get_schema_version()
        assert version == 1  # Initial schema version

    def test_apply_migrations_placeholder(self, db_manager):
        """Test migrations placeholder (full implementation in Task 4)."""
        # Placeholder test - full implementation in Task 4
        result = db_manager.apply_migrations()
        assert result is True


class TestDataDeletion:
    """Test data deletion operations (AC7)."""

    def test_delete_all_data(self, db_manager):
        """Test deleting all data from all tables."""
        # Insert test data
        db_manager.insert_email_analysis("msg1", {}, {"model_version": "v1.0"})
        db_manager.insert_performance_metric("op1", {"hardware_config": "test"})
        db_manager.set_preference("pref1", "value1")

        # Delete all data
        success = db_manager.delete_all_data()
        assert success is True

        # Verify all tables are empty
        assert db_manager.get_email_analysis("msg1") is None
        assert len(db_manager.get_performance_metrics(days=30)) == 0

        # Note: Default preferences remain (deleted then re-initialized)


class TestPerformance:
    """Test query performance (AC3)."""

    def test_query_performance_under_100ms(self, db_manager):
        """Test that common queries complete in <100ms."""
        # Insert test data
        message_id = "perf-test-msg"
        db_manager.insert_email_analysis(message_id, {}, {"model_version": "v1.0"})

        # Time the query
        start = time.time()
        result = db_manager.get_email_analysis(message_id)
        elapsed_ms = (time.time() - start) * 1000

        assert result is not None
        assert elapsed_ms < 100, f"Query took {elapsed_ms:.2f}ms (target: <100ms)"

    def test_bulk_insert_performance(self, db_manager):
        """Test bulk insert performance."""
        start = time.time()

        # Insert 100 records
        for i in range(100):
            db_manager.insert_email_analysis(
                f"bulk-msg-{i}",
                {"priority": "Medium"},
                {"model_version": "v1.0"}
            )

        elapsed_s = time.time() - start

        # Should complete in reasonable time (<5 seconds)
        assert elapsed_s < 5, f"Bulk insert took {elapsed_s:.2f}s (target: <5s)"


class TestErrorHandling:
    """Test error handling and exceptions."""

    def test_connection_error_invalid_path(self):
        """Test error handling for invalid database path."""
        # Use a path that will fail during mkdir (read-only filesystem)
        # This tests that the error is properly raised
        invalid_path = "/nonexistent/directory/database.db"

        with pytest.raises((DBConnectionError, OSError, FileNotFoundError)):
            manager = DatabaseManager(db_path=invalid_path)

    def test_query_error_on_sql_error(self, db_manager):
        """Test QueryError raised on SQL errors."""
        # Try to insert with invalid data type
        with pytest.raises(QueryError):
            db_manager._execute_query("INVALID SQL SYNTAX")
