"""
Performance Testing for Database Encryption

Story 3.1 AC4: Performance Overhead Testing
- Benchmark baseline (unencrypted) performance
- Benchmark encrypted performance
- Calculate overhead for INSERT, SELECT, UPDATE, DELETE
- Target: <10% overhead (goal <5%)
- Document performance metrics

Usage:
    python tests/performance/test_encryption_performance.py

Output:
    Performance report with overhead percentages for all operations
"""

import os
import sys
import time
import tempfile
import logging
from pathlib import Path
from typing import Dict, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Suppress debug logs during benchmarking
    format="%(message)s"
)
logger = logging.getLogger(__name__)

# Import database modules
try:
    import pysqlcipher3.dbapi2 as sqlite3_encrypted
    SQLCIPHER_AVAILABLE = True
except ImportError:
    print("ERROR: pysqlcipher3 not available - cannot test encrypted performance")
    SQLCIPHER_AVAILABLE = False
    sys.exit(1)

import sqlite3 as sqlite3_plain

# Test configuration
NUM_EMAILS = 1000  # Number of test emails for benchmarking
BATCH_SIZE = 100   # Batch size for INSERT operations
TEST_KEY = "0" * 128  # 64-byte hex-encoded test key


# ============================================================================
# Database Setup
# ============================================================================

def create_test_schema(conn):
    """Create test schema matching MailMind email_analysis table."""
    cursor = conn.cursor()

    # Create emails table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE NOT NULL,
            subject TEXT,
            sender TEXT NOT NULL,
            received_date TEXT NOT NULL,
            body_text TEXT,
            priority_score REAL,
            category TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create index
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_emails_priority
        ON emails(priority_score DESC)
    """)

    conn.commit()


def generate_test_email(email_id: int) -> tuple:
    """Generate test email data."""
    return (
        f"test-{email_id}@example.com",
        f"Test Subject {email_id}",
        f"sender-{email_id % 10}@example.com",
        "2025-10-15T10:00:00",
        f"Test email body {email_id} with some content to simulate real emails. " * 10,
        float(email_id % 100) / 100.0,  # Priority score 0.0-1.0
        ["urgent", "normal", "low"][email_id % 3]
    )


# ============================================================================
# Benchmark Functions
# ============================================================================

def benchmark_insert(conn, num_emails: int) -> float:
    """
    Benchmark INSERT performance.

    Args:
        conn: Database connection
        num_emails: Number of emails to insert

    Returns:
        float: Time taken in seconds
    """
    cursor = conn.cursor()

    start_time = time.time()

    for i in range(num_emails):
        email_data = generate_test_email(i)
        cursor.execute("""
            INSERT INTO emails (message_id, subject, sender, received_date, body_text, priority_score, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, email_data)

        # Commit in batches for realistic performance
        if (i + 1) % BATCH_SIZE == 0:
            conn.commit()

    conn.commit()  # Final commit

    end_time = time.time()
    return end_time - start_time


def benchmark_select_all(conn) -> float:
    """
    Benchmark SELECT all emails.

    Args:
        conn: Database connection

    Returns:
        float: Time taken in seconds
    """
    cursor = conn.cursor()

    start_time = time.time()

    cursor.execute("SELECT * FROM emails")
    rows = cursor.fetchall()

    end_time = time.time()

    # Verify we got data
    assert len(rows) > 0, "SELECT returned no rows"

    return end_time - start_time


def benchmark_select_filtered(conn) -> float:
    """
    Benchmark SELECT with WHERE clause and ORDER BY.

    Args:
        conn: Database connection

    Returns:
        float: Time taken in seconds
    """
    cursor = conn.cursor()

    start_time = time.time()

    cursor.execute("""
        SELECT * FROM emails
        WHERE priority_score > 0.5
        ORDER BY priority_score DESC
        LIMIT 100
    """)
    rows = cursor.fetchall()

    end_time = time.time()

    return end_time - start_time


def benchmark_update(conn) -> float:
    """
    Benchmark UPDATE operations.

    Args:
        conn: Database connection

    Returns:
        float: Time taken in seconds
    """
    cursor = conn.cursor()

    start_time = time.time()

    # Update priority scores
    cursor.execute("""
        UPDATE emails
        SET priority_score = priority_score * 0.9
        WHERE category = 'urgent'
    """)

    conn.commit()

    end_time = time.time()

    return end_time - start_time


def benchmark_delete(conn) -> float:
    """
    Benchmark DELETE operations.

    Args:
        conn: Database connection

    Returns:
        float: Time taken in seconds
    """
    cursor = conn.cursor()

    start_time = time.time()

    # Delete low priority emails
    cursor.execute("""
        DELETE FROM emails
        WHERE priority_score < 0.1
    """)

    conn.commit()

    end_time = time.time()

    return end_time - start_time


# ============================================================================
# Test Runner
# ============================================================================

def run_unencrypted_benchmark(db_path: str) -> Dict[str, float]:
    """
    Run benchmark on unencrypted database.

    Args:
        db_path: Path to database file

    Returns:
        dict: Benchmark results {operation: time_seconds}
    """
    print(f"\n{'='*70}")
    print("UNENCRYPTED DATABASE BENCHMARK")
    print(f"{'='*70}")

    # Create database
    conn = sqlite3_plain.connect(db_path)
    create_test_schema(conn)

    results = {}

    # INSERT benchmark
    print(f"\nINSERT {NUM_EMAILS} emails...")
    results["insert"] = benchmark_insert(conn, NUM_EMAILS)
    print(f"  Time: {results['insert']:.3f}s ({NUM_EMAILS/results['insert']:.1f} emails/sec)")

    # SELECT ALL benchmark
    print(f"\nSELECT * FROM emails...")
    results["select_all"] = benchmark_select_all(conn)
    print(f"  Time: {results['select_all']:.3f}s")

    # SELECT FILTERED benchmark
    print(f"\nSELECT with WHERE and ORDER BY...")
    results["select_filtered"] = benchmark_select_filtered(conn)
    print(f"  Time: {results['select_filtered']:.3f}s")

    # UPDATE benchmark
    print(f"\nUPDATE emails...")
    results["update"] = benchmark_update(conn)
    print(f"  Time: {results['update']:.3f}s")

    # DELETE benchmark
    print(f"\nDELETE emails...")
    results["delete"] = benchmark_delete(conn)
    print(f"  Time: {results['delete']:.3f}s")

    conn.close()

    return results


def run_encrypted_benchmark(db_path: str, encryption_key: str) -> Dict[str, float]:
    """
    Run benchmark on encrypted database.

    Args:
        db_path: Path to database file
        encryption_key: Hex-encoded encryption key

    Returns:
        dict: Benchmark results {operation: time_seconds}
    """
    print(f"\n{'='*70}")
    print("ENCRYPTED DATABASE BENCHMARK (SQLCipher)")
    print(f"{'='*70}")

    # Create encrypted database
    conn = sqlite3_encrypted.connect(db_path)
    conn.execute(f"PRAGMA key = '{encryption_key}'")
    create_test_schema(conn)

    results = {}

    # INSERT benchmark
    print(f"\nINSERT {NUM_EMAILS} emails...")
    results["insert"] = benchmark_insert(conn, NUM_EMAILS)
    print(f"  Time: {results['insert']:.3f}s ({NUM_EMAILS/results['insert']:.1f} emails/sec)")

    # SELECT ALL benchmark
    print(f"\nSELECT * FROM emails...")
    results["select_all"] = benchmark_select_all(conn)
    print(f"  Time: {results['select_all']:.3f}s")

    # SELECT FILTERED benchmark
    print(f"\nSELECT with WHERE and ORDER BY...")
    results["select_filtered"] = benchmark_select_filtered(conn)
    print(f"  Time: {results['select_filtered']:.3f}s")

    # UPDATE benchmark
    print(f"\nUPDATE emails...")
    results["update"] = benchmark_update(conn)
    print(f"  Time: {results['update']:.3f}s")

    # DELETE benchmark
    print(f"\nDELETE emails...")
    results["delete"] = benchmark_delete(conn)
    print(f"  Time: {results['delete']:.3f}s")

    conn.close()

    return results


def calculate_overhead(unencrypted_results: Dict[str, float], encrypted_results: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate encryption overhead percentages.

    Args:
        unencrypted_results: Unencrypted benchmark results
        encrypted_results: Encrypted benchmark results

    Returns:
        dict: Overhead percentages {operation: overhead_percent}
    """
    overhead = {}

    for operation in unencrypted_results:
        unenc_time = unencrypted_results[operation]
        enc_time = encrypted_results[operation]

        # Calculate overhead percentage: ((encrypted - unencrypted) / unencrypted) * 100
        overhead_pct = ((enc_time - unenc_time) / unenc_time) * 100
        overhead[operation] = overhead_pct

    return overhead


def print_summary(unencrypted_results: Dict[str, float], encrypted_results: Dict[str, float], overhead: Dict[str, float]):
    """Print performance summary report."""

    print(f"\n{'='*70}")
    print("PERFORMANCE SUMMARY")
    print(f"{'='*70}")

    print(f"\n{'Operation':<20} {'Unencrypted':<15} {'Encrypted':<15} {'Overhead':<15} {'Status':<10}")
    print("-" * 70)

    for operation in unencrypted_results:
        unenc_time = unencrypted_results[operation]
        enc_time = encrypted_results[operation]
        overhead_pct = overhead[operation]

        # Determine status
        if overhead_pct < 5.0:
            status = "✓ EXCELLENT"
        elif overhead_pct < 10.0:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"

        print(f"{operation:<20} {unenc_time:>8.3f}s      {enc_time:>8.3f}s      {overhead_pct:>7.2f}%      {status}")

    # Overall assessment
    avg_overhead = sum(overhead.values()) / len(overhead)
    max_overhead = max(overhead.values())

    print("\n" + "=" * 70)
    print("OVERALL ASSESSMENT")
    print("=" * 70)
    print(f"Average Overhead: {avg_overhead:.2f}%")
    print(f"Maximum Overhead: {max_overhead:.2f}%")

    if max_overhead < 5.0:
        print("\n✓ Result: EXCELLENT - All operations under 5% overhead (goal achieved)")
    elif max_overhead < 10.0:
        print("\n✓ Result: PASS - All operations under 10% overhead (AC4 satisfied)")
    else:
        print(f"\n✗ Result: FAIL - Some operations exceed 10% overhead (AC4 NOT satisfied)")
        print("   Optimization required!")

    print("\n" + "=" * 70)


# ============================================================================
# Main
# ============================================================================

def main():
    """Run performance benchmarks."""

    print(f"\nMailMind Database Encryption Performance Test")
    print(f"Story 3.1 AC4: Performance Overhead <10% (target <5%)")
    print(f"\nTest Configuration:")
    print(f"  - Number of emails: {NUM_EMAILS}")
    print(f"  - Batch size: {BATCH_SIZE}")
    print(f"  - SQLCipher available: {SQLCIPHER_AVAILABLE}")

    # Create temporary database files
    unenc_fd, unenc_path = tempfile.mkstemp(suffix=".db", prefix="benchmark_unenc_")
    os.close(unenc_fd)

    enc_fd, enc_path = tempfile.mkstemp(suffix=".db", prefix="benchmark_enc_")
    os.close(enc_fd)

    try:
        # Run benchmarks
        unencrypted_results = run_unencrypted_benchmark(unenc_path)
        encrypted_results = run_encrypted_benchmark(enc_path, TEST_KEY)

        # Calculate overhead
        overhead = calculate_overhead(unencrypted_results, encrypted_results)

        # Print summary
        print_summary(unencrypted_results, encrypted_results, overhead)

        # Return exit code based on results
        max_overhead = max(overhead.values())
        if max_overhead >= 10.0:
            print("\nERROR: Performance test FAILED - overhead exceeds 10%")
            return 1
        else:
            print("\nSUCCESS: Performance test PASSED - all operations under 10% overhead")
            return 0

    finally:
        # Cleanup temporary files
        try:
            if os.path.exists(unenc_path):
                os.remove(unenc_path)
            if os.path.exists(enc_path):
                os.remove(enc_path)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp files: {e}")


if __name__ == "__main__":
    sys.exit(main())
