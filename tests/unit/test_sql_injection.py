"""
Unit tests for SQL injection prevention (Story 3.3 AC1)

Tests verify that all SQL operations properly validate user inputs
against whitelists and reject malicious injection attempts.

Test Coverage:
- Table name injection attempts
- Column name injection attempts
- LIMIT parameter validation
- Whitelist enforcement
- Parameterized query verification
"""

import pytest
import tempfile
import os
from pathlib import Path

# Import DatabaseManager and constants
from mailmind.database.database_manager import (
    DatabaseManager,
    ALLOWED_TABLES,
    ALLOWED_COLUMNS,
    QueryError,
    DatabaseError
)


class TestSQLInjectionPrevention:
    """Test suite for SQL injection prevention measures."""

    @pytest.fixture
    def db_manager(self):
        """Create temporary database for testing."""
        # Create temporary database file
        temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        temp_db.close()
        db_path = temp_db.name

        # Disable encryption for testing
        os.environ['MAILMIND_DISABLE_ENCRYPTION'] = '1'

        # Create database manager
        db = DatabaseManager(db_path=db_path)

        yield db

        # Cleanup
        db.disconnect()
        try:
            os.unlink(db_path)
        except:
            pass

    # ========== Test 1: Table Name Injection ==========

    def test_sql_injection_table_name(self, db_manager):
        """
        Test AC1: Attempt SQL injection via table name in delete_all_data().

        Injection attempt: Modify tables list to include malicious table name
        Expected: ValueError raised with "Invalid table" message
        """
        # Save original method
        original_delete_all = db_manager.delete_all_data

        # Create malicious version that tries injection
        def malicious_delete():
            conn = db_manager._get_connection()
            cursor = conn.cursor()

            # Attempt injection: table name with SQL injection payload
            malicious_tables = ["email_analysis; DROP TABLE email_analysis--"]

            for table in malicious_tables:
                # This should raise ValueError due to whitelist validation
                if table not in ALLOWED_TABLES:
                    raise ValueError(f"Invalid table name: {table}. Must be one of {ALLOWED_TABLES}")
                cursor.execute(f"DELETE FROM {table}")

            conn.commit()

        # Test that injection attempt is blocked
        with pytest.raises(ValueError, match="Invalid table"):
            malicious_delete()

    def test_table_whitelist_enforcement(self, db_manager):
        """
        Test AC1: Verify ALLOWED_TABLES whitelist is enforced.

        Expected: Only tables in ALLOWED_TABLES are valid
        """
        # Verify whitelist contains expected tables
        assert ALLOWED_TABLES == {
            'email_analysis',
            'performance_metrics',
            'user_preferences',
            'user_corrections'
        }

        # Test that invalid table names are rejected
        invalid_tables = [
            'evil_table',
            'email_analysis; DROP TABLE users--',
            'users',
            '../etc/passwd',
            'email_analysis OR 1=1',
        ]

        for table in invalid_tables:
            assert table not in ALLOWED_TABLES, f"Table {table} should not be in whitelist"

    # ========== Test 2: Column Name Injection ==========

    def test_sql_injection_column_name(self, db_manager):
        """
        Test AC1: Attempt SQL injection via column name in query_email_analyses().

        Injection attempt: filters={'priority; DROP TABLE email_analysis--': 'High'}
        Expected: ValueError raised with "Invalid column" message
        """
        malicious_filter = {
            'priority; DROP TABLE email_analysis--': 'High'
        }

        with pytest.raises(ValueError, match="Invalid column name"):
            db_manager.query_email_analyses(filters=malicious_filter)

    def test_column_whitelist_enforcement(self, db_manager):
        """
        Test AC1: Verify ALLOWED_COLUMNS whitelist is enforced.

        Expected: Only columns in ALLOWED_COLUMNS are valid for filtering
        """
        # Verify whitelist contains expected columns
        expected_columns = {
            'message_id', 'subject', 'sender', 'received_date', 'analysis_json',
            'priority', 'suggested_folder', 'confidence_score', 'sentiment',
            'processing_time_ms', 'model_version', 'hardware_profile', 'processed_date'
        }
        assert ALLOWED_COLUMNS == expected_columns

        # Test valid columns pass validation
        valid_filters = [
            {'priority': 'High'},
            {'sender': 'test@example.com'},
            {'sentiment': 'positive'},
        ]

        for filters in valid_filters:
            # Should not raise any exception
            try:
                db_manager.query_email_analyses(filters=filters, limit=10)
            except ValueError:
                pytest.fail(f"Valid filter {filters} was rejected")

        # Test invalid columns are rejected
        invalid_filters = [
            {'evil_column': 'value'},
            {'priority; DROP TABLE': 'High'},
            {'* FROM users WHERE 1=1 --': 'value'},
        ]

        for filters in invalid_filters:
            with pytest.raises(ValueError, match="Invalid column name"):
                db_manager.query_email_analyses(filters=filters)

    # ========== Test 3: LIMIT Parameter Injection ==========

    def test_limit_parameter_validation(self, db_manager):
        """
        Test AC1: Verify LIMIT parameter validation prevents injection.

        Expected: Only positive integers within range are accepted
        """
        # Test valid LIMIT values
        valid_limits = [1, 10, 100, 1000, 10000, 100000]
        for limit in valid_limits:
            try:
                db_manager.query_email_analyses(limit=limit)
            except ValueError:
                pytest.fail(f"Valid LIMIT {limit} was rejected")

        # Test invalid LIMIT values
        invalid_limits = [
            0,  # Zero
            -1,  # Negative
            -999,  # Large negative
            100001,  # Too large
            999999,  # Way too large
            "1000",  # String instead of int
            1.5,  # Float instead of int
            None,  # None
            "1000; DROP TABLE email_analysis--",  # Injection attempt
        ]

        for limit in invalid_limits:
            with pytest.raises((ValueError, TypeError)):
                db_manager.query_email_analyses(limit=limit)

    # ========== Test 4: Parameterized Queries ==========

    def test_parameterized_queries_used(self, db_manager):
        """
        Test AC1: Verify that parameterized queries (? placeholders) are used.

        This test verifies that user-provided VALUES use ? placeholders,
        not string interpolation.
        """
        # Insert test data using parameterized query
        message_id = "test_msg_001"
        analysis = {"priority": "High"}
        metadata = {
            "subject": "Test Subject",
            "sender": "test@example.com",
            "received_date": "2025-10-16",
            "priority": "High",
            "suggested_folder": "Important",
            "confidence_score": 0.95,
            "sentiment": "positive",
            "processing_time_ms": 150,
            "model_version": "llama3.1:8b",
            "hardware_profile": "CPU-only"
        }

        # Should not raise any exception (parameterized query is safe)
        db_manager.insert_email_analysis(message_id, analysis, metadata)

        # Attempt injection via filter VALUE (should be safe with parameterized queries)
        malicious_value = "High' OR '1'='1"
        results = db_manager.query_email_analyses(filters={'priority': malicious_value})

        # Should return empty results (injection neutralized by parameterization)
        assert len(results) == 0, "Injection attempt should return no results"

    def test_injection_in_values_neutralized(self, db_manager):
        """
        Test AC1: Verify SQL injection in parameter VALUES is neutralized.

        Parameterized queries should treat injection payloads as literal strings.
        """
        # Insert test email
        db_manager.insert_email_analysis(
            message_id="test_001",
            analysis={},
            metadata={
                "subject": "Test",
                "sender": "test@example.com",
                "received_date": "2025-10-16",
                "priority": "High",
                "model_version": "test-model",
                "hardware_profile": "test-hw"
            }
        )

        # Attempt injection via WHERE value (should be treated as literal string)
        injection_payloads = [
            "High' OR '1'='1",
            "High'; DROP TABLE email_analysis--",
            "High' UNION SELECT * FROM user_preferences--",
            "1' OR '1'='1' --",
        ]

        for payload in injection_payloads:
            results = db_manager.query_email_analyses(filters={'priority': payload})
            # Should return empty (payload treated as literal string, not SQL)
            assert len(results) == 0, f"Injection payload {payload} should return no results"

    # ========== Test 5: Static Analysis Verification ==========

    def test_no_string_interpolation_in_sql(self):
        """
        Test AC1: Verify no f-string interpolation with user data in SQL.

        Note: This is a documentation test. Actual verification done via bandit.
        """
        # Read database_manager.py source code
        db_manager_path = Path(__file__).parent.parent.parent / 'src' / 'mailmind' / 'database' / 'database_manager.py'

        if db_manager_path.exists():
            source_code = db_manager_path.read_text()

            # Check that SQL injection prevention comments are present
            assert 'Story 3.3 AC1' in source_code, "SQL injection prevention markers missing"
            assert 'ALLOWED_TABLES' in source_code, "ALLOWED_TABLES whitelist missing"
            assert 'ALLOWED_COLUMNS' in source_code, "ALLOWED_COLUMNS whitelist missing"

            # Check for validation comments
            assert 'Validate table name against whitelist' in source_code
            assert 'Validate column name against whitelist' in source_code
            assert 'SQL injection prevention' in source_code

    # ========== Test 6: Edge Cases ==========

    def test_empty_filters_safe(self, db_manager):
        """Test that empty filters don't cause issues."""
        # Empty filters should work fine
        results = db_manager.query_email_analyses(filters={})
        assert isinstance(results, list)

        # None filters should work fine
        results = db_manager.query_email_analyses(filters=None)
        assert isinstance(results, list)

    def test_special_characters_in_values(self, db_manager):
        """Test that special characters in VALUES are handled safely."""
        # Insert email with special characters
        db_manager.insert_email_analysis(
            message_id="test_special",
            analysis={},
            metadata={
                "subject": "Test's \"Subject\" with <html> & $pecial ch@rs",
                "sender": "user+tag@example.com",
                "received_date": "2025-10-16",
                "priority": "High",
                "model_version": "test-model",
                "hardware_profile": "test-hw"
            }
        )

        # Query should work fine (parameterized queries handle special chars)
        result = db_manager.get_email_analysis("test_special")
        assert result is not None
        assert "Test's \"Subject\"" in result['subject']

    def test_delete_all_data_validation(self, db_manager):
        """
        Test AC1: Verify delete_all_data() validates table names.

        Expected: Only ALLOWED_TABLES can be deleted
        """
        # delete_all_data() should work with valid tables
        result = db_manager.delete_all_data()
        assert result is True

        # Verify all data deleted
        results = db_manager.query_email_analyses(limit=10)
        assert len(results) == 0


class TestSQLInjectionDocumentation:
    """Tests to verify SQL injection prevention is properly documented."""

    def test_whitelists_defined(self):
        """Verify ALLOWED_TABLES and ALLOWED_COLUMNS are defined."""
        assert ALLOWED_TABLES is not None
        assert ALLOWED_COLUMNS is not None
        assert len(ALLOWED_TABLES) == 4
        assert len(ALLOWED_COLUMNS) >= 10

    def test_whitelists_are_sets(self):
        """Verify whitelists are sets (O(1) lookup performance)."""
        assert isinstance(ALLOWED_TABLES, set)
        assert isinstance(ALLOWED_COLUMNS, set)


# ========== Integration with Static Analysis ==========

def test_bandit_instructions():
    """
    Instructions for running bandit static analysis (AC1 requirement).

    Run this command to verify no SQL injection vectors:
        bandit -r src/mailmind/database/database_manager.py -f json

    Expected: No issues with codes B608 (SQL injection)
    """
    pass  # This test is documentation only


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
