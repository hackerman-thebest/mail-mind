"""
Performance Optimization & Caching Demo

This demo showcases Story 1.6: Performance Optimization & Caching features.

Demonstrates:
1. CacheManager - Sub-100ms cache retrieval
2. HardwareProfiler - System hardware detection and optimization
3. PerformanceTracker - Real-time metrics tracking
4. BatchQueueManager - Batch processing with memory monitoring
5. Memory management and graceful degradation

Usage:
    python examples/performance_optimization_demo.py
"""

import time
from pathlib import Path

from src.mailmind.core.cache_manager import CacheManager
from src.mailmind.core.hardware_profiler import HardwareProfiler
from src.mailmind.core.performance_tracker import PerformanceTracker
from src.mailmind.core.batch_queue_manager import BatchQueueManager, QueuePriority


def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70 + "\n")


def print_subheader(title):
    """Print formatted subheader."""
    print("\n" + "-" * 70)
    print(title)
    print("-" * 70)


def demo_hardware_profiling():
    """Demo 1: Hardware Profiling"""
    print_header("DEMO 1: Hardware Profiling")

    print("Detecting system hardware...")
    profile = HardwareProfiler.detect_hardware()

    print("\n✓ Hardware Detection Complete\n")
    print("System Hardware:")
    print(f"  CPU: {profile['cpu_cores']} cores ({profile['cpu_logical_cores']} logical)")
    print(f"  RAM: {profile['ram_total_gb']}GB total, {profile['ram_available_gb']}GB available")
    print(f"  GPU: {profile['gpu_detected'] or 'Not detected (CPU-only mode)'}")

    if profile['gpu_detected']:
        print(f"  VRAM: {profile['gpu_vram_gb']}GB")
        print(f"  Driver: {profile['gpu_driver_version']}")

    print(f"\nHardware Tier: {profile['hardware_tier']}")
    print(f"Expected Performance: {profile['expected_tokens_per_second']} tokens/second")
    print(f"Recommended Model: {profile['recommended_model']}")

    # Show optimization settings
    print("\nOptimized Settings for Your Hardware:")
    settings = HardwareProfiler.get_optimization_settings(profile)
    print(f"  Batch Size: {settings['batch_size']} emails")
    print(f"  Timeout: {settings['timeout_seconds']}s")
    print(f"  Max Concurrent: {settings['max_concurrent']}")
    print(f"  GPU Enabled: {settings['enable_gpu']}")
    print(f"  Context Window: {settings['context_window']}")

    # Show real-time resource monitoring
    print("\nReal-Time Resource Monitoring:")
    resources = HardwareProfiler.monitor_resources()
    print(f"  CPU Usage: {resources['cpu_percent']:.1f}%")
    print(f"  RAM Usage: {resources['ram_used_gb']:.2f}GB ({resources['ram_percent']:.1f}%)")
    print(f"  RAM Available: {resources['ram_available_gb']:.2f}GB")


def demo_cache_manager():
    """Demo 2: CacheManager - Sub-100ms Cache Retrieval"""
    print_header("DEMO 2: CacheManager - Sub-100ms Cache Retrieval")

    # Initialize cache manager
    db_path = "data/demo_cache.db"
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    cache = CacheManager(db_path)

    print("Initializing CacheManager...")
    print(f"✓ Cache ready: {db_path}\n")

    # Sample analysis result
    analysis = {
        'priority': 'High',
        'confidence': 0.92,
        'summary': 'Important email about project deadline',
        'tags': ['deadline', 'project', 'urgent'],
        'sentiment': 'urgent',
        'action_items': ['Review proposal by Friday'],
        'processing_time_ms': 1847,
        'tokens_per_second': 52.3,
        'model_version': 'llama3.1:8b-instruct-q4_K_M'
    }

    message_id = 'test_email_001'
    model_version = 'llama3.1:8b-instruct-q4_K_M'

    # Cache miss (first time)
    print_subheader("Cache Miss (First Analysis)")
    start = time.time()
    cached = cache.get_cached_analysis(message_id, model_version)
    miss_time_ms = (time.time() - start) * 1000

    print(f"Cache lookup time: {miss_time_ms:.2f}ms")
    print(f"Result: {cached}")
    print("✓ Cache miss as expected (email not yet cached)")

    # Store in cache
    print("\nStoring analysis in cache...")
    cache.cache_analysis(message_id, analysis, model_version)
    print("✓ Analysis cached successfully")

    # Cache hit (second time)
    print_subheader("Cache Hit (Second Analysis)")
    start = time.time()
    cached = cache.get_cached_analysis(message_id, model_version)
    hit_time_ms = (time.time() - start) * 1000

    print(f"Cache lookup time: {hit_time_ms:.2f}ms")
    print(f"\nOriginal processing time: {analysis['processing_time_ms']}ms")
    print(f"Cache retrieval time: {hit_time_ms:.2f}ms")
    print(f"Speedup: {analysis['processing_time_ms'] / hit_time_ms:.1f}x faster! 🚀")

    if hit_time_ms < 100:
        print(f"✓ Performance target met: <100ms (actual: {hit_time_ms:.2f}ms)")
    else:
        print(f"⚠ Warning: Cache retrieval took longer than target (<100ms)")

    # Show cache statistics
    print_subheader("Cache Statistics")

    # Add more entries to cache
    for i in range(10):
        cache.cache_analysis(f'email_{i}', analysis, model_version)

    stats = cache.get_cache_stats()
    print(f"Total Entries: {stats['total_entries']}")
    print(f"Cache Size: {stats['total_size_mb']:.2f} MB")
    print(f"Avg Access Count: {stats['avg_access_count']}")

    if stats['by_model']:
        print(f"\nBy Model Version:")
        for model_stats in stats['by_model']:
            print(f"  {model_stats['model_version']}: {model_stats['entries']} entries")

    # Demonstrate cache invalidation
    print_subheader("Cache Invalidation")
    print("Simulating model version change...")

    old_model = 'llama3.1:8b-instruct-q4_K_M'
    new_model = 'llama3.2:3b-instruct-q4_K_M'

    deleted_count = cache.invalidate_by_model_version(old_model)
    print(f"✓ Invalidated {deleted_count} entries for old model version")
    print("Reason: Model version changed, cache must be refreshed")


def demo_performance_tracker():
    """Demo 3: PerformanceTracker - Real-Time Metrics"""
    print_header("DEMO 3: PerformanceTracker - Real-Time Metrics")

    # Initialize tracker
    db_path = "data/demo_performance.db"
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    tracker = PerformanceTracker(db_path, hardware_tier='Recommended')

    print("Initializing PerformanceTracker...")
    print(f"✓ Tracker ready: {db_path}\n")

    # Log some sample operations
    print_subheader("Logging Performance Metrics")

    print("Simulating 10 email analysis operations...\n")
    for i in range(10):
        # Simulate varying performance
        processing_time = 1500 + (i * 100)
        tokens_per_sec = 50.0 + (i * 2)

        tracker.log_operation(
            operation='email_analysis',
            processing_time_ms=processing_time,
            tokens_per_second=tokens_per_sec,
            memory_usage_mb=3000 + (i * 50),
            model_version='llama3.1:8b-instruct-q4_K_M'
        )

        print(f"  Operation {i+1}: {processing_time}ms, {tokens_per_sec:.1f} t/s")
        time.sleep(0.1)  # Small delay

    print("\n✓ 10 operations logged successfully")

    # Get metrics summary
    print_subheader("Performance Metrics Summary (Last 7 Days)")

    summary = tracker.get_metrics_summary(days=7)
    if 'email_analysis' in summary:
        metrics = summary['email_analysis']
        print(f"Operation: email_analysis")
        print(f"  Count: {metrics['count']}")
        print(f"  Avg Time: {metrics['avg_time_ms']:.2f}ms")
        print(f"  Avg Tokens/Sec: {metrics['avg_tokens_per_sec']:.2f}")
        print(f"  Min Time: {metrics['min_time_ms']}ms")
        print(f"  Max Time: {metrics['max_time_ms']}ms")

    # Get real-time metrics
    print_subheader("Real-Time Metrics (Last 10 Operations)")

    realtime = tracker.get_realtime_metrics()
    print(f"Operations Tracked: {len(realtime['last_10_operations'])}")
    print(f"Avg Tokens/Sec: {realtime['avg_tokens_per_sec']:.2f}")
    print(f"Avg Processing Time: {realtime['avg_processing_time_ms']:.2f}ms")

    # Export to CSV
    print_subheader("Exporting to CSV")

    csv_path = "data/performance_export.csv"
    success = tracker.export_to_csv(csv_path, days=7)

    if success:
        print(f"✓ Performance data exported to: {csv_path}")
        print("  Use Excel or data analysis tools to view trends")


def demo_batch_queue_manager():
    """Demo 4: BatchQueueManager - Memory-Aware Batch Processing"""
    print_header("DEMO 4: BatchQueueManager - Memory-Aware Batch Processing")

    # Initialize batch queue manager
    db_path = "data/demo_queue.db"
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    manager = BatchQueueManager(
        db_path=db_path,
        memory_limit_gb=8.0,
        target_throughput=15
    )

    print("Initializing BatchQueueManager...")
    print(f"✓ Manager ready: {db_path}")
    print(f"  Memory Limit: 8.0 GB")
    print(f"  Target Throughput: 15 emails/min")
    print(f"  Initial Batch Size: {manager.current_batch_size}\n")

    # Add items to queue with different priorities
    print_subheader("Adding Items to Queue")

    print("Adding 5 high-priority emails...")
    for i in range(5):
        manager.add_to_queue(
            item_id=f'high_priority_{i}',
            data={'email_id': f'email_h{i}', 'subject': f'Urgent email {i}'},
            priority=QueuePriority.HIGH
        )

    print("Adding 3 medium-priority emails...")
    for i in range(3):
        manager.add_to_queue(
            item_id=f'medium_priority_{i}',
            data={'email_id': f'email_m{i}', 'subject': f'Standard email {i}'},
            priority=QueuePriority.MEDIUM
        )

    print("Adding 2 low-priority emails...")
    for i in range(2):
        manager.add_to_queue(
            item_id=f'low_priority_{i}',
            data={'email_id': f'email_l{i}', 'subject': f'Newsletter {i}'},
            priority=QueuePriority.LOW
        )

    # Show queue status
    print("\n✓ Queue populated\n")
    status = manager.get_queue_status()
    print("Queue Status:")
    print(f"  Total Items: {status['total_items']}")
    print(f"  Pending: {status['pending']}")
    print(f"  Processing: {status['processing']}")
    print(f"  Completed: {status['completed']}")

    # Process queue
    print_subheader("Processing Queue (Priority Order)")

    print("Processing queue items...")
    print("Note: High-priority items will be processed first\n")

    def mock_processor(data):
        """Mock email processor."""
        time.sleep(0.2)  # Simulate processing
        return {'result': f"Processed {data['email_id']}", 'status': 'success'}

    def progress_callback(current, total, result):
        """Progress callback."""
        print(f"  [{current}/{total}] {result['result']}")

    results = manager.process_queue(
        processor_func=mock_processor,
        callback=progress_callback
    )

    print(f"\n✓ Queue processing complete")
    print(f"  Results: {len(results)} items processed")

    # Show final status
    final_status = manager.get_queue_status()
    print(f"\nFinal Queue Status:")
    print(f"  Pending: {final_status['pending']}")
    print(f"  Completed: {final_status['completed']}")
    print(f"  Failed: {final_status['failed']}")


def demo_memory_monitoring():
    """Demo 5: Memory Monitoring and Graceful Degradation"""
    print_header("DEMO 5: Memory Monitoring and Graceful Degradation")

    print("Checking current system memory...")
    resources = HardwareProfiler.monitor_resources()

    print(f"\nCurrent System State:")
    print(f"  RAM Used: {resources['ram_used_gb']:.2f}GB")
    print(f"  RAM Usage: {resources['ram_percent']:.1f}%")
    print(f"  RAM Available: {resources['ram_available_gb']:.2f}GB")

    # Check memory pressure
    print("\nMemory Pressure Checks:")

    is_pressure_85 = HardwareProfiler.check_memory_pressure(threshold_percent=85.0)
    print(f"  85% threshold: {'⚠ PRESSURE' if is_pressure_85 else '✓ OK'}")

    is_pressure_90 = HardwareProfiler.check_memory_pressure(threshold_percent=90.0)
    print(f"  90% threshold: {'🔴 CRITICAL' if is_pressure_90 else '✓ OK'}")

    print("\nGraceful Degradation Strategy:")
    print("  - At 85% memory: Trigger garbage collection")
    print("  - At 90% memory: Reduce batch size by 50%")
    print("  - At 95% memory: Process items sequentially (batch_size=1)")
    print("  - At 98% memory: Reject new work to prevent crashes")

    print("\nPerformance Optimization:")
    profile = HardwareProfiler.detect_hardware()
    settings = HardwareProfiler.get_optimization_settings(profile)

    print(f"  Hardware Tier: {profile['hardware_tier']}")
    print(f"  Recommended Batch Size: {settings['batch_size']}")
    print(f"  Timeout Limit: {settings['timeout_seconds']}s")
    print(f"  Max Concurrent Operations: {settings['max_concurrent']}")

    if profile['hardware_tier'] == 'Insufficient':
        print("\n⚠ Warning: System resources below recommended minimum")
        print("  Consider:")
        print("    - Upgrading to 16GB RAM minimum")
        print("    - Reducing batch size to 1")
        print("    - Increasing timeout to 60s")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("  MAILMIND - PERFORMANCE OPTIMIZATION & CACHING DEMO  ".center(70))
    print("  Story 1.6: CacheManager, HardwareProfiler, PerformanceTracker  ".center(70))
    print("=" * 70)

    demos = [
        ("Hardware Profiling", demo_hardware_profiling),
        ("Cache Manager", demo_cache_manager),
        ("Performance Tracker", demo_performance_tracker),
        ("Batch Queue Manager", demo_batch_queue_manager),
        ("Memory Monitoring", demo_memory_monitoring)
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            demo_func()
        except KeyboardInterrupt:
            print("\n\n⚠ Demo interrupted by user")
            break
        except Exception as e:
            print(f"\n\n❌ Error in {name}: {e}")
            import traceback
            traceback.print_exc()

        # Ask to continue (except for last demo)
        if i < len(demos):
            print("\n" + "=" * 70)
            response = input(f"\nContinue to next demo? (y/n) [y]: ").strip().lower()
            if response == 'n':
                print("\nDemo session ended by user.")
                break

    print("\n" + "=" * 70)
    print("DEMO SESSION COMPLETE".center(70))
    print("=" * 70)
    print("\nKey Features Demonstrated:")
    print("  ✓ Hardware profiling and tier classification")
    print("  ✓ Sub-100ms cache retrieval (10-50x speedup)")
    print("  ✓ Real-time performance metrics tracking")
    print("  ✓ Priority-based batch queue processing")
    print("  ✓ Memory monitoring and graceful degradation")
    print("\nFor more information, see:")
    print("  - docs/stories/story-1.6.md")
    print("  - src/mailmind/core/cache_manager.py")
    print("  - src/mailmind/core/hardware_profiler.py")
    print("  - src/mailmind/core/performance_tracker.py")
    print("  - src/mailmind/core/batch_queue_manager.py")
    print()


if __name__ == "__main__":
    main()
