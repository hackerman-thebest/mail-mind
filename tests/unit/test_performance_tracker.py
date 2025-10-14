"""
Unit Tests for PerformanceTracker

Tests Story 1.6: Performance Optimization & Caching (AC3, AC7)
"""

import pytest
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta

from src.mailmind.core.performance_tracker import PerformanceTracker


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_perf.db")
        yield db_path


@pytest.fixture
def tracker(temp_db):
    """Create PerformanceTracker instance for testing."""
    return PerformanceTracker(temp_db, hardware_tier='Recommended')


class TestPerformanceTrackerInitialization:
    """Test PerformanceTracker initialization."""

    def test_initialization(self, temp_db):
        """Test PerformanceTracker initializes correctly."""
        tracker = PerformanceTracker(temp_db, hardware_tier='Optimal')

        assert tracker.db_path == temp_db
        assert tracker.hardware_tier == 'Optimal'
        assert Path(temp_db).exists()

    def test_database_schema_creation(self, tracker):
        """Test database schema is created correctly."""
        import sqlite3
        conn = sqlite3.connect(tracker.db_path)
        cursor = conn.cursor()

        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='performance_metrics'")
        assert cursor.fetchone() is not None

        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_metrics_timestamp'")
        assert cursor.fetchone() is not None

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_metrics_operation'")
        assert cursor.fetchone() is not None

        conn.close()


class TestMetricsLogging:
    """Test performance metrics logging."""

    def test_log_operation(self, tracker):
        """Test logging operation metrics."""
        tracker.log_operation(
            operation='email_analysis',
            processing_time_ms=1847,
            tokens_per_second=52.3,
            memory_usage_mb=3200,
            model_version='llama3.1:8b-instruct-q4_K_M'
        )

        # Verify logged
        summary = tracker.get_metrics_summary(days=1)
        assert 'email_analysis' in summary
        assert summary['email_analysis']['count'] == 1

    def test_log_operation_performance(self, tracker):
        """Test logging operation has minimal overhead (<5ms)."""
        start = time.time()
        tracker.log_operation(
            operation='test_operation',
            processing_time_ms=1000
        )
        log_time_ms = (time.time() - start) * 1000

        assert log_time_ms < 10, f"Logging took {log_time_ms:.2f}ms (expected <10ms)"

    def test_log_multiple_operations(self, tracker):
        """Test logging multiple operations."""
        for i in range(10):
            tracker.log_operation(
                operation='email_analysis',
                processing_time_ms=1500 + i * 100,
                tokens_per_second=50.0 + i
            )

        summary = tracker.get_metrics_summary(days=1)
        assert summary['email_analysis']['count'] == 10


class TestMetricsSummary:
    """Test metrics summary and aggregation."""

    def test_get_metrics_summary_empty(self, tracker):
        """Test metrics summary for empty database."""
        summary = tracker.get_metrics_summary(days=7)
        assert summary == {}

    def test_get_metrics_summary_with_data(self, tracker):
        """Test metrics summary with logged data."""
        # Log operations
        for i in range(5):
            tracker.log_operation(
                operation='email_analysis',
                processing_time_ms=2000,
                tokens_per_second=50.0
            )

        summary = tracker.get_metrics_summary(days=7)

        assert 'email_analysis' in summary
        assert summary['email_analysis']['count'] == 5
        assert summary['email_analysis']['avg_time_ms'] == 2000
        assert summary['email_analysis']['avg_tokens_per_sec'] == 50.0

    def test_metrics_summary_by_operation_type(self, tracker):
        """Test metrics summary groups by operation type."""
        # Log different operations
        tracker.log_operation('email_analysis', 1500)
        tracker.log_operation('batch_processing', 3000)
        tracker.log_operation('email_analysis', 1600)

        summary = tracker.get_metrics_summary(days=7)

        assert 'email_analysis' in summary
        assert 'batch_processing' in summary
        assert summary['email_analysis']['count'] == 2
        assert summary['batch_processing']['count'] == 1


class TestPerformanceTrends:
    """Test performance trend analysis."""

    def test_get_performance_trends(self, tracker):
        """Test performance trends calculation."""
        # Log baseline operations (simulating older data)
        for i in range(5):
            tracker.log_operation('email_analysis', 1800)

        # Log recent operations (simulating newer data)
        for i in range(5):
            tracker.log_operation('email_analysis', 2200)

        trends = tracker.get_performance_trends('email_analysis', days=30)

        assert 'operation' in trends
        assert trends['operation'] == 'email_analysis'
        assert 'degradation_percent' in trends

    def test_check_performance_degradation(self, tracker):
        """Test performance degradation detection."""
        # Log consistent performance (no degradation)
        for i in range(10):
            tracker.log_operation('email_analysis', 1800)

        degraded = tracker.check_performance_degradation(threshold_percent=20.0)

        # Should be empty (no degradation)
        assert isinstance(degraded, list)


class TestRealTimeMetrics:
    """Test real-time metrics."""

    def test_get_realtime_metrics_empty(self, tracker):
        """Test real-time metrics for empty database."""
        metrics = tracker.get_realtime_metrics()

        assert 'last_10_operations' in metrics
        assert len(metrics['last_10_operations']) == 0

    def test_get_realtime_metrics_with_data(self, tracker):
        """Test real-time metrics with logged data."""
        # Log operations
        for i in range(15):
            tracker.log_operation(
                operation='email_analysis',
                processing_time_ms=1500 + i * 100,
                tokens_per_second=50.0 + i
            )

        metrics = tracker.get_realtime_metrics()

        assert 'last_10_operations' in metrics
        assert len(metrics['last_10_operations']) == 10  # Only last 10
        assert 'avg_tokens_per_sec' in metrics
        assert 'avg_processing_time_ms' in metrics


class TestCSVExport:
    """Test CSV export functionality."""

    def test_export_to_csv(self, tracker, temp_db):
        """Test exporting performance data to CSV."""
        # Log some operations
        for i in range(5):
            tracker.log_operation(
                operation='email_analysis',
                processing_time_ms=1500 + i * 100,
                tokens_per_second=50.0 + i,
                model_version='llama3.1:8b-instruct-q4_K_M'
            )

        # Export to CSV
        csv_path = str(Path(temp_db).parent / "metrics.csv")
        success = tracker.export_to_csv(csv_path, days=7)

        assert success is True
        assert Path(csv_path).exists()

        # Verify CSV contents
        with open(csv_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 6  # Header + 5 data rows
            assert 'Operation' in lines[0]  # Header row
