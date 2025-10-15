"""
Memory pressure monitoring and graceful degradation.

Monitors system memory and triggers optimization strategies when memory is low.

Story 2.6 AC12: Error Scenario - Insufficient memory
Story 2.6 Subtask 1.6: Add graceful degradation for memory pressure
"""

import logging
import gc
import threading
import time
from typing import Optional, Callable, Dict, Any

try:
    from mailmind.core.hardware_profiler import HardwareProfiler
    from mailmind.core.exceptions import InsufficientMemoryError
except ImportError:
    # Fallback if modules not available yet
    HardwareProfiler = None
    InsufficientMemoryError = None


logger = logging.getLogger(__name__)


class MemoryMonitor:
    """
    Monitors memory usage and triggers graceful degradation.

    Story 2.6 Constraint arch-7: Background thread calling HardwareProfiler.monitor_resources()
    every 5 seconds. If check_memory_pressure(85.0) returns True: (1) log WARNING, (2) trigger
    garbage collection, (3) reduce batch size, (4) show toast notification if >90%.
    """

    def __init__(
        self,
        check_interval: float = 5.0,
        warning_threshold: float = 85.0,
        critical_threshold: float = 90.0
    ):
        """
        Initialize MemoryMonitor.

        Args:
            check_interval: Interval between checks in seconds (default: 5.0)
            warning_threshold: Memory usage % to trigger warning (default: 85%)
            critical_threshold: Memory usage % to trigger critical alert (default: 90%)
        """
        self.check_interval = check_interval
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._callbacks: Dict[str, Callable] = {}
        self._last_warning_time = 0
        self._warning_cooldown = 60.0  # Don't spam warnings (1 minute cooldown)

        logger.info(
            f"MemoryMonitor initialized (check_interval={check_interval}s, "
            f"warning={warning_threshold}%, critical={critical_threshold}%)"
        )

    def register_callback(self, event: str, callback: Callable):
        """
        Register callback for memory events.

        Args:
            event: Event type ("warning", "critical", "normal")
            callback: Callback function(memory_info: Dict) -> None
        """
        self._callbacks[event] = callback
        logger.debug(f"Registered callback for '{event}' event")

    def start(self):
        """Start memory monitoring background thread."""
        if self._running:
            logger.warning("MemoryMonitor already running")
            return

        if HardwareProfiler is None:
            logger.error("HardwareProfiler not available, cannot start MemoryMonitor")
            return

        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="MemoryMonitor"
        )
        self._monitor_thread.start()
        logger.info("✅ MemoryMonitor started")

    def stop(self):
        """Stop memory monitoring background thread."""
        if not self._running:
            return

        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        logger.info("MemoryMonitor stopped")

    def _monitor_loop(self):
        """Background monitoring loop."""
        logger.info("Memory monitoring loop started")

        while self._running:
            try:
                # Monitor resources
                memory_info = HardwareProfiler.monitor_resources()
                ram_percent = memory_info.get('ram_percent', 0)
                ram_available_gb = memory_info.get('ram_available_gb', 0)

                # Check memory pressure
                is_pressure = HardwareProfiler.check_memory_pressure(self.warning_threshold)

                current_time = time.time()

                # AC12: Insufficient memory scenario
                if ram_available_gb < 2.0:
                    # Critical: Less than 2GB available
                    self._handle_critical_memory(memory_info)
                elif is_pressure and ram_percent >= self.critical_threshold:
                    # Critical: Above 90%
                    self._handle_critical_memory(memory_info)
                elif is_pressure and ram_percent >= self.warning_threshold:
                    # Warning: Above 85%
                    # Only trigger if cooldown period has passed
                    if current_time - self._last_warning_time > self._warning_cooldown:
                        self._handle_warning_memory(memory_info)
                        self._last_warning_time = current_time
                else:
                    # Normal: Below warning threshold
                    self._handle_normal_memory(memory_info)

                # Sleep until next check
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in memory monitoring loop: {e}", exc_info=True)
                time.sleep(self.check_interval)

        logger.info("Memory monitoring loop stopped")

    def _handle_warning_memory(self, memory_info: Dict[str, Any]):
        """
        Handle warning-level memory pressure.

        Constraint arch-7: (1) log WARNING, (2) trigger garbage collection, (3) reduce batch size
        """
        ram_percent = memory_info.get('ram_percent', 0)
        ram_available_gb = memory_info.get('ram_available_gb', 0)

        # (1) Log WARNING
        logger.warning(
            f"⚠️  Memory pressure detected: {ram_percent:.1f}% used "
            f"({ram_available_gb:.1f}GB available)"
        )

        # (2) Trigger garbage collection
        logger.info("Triggering garbage collection to free memory...")
        gc.collect()

        # (3) Reduce batch size (via callback)
        if 'warning' in self._callbacks:
            try:
                self._callbacks['warning'](memory_info)
            except Exception as e:
                logger.error(f"Error in warning callback: {e}")

    def _handle_critical_memory(self, memory_info: Dict[str, Any]):
        """
        Handle critical-level memory pressure.

        Constraint arch-7: (4) show toast notification if >90%
        AC12: Show error dialog suggesting to close applications
        """
        ram_percent = memory_info.get('ram_percent', 0)
        ram_available_gb = memory_info.get('ram_available_gb', 0)

        # Log CRITICAL
        logger.critical(
            f"🚨 Critical memory pressure: {ram_percent:.1f}% used "
            f"({ram_available_gb:.1f}GB available, {2.0:.1f}GB recommended)"
        )

        # Trigger aggressive garbage collection
        logger.info("Triggering aggressive garbage collection...")
        gc.collect()
        gc.collect()  # Run twice for aggressive cleanup

        # Show critical notification (via callback)
        if 'critical' in self._callbacks:
            try:
                self._callbacks['critical'](memory_info)
            except Exception as e:
                logger.error(f"Error in critical callback: {e}")

        # Raise InsufficientMemoryError if available
        if InsufficientMemoryError:
            try:
                raise InsufficientMemoryError(
                    available_gb=ram_available_gb,
                    required_gb=2.0,
                    technical_details=f"Memory usage at {ram_percent:.1f}%"
                )
            except InsufficientMemoryError as e:
                # Don't crash the monitoring thread, just log
                logger.error(f"Insufficient memory: {e.user_message}")

    def _handle_normal_memory(self, memory_info: Dict[str, Any]):
        """Handle normal memory levels (no action needed)."""
        # Call normal callback if registered (for resetting optimizations)
        if 'normal' in self._callbacks:
            try:
                self._callbacks['normal'](memory_info)
            except Exception as e:
                logger.error(f"Error in normal callback: {e}")

    def get_current_memory_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current memory information.

        Returns:
            Dict with memory info or None if HardwareProfiler not available
        """
        if HardwareProfiler is None:
            return None

        try:
            return HardwareProfiler.monitor_resources()
        except Exception as e:
            logger.error(f"Failed to get memory info: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

_memory_monitor_instance: Optional[MemoryMonitor] = None


def get_memory_monitor() -> MemoryMonitor:
    """
    Get MemoryMonitor singleton instance.

    Returns:
        MemoryMonitor singleton
    """
    global _memory_monitor_instance

    if _memory_monitor_instance is None:
        _memory_monitor_instance = MemoryMonitor()

    return _memory_monitor_instance
