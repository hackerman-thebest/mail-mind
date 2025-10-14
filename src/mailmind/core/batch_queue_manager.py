"""
Batch Queue Manager for MailMind

This module provides batch processing queue management with memory monitoring.
Implements Story 1.6: Performance Optimization & Caching (AC4, AC5, AC6)

Key Features:
- Sequential batch processing queue with pause/resume
- Priority queue support (high priority emails processed first)
- Memory monitoring every 5 seconds during operations
- Automatic batch size reduction under memory pressure
- Graceful degradation when resources are constrained
- Queue persistence across application restarts
- Progress tracking and callbacks

Integration:
- Used by EmailAnalysisEngine for batch operations
- Integrates with HardwareProfiler for resource monitoring
- Standalone class that can be used independently

Performance Targets:
- Throughput: 10-15 emails/minute on recommended hardware
- Memory limit: <8GB RAM with model loaded
- Automatic GC trigger at 85% memory usage
"""

import gc
import json
import logging
import sqlite3
import threading
import time
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

from src.mailmind.core.hardware_profiler import HardwareProfiler


logger = logging.getLogger(__name__)


class QueueItemStatus(Enum):
    """Status of queue items."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueuePriority(Enum):
    """Priority levels for queue items."""
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class QueueItem:
    """Represents an item in the batch processing queue."""
    id: str
    data: Any
    priority: QueuePriority
    status: QueueItemStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class BatchQueueManager:
    """
    Manages batch processing queue with memory monitoring and graceful degradation.

    Provides sequential processing, pause/resume, priority queuing, and
    automatic resource management under memory pressure.

    Example:
        manager = BatchQueueManager(
            db_path='data/mailmind.db',
            memory_limit_gb=8.0,
            target_throughput=15
        )

        # Add items to queue
        for email in emails:
            manager.add_to_queue(email_id, email, priority=QueuePriority.HIGH)

        # Process queue with callback
        def progress_callback(current, total, result):
            print(f"Progress: {current}/{total}")

        results = manager.process_queue(
            processor_func=analyze_email,
            callback=progress_callback
        )
    """

    def __init__(self, db_path: str, memory_limit_gb: float = 8.0,
                 target_throughput: int = 15):
        """
        Initialize Batch Queue Manager.

        Args:
            db_path: Path to SQLite database for queue persistence
            memory_limit_gb: Hard memory limit in GB (default: 8.0)
            target_throughput: Target emails per minute (default: 15)
        """
        self.db_path = db_path
        self.memory_limit_gb = memory_limit_gb
        self.memory_limit_bytes = int(memory_limit_gb * 1024**3)
        self.target_throughput = target_throughput

        # Queue state
        self.queue: List[QueueItem] = []
        self.is_paused = False
        self.is_processing = False
        self.current_batch_size = self._calculate_initial_batch_size()

        # Memory monitoring
        self.memory_check_interval = 5.0  # seconds
        self.memory_monitor_thread: Optional[threading.Thread] = None
        self.stop_monitoring = threading.Event()

        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        # Load persisted queue
        self._load_queue()

        logger.info(f"BatchQueueManager initialized: memory_limit={memory_limit_gb}GB, "
                   f"target_throughput={target_throughput}/min, "
                   f"initial_batch_size={self.current_batch_size}")

    def _init_database(self):
        """Initialize queue persistence table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS batch_queue (
                id TEXT PRIMARY KEY,
                data_json TEXT NOT NULL,
                priority INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                started_at DATETIME,
                completed_at DATETIME,
                result_json TEXT,
                error TEXT
            )
        ''')

        # Index for priority-based sorting
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_queue_priority_status
            ON batch_queue(priority, status, created_at)
        ''')

        conn.commit()
        conn.close()

        logger.debug("Batch queue database schema initialized")

    def _load_queue(self):
        """Load persisted queue from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Load pending and processing items
            cursor.execute('''
                SELECT id, data_json, priority, status, created_at,
                       started_at, completed_at, result_json, error
                FROM batch_queue
                WHERE status IN ('pending', 'processing')
                ORDER BY priority ASC, created_at ASC
            ''')

            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                item = QueueItem(
                    id=row[0],
                    data=json.loads(row[1]),
                    priority=QueuePriority(row[2]),
                    status=QueueItemStatus(row[3]),
                    created_at=datetime.fromisoformat(row[4]),
                    started_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    completed_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    result=json.loads(row[7]) if row[7] else None,
                    error=row[8]
                )
                self.queue.append(item)

            if self.queue:
                logger.info(f"Loaded {len(self.queue)} items from persisted queue")

        except Exception as e:
            logger.error(f"Failed to load persisted queue: {e}")

    def _calculate_initial_batch_size(self) -> int:
        """Calculate initial batch size based on hardware."""
        try:
            hardware = HardwareProfiler.detect_hardware()
            tier = hardware['hardware_tier']

            # Batch sizes by tier
            batch_sizes = {
                'Optimal': 15,
                'Recommended': 10,
                'Minimum': 5,
                'Insufficient': 1
            }

            return batch_sizes.get(tier, 5)

        except Exception as e:
            logger.warning(f"Failed to detect hardware for batch size: {e}")
            return 5  # Safe default

    def add_to_queue(self, item_id: str, data: Any,
                    priority: QueuePriority = QueuePriority.MEDIUM):
        """
        Add item to batch processing queue.

        Args:
            item_id: Unique identifier for queue item
            data: Data to process (will be JSON serialized)
            priority: Queue priority (HIGH/MEDIUM/LOW)
        """
        item = QueueItem(
            id=item_id,
            data=data,
            priority=priority,
            status=QueueItemStatus.PENDING,
            created_at=datetime.now()
        )

        self.queue.append(item)
        self._persist_queue_item(item)

        logger.debug(f"Added item {item_id} to queue with priority {priority.name}")

    def _persist_queue_item(self, item: QueueItem):
        """Persist queue item to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO batch_queue
                (id, data_json, priority, status, created_at,
                 started_at, completed_at, result_json, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.id,
                json.dumps(item.data),
                item.priority.value,
                item.status.value,
                item.created_at.isoformat(),
                item.started_at.isoformat() if item.started_at else None,
                item.completed_at.isoformat() if item.completed_at else None,
                json.dumps(item.result) if item.result else None,
                item.error
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to persist queue item {item.id}: {e}")

    def process_queue(self, processor_func: Callable[[Any], Any],
                     callback: Optional[Callable[[int, int, Any], None]] = None) -> List[Any]:
        """
        Process all items in queue.

        Args:
            processor_func: Function to process each item (item.data) → result
            callback: Optional progress callback(current, total, result)

        Returns:
            List of processing results
        """
        if self.is_processing:
            logger.warning("Queue is already being processed")
            return []

        self.is_processing = True
        self._start_memory_monitoring()

        try:
            # Sort queue by priority
            self.queue.sort(key=lambda x: (x.priority.value, x.created_at))

            total = len([item for item in self.queue if item.status == QueueItemStatus.PENDING])
            current = 0
            results = []

            logger.info(f"Starting queue processing: {total} items")

            for item in self.queue:
                # Skip non-pending items
                if item.status != QueueItemStatus.PENDING:
                    continue

                # Check if paused
                while self.is_paused:
                    logger.debug("Queue processing paused")
                    time.sleep(1)

                # Check memory pressure before processing
                if self._check_and_handle_memory_pressure():
                    logger.warning("Memory pressure detected, reducing batch size")

                # Process item
                current += 1
                item.status = QueueItemStatus.PROCESSING
                item.started_at = datetime.now()
                self._persist_queue_item(item)

                try:
                    logger.debug(f"Processing queue item {current}/{total}: {item.id}")
                    result = processor_func(item.data)

                    item.status = QueueItemStatus.COMPLETED
                    item.completed_at = datetime.now()
                    item.result = result
                    results.append(result)

                    # Call progress callback
                    if callback:
                        callback(current, total, result)

                except Exception as e:
                    logger.error(f"Failed to process queue item {item.id}: {e}")
                    item.status = QueueItemStatus.FAILED
                    item.completed_at = datetime.now()
                    item.error = str(e)
                    results.append(None)

                finally:
                    self._persist_queue_item(item)

            # Calculate throughput
            processing_time = sum([
                (item.completed_at - item.started_at).total_seconds()
                for item in self.queue
                if item.completed_at and item.started_at
            ])

            if processing_time > 0:
                throughput = (current / processing_time) * 60
                logger.info(f"Queue processing complete: {current} items, "
                           f"throughput={throughput:.1f} items/min")

            return results

        finally:
            self.is_processing = False
            self._stop_memory_monitoring()

    def _start_memory_monitoring(self):
        """Start background memory monitoring thread."""
        self.stop_monitoring.clear()
        self.memory_monitor_thread = threading.Thread(
            target=self._monitor_memory_loop,
            daemon=True
        )
        self.memory_monitor_thread.start()
        logger.debug("Memory monitoring started")

    def _stop_memory_monitoring(self):
        """Stop background memory monitoring thread."""
        self.stop_monitoring.set()
        if self.memory_monitor_thread:
            self.memory_monitor_thread.join(timeout=2)
        logger.debug("Memory monitoring stopped")

    def _monitor_memory_loop(self):
        """Background thread to monitor memory usage."""
        while not self.stop_monitoring.is_set():
            try:
                resources = HardwareProfiler.monitor_resources()
                ram_percent = resources['ram_percent']
                ram_used_gb = resources['ram_used_gb']

                # Check memory thresholds
                if ram_used_gb > self.memory_limit_gb * 0.90:
                    logger.warning(f"Memory usage critical: {ram_used_gb:.2f}GB "
                                 f"({ram_percent:.1f}%) exceeds 90% of {self.memory_limit_gb}GB limit")

                elif ram_used_gb > self.memory_limit_gb * 0.85:
                    logger.info(f"Memory usage high: {ram_used_gb:.2f}GB "
                              f"({ram_percent:.1f}%), triggering garbage collection")
                    gc.collect()

            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")

            # Sleep for interval
            self.stop_monitoring.wait(self.memory_check_interval)

    def _check_and_handle_memory_pressure(self) -> bool:
        """
        Check for memory pressure and take action.

        Returns:
            True if memory pressure detected, False otherwise
        """
        try:
            resources = HardwareProfiler.monitor_resources()
            ram_used_gb = resources['ram_used_gb']
            ram_percent = resources['ram_percent']

            # Memory pressure threshold: 85% of limit
            if ram_used_gb > self.memory_limit_gb * 0.85:
                logger.warning(f"Memory pressure detected: {ram_used_gb:.2f}GB / {self.memory_limit_gb}GB")

                # Trigger garbage collection
                gc.collect()

                # Reduce batch size
                new_batch_size = max(1, self.current_batch_size // 2)
                if new_batch_size != self.current_batch_size:
                    logger.info(f"Reducing batch size: {self.current_batch_size} → {new_batch_size}")
                    self.current_batch_size = new_batch_size

                return True

            return False

        except Exception as e:
            logger.error(f"Failed to check memory pressure: {e}")
            return False

    def pause(self):
        """Pause queue processing."""
        self.is_paused = True
        logger.info("Queue processing paused")

    def resume(self):
        """Resume queue processing."""
        self.is_paused = False
        logger.info("Queue processing resumed")

    def cancel_item(self, item_id: str) -> bool:
        """
        Cancel a specific queue item.

        Args:
            item_id: ID of item to cancel

        Returns:
            True if item was cancelled, False if not found or already completed
        """
        for item in self.queue:
            if item.id == item_id:
                if item.status in [QueueItemStatus.PENDING, QueueItemStatus.PROCESSING]:
                    item.status = QueueItemStatus.CANCELLED
                    item.completed_at = datetime.now()
                    self._persist_queue_item(item)
                    logger.info(f"Cancelled queue item: {item_id}")
                    return True
                else:
                    logger.warning(f"Cannot cancel item {item_id}: status={item.status.value}")
                    return False

        logger.warning(f"Item not found in queue: {item_id}")
        return False

    def cancel_all(self):
        """Cancel all pending queue items."""
        cancelled_count = 0
        for item in self.queue:
            if item.status == QueueItemStatus.PENDING:
                item.status = QueueItemStatus.CANCELLED
                item.completed_at = datetime.now()
                self._persist_queue_item(item)
                cancelled_count += 1

        logger.info(f"Cancelled {cancelled_count} pending queue items")

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status.

        Returns:
            Status dictionary:
            {
                "total_items": 50,
                "pending": 30,
                "processing": 1,
                "completed": 15,
                "failed": 2,
                "cancelled": 2,
                "is_paused": False,
                "current_batch_size": 10
            }
        """
        status_counts = {
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0,
            'cancelled': 0
        }

        for item in self.queue:
            status_counts[item.status.value] += 1

        return {
            'total_items': len(self.queue),
            'pending': status_counts['pending'],
            'processing': status_counts['processing'],
            'completed': status_counts['completed'],
            'failed': status_counts['failed'],
            'cancelled': status_counts['cancelled'],
            'is_paused': self.is_paused,
            'is_processing': self.is_processing,
            'current_batch_size': self.current_batch_size
        }

    def clear_completed(self):
        """Remove completed, failed, and cancelled items from queue."""
        initial_count = len(self.queue)

        self.queue = [
            item for item in self.queue
            if item.status not in [QueueItemStatus.COMPLETED, QueueItemStatus.FAILED, QueueItemStatus.CANCELLED]
        ]

        removed_count = initial_count - len(self.queue)
        logger.info(f"Cleared {removed_count} completed/failed/cancelled items from queue")
