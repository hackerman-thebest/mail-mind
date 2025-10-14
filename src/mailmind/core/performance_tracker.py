"""
Performance Tracker for MailMind

This module provides real-time performance monitoring and trend analysis.
Implements Story 1.6: Performance Optimization & Caching (AC3, AC7)

Key Features:
- Real-time performance metrics tracking (tokens/sec, processing time, memory)
- Performance metrics logging to database
- 7-day and 30-day performance averages
- Performance degradation detection (>20% from baseline)
- CSV export for external analysis
- Queue depth tracking for batch processing

Integration:
- Used by EmailAnalysisEngine and other components
- Uses existing performance_metrics table
- Standalone class that can be used independently

Performance Targets:
- Metrics logging overhead: <5ms per operation
- Metrics summary calculation: <100ms for 30 days
"""

import logging
import sqlite3
import csv
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path


logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Tracks and analyzes performance metrics for MailMind operations.

    Provides real-time monitoring, trend analysis, and performance
    degradation detection.

    Example:
        tracker = PerformanceTracker('data/mailmind.db')

        # Log operation performance
        tracker.log_operation(
            operation='email_analysis',
            processing_time_ms=1847,
            tokens_per_second=52.3,
            memory_usage_mb=3200
        )

        # Get performance summary
        summary = tracker.get_metrics_summary(days=7)
        print(f"Avg tokens/sec: {summary['email_analysis']['avg_tokens_per_sec']}")

        # Check for performance degradation
        is_degraded = tracker.check_performance_degradation()
    """

    def __init__(self, db_path: str, hardware_tier: str = 'Unknown'):
        """
        Initialize PerformanceTracker with SQLite database.

        Args:
            db_path: Path to SQLite database file
            hardware_tier: Hardware tier for context (Optimal/Recommended/Minimum)
        """
        self.db_path = db_path
        self.hardware_tier = hardware_tier

        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database (reuses existing performance_metrics table)
        self._init_database()

        logger.info(f"PerformanceTracker initialized with database: {db_path}")

    def _init_database(self):
        """Ensure performance_metrics table exists (may already exist from EmailAnalysisEngine)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create performance_metrics table (if not exists)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                hardware_config TEXT,
                model_version TEXT,
                tokens_per_second REAL,
                memory_usage_mb INTEGER,
                processing_time_ms INTEGER,
                batch_size INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Index for fast time-range queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
            ON performance_metrics(timestamp)
        ''')

        # Index for operation-based queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_metrics_operation
            ON performance_metrics(operation)
        ''')

        conn.commit()
        conn.close()

        logger.debug("Performance metrics database schema initialized")

    def log_operation(self, operation: str, processing_time_ms: int,
                     tokens_per_second: Optional[float] = None,
                     memory_usage_mb: Optional[int] = None,
                     model_version: Optional[str] = None,
                     batch_size: int = 1):
        """
        Log performance metrics for an operation.

        Args:
            operation: Operation name (e.g., 'email_analysis', 'batch_processing')
            processing_time_ms: Processing time in milliseconds
            tokens_per_second: Tokens per second (for LLM operations)
            memory_usage_mb: Memory usage in MB
            model_version: LLM model version
            batch_size: Number of items processed (for batch operations)
        """
        start_time = time.time()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO performance_metrics (
                    operation,
                    hardware_config,
                    model_version,
                    tokens_per_second,
                    memory_usage_mb,
                    processing_time_ms,
                    batch_size,
                    timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                operation,
                self.hardware_tier,
                model_version,
                tokens_per_second,
                memory_usage_mb,
                processing_time_ms,
                batch_size
            ))

            conn.commit()
            conn.close()

            log_time_ms = int((time.time() - start_time) * 1000)
            logger.debug(f"Performance logged: {operation}, {processing_time_ms}ms (log overhead: {log_time_ms}ms)")

        except Exception as e:
            logger.error(f"Failed to log performance: {e}")

    def get_metrics_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get performance metrics summary for last N days.

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            Metrics summary dictionary grouped by operation:
            {
                "email_analysis": {
                    "count": 150,
                    "avg_time_ms": 1847.5,
                    "avg_tokens_per_sec": 52.3,
                    "avg_memory_mb": 3200.0,
                    "min_time_ms": 850,
                    "max_time_ms": 4200
                },
                ...
            }
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Calculate date threshold
            date_threshold = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute('''
                SELECT
                    operation,
                    COUNT(*) as count,
                    AVG(processing_time_ms) as avg_time_ms,
                    AVG(tokens_per_second) as avg_tokens_per_sec,
                    AVG(memory_usage_mb) as avg_memory_mb,
                    MIN(processing_time_ms) as min_time_ms,
                    MAX(processing_time_ms) as max_time_ms
                FROM performance_metrics
                WHERE timestamp > ?
                GROUP BY operation
            ''', (date_threshold,))

            rows = cursor.fetchall()
            conn.close()

            metrics = {}
            for row in rows:
                metrics[row[0]] = {
                    'count': row[1],
                    'avg_time_ms': round(row[2], 2) if row[2] else 0,
                    'avg_tokens_per_sec': round(row[3], 2) if row[3] else None,
                    'avg_memory_mb': round(row[4], 2) if row[4] else None,
                    'min_time_ms': row[5] or 0,
                    'max_time_ms': row[6] or 0
                }

            logger.debug(f"Retrieved metrics summary for last {days} days: {len(metrics)} operations")

            return metrics

        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {}

    def get_performance_trends(self, operation: str, days: int = 30) -> Dict[str, Any]:
        """
        Get performance trends for a specific operation over time.

        Args:
            operation: Operation name to analyze
            days: Number of days to analyze (default: 30)

        Returns:
            Trends dictionary:
            {
                "operation": "email_analysis",
                "period_days": 30,
                "baseline_avg_time_ms": 1800.0,
                "current_avg_time_ms": 2200.0,
                "degradation_percent": 22.2,
                "is_degraded": True
            }
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get baseline (oldest 25% of data in period)
            date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
            baseline_end = (datetime.now() - timedelta(days=int(days * 0.75))).isoformat()

            cursor.execute('''
                SELECT AVG(processing_time_ms), AVG(tokens_per_second)
                FROM performance_metrics
                WHERE operation = ? AND timestamp > ? AND timestamp < ?
            ''', (operation, date_threshold, baseline_end))

            baseline_row = cursor.fetchone()
            baseline_avg_time = baseline_row[0] or 0
            baseline_avg_tokens = baseline_row[1] or 0

            # Get current (newest 25% of data in period)
            current_start = (datetime.now() - timedelta(days=int(days * 0.25))).isoformat()

            cursor.execute('''
                SELECT AVG(processing_time_ms), AVG(tokens_per_second)
                FROM performance_metrics
                WHERE operation = ? AND timestamp > ?
            ''', (operation, current_start))

            current_row = cursor.fetchone()
            current_avg_time = current_row[0] or 0
            current_avg_tokens = current_row[1] or 0

            conn.close()

            # Calculate degradation
            degradation_percent = 0.0
            is_degraded = False

            if baseline_avg_time > 0:
                degradation_percent = ((current_avg_time - baseline_avg_time) / baseline_avg_time) * 100
                is_degraded = degradation_percent > 20.0  # >20% degradation threshold

            return {
                'operation': operation,
                'period_days': days,
                'baseline_avg_time_ms': round(baseline_avg_time, 2),
                'baseline_avg_tokens_per_sec': round(baseline_avg_tokens, 2) if baseline_avg_tokens else None,
                'current_avg_time_ms': round(current_avg_time, 2),
                'current_avg_tokens_per_sec': round(current_avg_tokens, 2) if current_avg_tokens else None,
                'degradation_percent': round(degradation_percent, 2),
                'is_degraded': is_degraded
            }

        except Exception as e:
            logger.error(f"Failed to get performance trends: {e}")
            return {
                'operation': operation,
                'error': str(e)
            }

    def check_performance_degradation(self, threshold_percent: float = 20.0,
                                     days: int = 30) -> List[Dict[str, Any]]:
        """
        Check for performance degradation across all operations.

        Args:
            threshold_percent: Degradation threshold (default: 20%)
            days: Number of days to analyze (default: 30)

        Returns:
            List of degraded operations:
            [
                {
                    "operation": "email_analysis",
                    "degradation_percent": 25.5,
                    "baseline_avg_time_ms": 1800.0,
                    "current_avg_time_ms": 2259.0
                }
            ]
        """
        try:
            # Get list of operations
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT DISTINCT operation FROM performance_metrics')
            operations = [row[0] for row in cursor.fetchall()]

            conn.close()

            # Check each operation for degradation
            degraded = []
            for operation in operations:
                trends = self.get_performance_trends(operation, days=days)
                if trends.get('is_degraded', False):
                    degraded.append({
                        'operation': operation,
                        'degradation_percent': trends['degradation_percent'],
                        'baseline_avg_time_ms': trends['baseline_avg_time_ms'],
                        'current_avg_time_ms': trends['current_avg_time_ms']
                    })

            if degraded:
                logger.warning(f"Performance degradation detected for {len(degraded)} operation(s)")

            return degraded

        except Exception as e:
            logger.error(f"Failed to check performance degradation: {e}")
            return []

    def export_to_csv(self, output_path: str, days: int = 30) -> bool:
        """
        Export performance data to CSV for external analysis.

        Args:
            output_path: Path to output CSV file
            days: Number of days to export (default: 30)

        Returns:
            True if export successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get data for last N days
            date_threshold = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute('''
                SELECT
                    operation,
                    hardware_config,
                    model_version,
                    tokens_per_second,
                    memory_usage_mb,
                    processing_time_ms,
                    batch_size,
                    timestamp
                FROM performance_metrics
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            ''', (date_threshold,))

            rows = cursor.fetchall()
            conn.close()

            # Write to CSV
            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Header
                writer.writerow([
                    'Operation', 'Hardware Config', 'Model Version',
                    'Tokens/Sec', 'Memory (MB)', 'Processing Time (ms)',
                    'Batch Size', 'Timestamp'
                ])

                # Data rows
                writer.writerows(rows)

            logger.info(f"Exported {len(rows)} metrics to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export metrics to CSV: {e}")
            return False

    def get_realtime_metrics(self) -> Dict[str, Any]:
        """
        Get real-time metrics for last 10 operations.

        Returns:
            Real-time metrics dictionary:
            {
                "last_10_operations": [
                    {
                        "operation": "email_analysis",
                        "processing_time_ms": 1847,
                        "tokens_per_second": 52.3,
                        "timestamp": "2025-10-13T14:30:00"
                    },
                    ...
                ],
                "avg_tokens_per_sec": 50.5,
                "avg_processing_time_ms": 1920.3
            }
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT
                    operation,
                    processing_time_ms,
                    tokens_per_second,
                    memory_usage_mb,
                    timestamp
                FROM performance_metrics
                ORDER BY timestamp DESC
                LIMIT 10
            ''')

            rows = cursor.fetchall()
            conn.close()

            operations = []
            total_tokens_per_sec = 0.0
            total_processing_time = 0
            token_count = 0

            for row in rows:
                operations.append({
                    'operation': row[0],
                    'processing_time_ms': row[1],
                    'tokens_per_second': row[2],
                    'memory_usage_mb': row[3],
                    'timestamp': row[4]
                })

                if row[2]:  # tokens_per_second
                    total_tokens_per_sec += row[2]
                    token_count += 1

                if row[1]:  # processing_time_ms
                    total_processing_time += row[1]

            avg_tokens_per_sec = total_tokens_per_sec / token_count if token_count > 0 else 0
            avg_processing_time = total_processing_time / len(operations) if operations else 0

            return {
                'last_10_operations': operations,
                'avg_tokens_per_sec': round(avg_tokens_per_sec, 2),
                'avg_processing_time_ms': round(avg_processing_time, 2)
            }

        except Exception as e:
            logger.error(f"Failed to get realtime metrics: {e}")
            return {
                'last_10_operations': [],
                'error': str(e)
            }
