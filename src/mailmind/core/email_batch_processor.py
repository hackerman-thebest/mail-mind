"""
Email Batch Processor - Parallel Email Processing

Implements parallel email processing using ThreadPoolExecutor and connection pooling
for improved throughput and performance.

Story 3.3 AC4: Parallel Email Processing
Story 3.3 AC5: Performance Target (10-15 emails/minute)
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result from batch processing operation."""
    total: int
    success: int
    failed: int
    results: List[Dict[str, Any]]
    elapsed_time: float
    emails_per_minute: float


class EmailBatchProcessor:
    """
    Process emails in parallel using connection pool.

    Story 3.3 AC4: Parallel processing implementation
    Story 3.3 AC5: Performance optimization for 10-15 emails/minute target

    Implements:
    - ThreadPoolExecutor for concurrent processing
    - Individual email failure isolation (don't stop batch)
    - Timeout handling (30s per email max)
    - Progress callback support
    - Result aggregation with success/failure counts
    - Performance metrics calculation

    Usage:
        pool = OllamaConnectionPool(size=3)
        engine = EmailAnalysisEngine(...)
        processor = EmailBatchProcessor(engine, pool)

        results = processor.process_batch(emails, progress_callback=my_callback)
        print(f"Processed {results.success}/{results.total} emails")
        print(f"Throughput: {results.emails_per_minute:.1f} emails/minute")
    """

    def __init__(self, analysis_engine, pool):
        """
        Initialize batch processor.

        Args:
            analysis_engine: EmailAnalysisEngine instance for processing emails
            pool: OllamaConnectionPool for concurrent connection management

        Story 3.3 AC4: Configure max_workers based on pool size
        """
        self.engine = analysis_engine
        self.pool = pool

        # Story 3.3 AC4: max_workers = pool.size for optimal parallelism
        self.executor = ThreadPoolExecutor(max_workers=pool.size)

        logger.info(f"EmailBatchProcessor initialized with {pool.size} workers")

    def process_batch(
        self,
        emails: List[Any],
        progress_callback: Optional[Callable[[int, int], None]] = None,
        email_timeout: float = 30.0
    ) -> BatchResult:
        """
        Process emails concurrently using connection pool.

        Story 3.3 AC4: Parallel email processing with error isolation
        Story 3.3 AC5: Performance tracking (emails/minute)

        Args:
            emails: List of email objects to process
            progress_callback: Optional callback function(current, total) for progress updates
            email_timeout: Maximum time per email in seconds (default: 30s)

        Returns:
            BatchResult with success/failure counts, results, and performance metrics

        Implementation:
        - Submits all emails to ThreadPoolExecutor
        - Waits for completion with per-email timeout
        - Individual failures logged but don't stop batch
        - Returns aggregated results with performance metrics
        """
        if not emails:
            logger.warning("process_batch called with empty email list")
            return BatchResult(
                total=0,
                success=0,
                failed=0,
                results=[],
                elapsed_time=0.0,
                emails_per_minute=0.0
            )

        logger.info(f"Processing batch of {len(emails)} emails with {self.pool.size} workers...")
        start_time = time.time()

        # Story 3.3 AC4: Submit all emails for parallel processing
        futures = []
        for email in emails:
            future = self.executor.submit(self._process_one, email)
            futures.append((email, future))

        # Story 3.3 AC4: Wait for completion with individual error handling
        results = []
        success_count = 0
        failed_count = 0

        for i, (email, future) in enumerate(futures):
            try:
                # Story 3.3 AC4: Per-email timeout (30s default)
                result = future.result(timeout=email_timeout)

                if result.get('error'):
                    # Email processed but had an error
                    failed_count += 1
                    logger.warning(
                        f"Email {i+1}/{len(emails)} failed: {result.get('error')}"
                    )
                else:
                    success_count += 1
                    logger.debug(f"Email {i+1}/{len(emails)} processed successfully")

                results.append(result)

            except FutureTimeoutError:
                # Story 3.3 AC4: Timeout handling
                failed_count += 1
                error_result = {
                    'error': f'Timeout after {email_timeout}s',
                    'email_id': getattr(email, 'id', None),
                    'timeout': True
                }
                results.append(error_result)
                logger.error(
                    f"Email {i+1}/{len(emails)} timed out after {email_timeout}s"
                )

            except Exception as e:
                # Story 3.3 AC4: Individual email failures don't stop batch
                failed_count += 1
                error_result = {
                    'error': str(e),
                    'email_id': getattr(email, 'id', None),
                    'exception': True
                }
                results.append(error_result)
                logger.error(
                    f"Email {i+1}/{len(emails)} failed with exception: {e}",
                    exc_info=True
                )

            # Story 3.3 AC4: Progress callback support
            if progress_callback:
                try:
                    progress_callback(i + 1, len(emails))
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")

        # Story 3.3 AC5: Calculate performance metrics
        elapsed_time = time.time() - start_time
        emails_per_minute = (len(emails) / elapsed_time) * 60 if elapsed_time > 0 else 0.0

        logger.info(
            f"Batch processing complete: {success_count}/{len(emails)} successful, "
            f"{failed_count} failed in {elapsed_time:.2f}s "
            f"({emails_per_minute:.1f} emails/minute)"
        )

        return BatchResult(
            total=len(emails),
            success=success_count,
            failed=failed_count,
            results=results,
            elapsed_time=elapsed_time,
            emails_per_minute=emails_per_minute
        )

    def _process_one(self, email: Any) -> Dict[str, Any]:
        """
        Process single email with pooled connection.

        Story 3.3 AC4: Use connection pool context manager

        Args:
            email: Email object to process

        Returns:
            Dictionary with analysis results or error information
        """
        try:
            # Story 3.3 AC2: Use connection pool context manager
            with self.pool.acquire() as conn:
                # Process email using analysis engine
                # Note: EmailAnalysisEngine.analyze_email needs to accept conn parameter
                result = self.engine.analyze_email(email, conn)
                return result

        except Exception as e:
            logger.error(f"Error processing email: {e}", exc_info=True)
            return {
                'error': str(e),
                'email_id': getattr(email, 'id', None)
            }

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the thread pool executor.

        Story 3.3 arch-8: Graceful cleanup

        Args:
            wait: If True, wait for all submitted tasks to complete
        """
        logger.info("Shutting down EmailBatchProcessor...")
        self.executor.shutdown(wait=wait)
        logger.info("EmailBatchProcessor shutdown complete")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.shutdown(wait=True)
        return False
