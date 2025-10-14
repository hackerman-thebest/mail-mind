"""
Cache Manager for MailMind

This module provides intelligent caching of email analysis results using SQLite.
Implements Story 1.6: Performance Optimization & Caching (AC1, AC8)

Key Features:
- Sub-100ms cache retrieval for analyzed emails
- Model version tracking for automatic cache invalidation
- Cache statistics and management (hit rate, size, entries)
- Manual cache clearing with confirmation
- LRU eviction support (optional)
- Database indexes for <10ms lookups

Integration:
- Used by EmailAnalysisEngine for result caching
- Standalone class that can be used independently

Performance Targets:
- Cache hit: <50ms average, <100ms max
- Cache write: <10ms average
- Cache lookup (indexed): <10ms
"""

import json
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from mailmind.database import DatabaseManager


logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages caching of email analysis results in SQLite.

    Provides fast cache retrieval (<100ms), model version tracking,
    and automatic cache invalidation when model versions change.

    Example:
        cache = CacheManager('data/mailmind.db')

        # Try to get cached result
        cached = cache.get_cached_analysis(message_id, current_model)
        if cached:
            return cached

        # Perform analysis...

        # Store result in cache
        cache.cache_analysis(message_id, analysis_result, current_model)
    """

    def __init__(self, db_path: str):
        """
        Initialize CacheManager with DatabaseManager.

        Args:
            db_path: Path to SQLite database file
        """
        # Use DatabaseManager for all database operations
        self.db = DatabaseManager(db_path=db_path)

        logger.info(f"CacheManager initialized with DatabaseManager: {db_path}")


    def get_cached_analysis(self, message_id: str, current_model_version: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached analysis result if available and valid using DatabaseManager.

        Args:
            message_id: Unique identifier for email
            current_model_version: Current LLM model version

        Returns:
            Cached analysis dict or None if not cached/invalid
        """
        start_time = time.time()

        try:
            cached_result = self.db.get_email_analysis(message_id)

            if cached_result:
                cached_model_version = cached_result.get('model_version')
                original_processing_time = cached_result.get('processing_time_ms', 0)

                # Cache invalidation: model version mismatch
                if cached_model_version != current_model_version:
                    logger.info(f"Cache invalidated for {message_id}: model version mismatch "
                               f"({cached_model_version} != {current_model_version})")
                    self.invalidate_entry(message_id)
                    return None

                # Extract analysis from cached result
                analysis = cached_result.get('analysis', {})
                analysis['cache_hit'] = True
                analysis['cache_retrieval_time_ms'] = int((time.time() - start_time) * 1000)
                analysis['original_processing_time_ms'] = original_processing_time

                logger.debug(f"Cache hit for {message_id} in {analysis['cache_retrieval_time_ms']}ms")

                return analysis

            return None

        except Exception as e:
            logger.error(f"Cache retrieval failed for {message_id}: {e}")
            return None

    def cache_analysis(self, message_id: str, analysis: Dict[str, Any], model_version: str):
        """
        Store analysis result in cache using DatabaseManager.

        Args:
            message_id: Unique identifier for email
            analysis: Analysis results dictionary
            model_version: LLM model version used for analysis
        """
        try:
            # Remove cache_hit flags before storing
            analysis_copy = analysis.copy()
            analysis_copy.pop('cache_hit', None)
            analysis_copy.pop('cache_retrieval_time_ms', None)
            analysis_copy.pop('original_processing_time_ms', None)

            processing_time = analysis.get('processing_time_ms', 0)

            # Insert using DatabaseManager
            self.db.insert_email_analysis(
                message_id=message_id,
                analysis=analysis_copy,
                metadata={
                    'model_version': model_version,
                    'processing_time_ms': processing_time
                }
            )

            logger.debug(f"Cached analysis for {message_id}")

        except Exception as e:
            logger.error(f"Failed to cache analysis for {message_id}: {e}")

    def invalidate_entry(self, message_id: str):
        """
        Remove specific cache entry using DatabaseManager.

        Args:
            message_id: Unique identifier for email
        """
        try:
            success = self.db.delete_email_analysis(message_id)

            if success:
                logger.debug(f"Invalidated cache entry for {message_id}")

        except Exception as e:
            logger.error(f"Failed to invalidate cache entry {message_id}: {e}")

    def invalidate_by_model_version(self, old_model_version: str) -> int:
        """
        Invalidate all cache entries for a specific model version using DatabaseManager.

        Args:
            old_model_version: Model version to invalidate

        Returns:
            Number of entries deleted
        """
        try:
            # Get all emails and delete those matching the model version
            deleted_count = 0
            all_emails = self.db.query_emails(filters={}, limit=10000)  # Get up to 10k emails

            for email in all_emails:
                if email.get('model_version') == old_model_version:
                    if self.db.delete_email_analysis(email['message_id']):
                        deleted_count += 1

            logger.info(f"Invalidated {deleted_count} cache entries for model {old_model_version}")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to invalidate cache by model version: {e}")
            return 0

    def clear_all(self) -> int:
        """
        Clear entire cache using DatabaseManager.

        Returns:
            Number of entries deleted
        """
        try:
            # Get count before deletion
            all_emails = self.db.query_emails(filters={}, limit=100000)
            count_before = len(all_emails)

            # Delete all email analyses
            success = self.db.delete_all_email_analyses()

            if success:
                logger.info(f"Cache cleared: {count_before} entries removed")
                return count_before
            else:
                return 0

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics using DatabaseManager.

        Returns:
            Statistics dictionary with:
            - total_entries: Total number of cached analyses
            - total_size_mb: Total size of database in MB
            - by_model: List of stats grouped by model version
        """
        try:
            # Get all emails to calculate stats
            all_emails = self.db.query_emails(filters={}, limit=100000)
            total_entries = len(all_emails)

            # Get database size
            total_size_mb = self.db.get_database_size_mb()

            # Group by model version
            model_stats = {}
            for email in all_emails:
                model_version = email.get('model_version', 'unknown')
                if model_version not in model_stats:
                    model_stats[model_version] = {
                        'model_version': model_version,
                        'entries': 0,
                        'oldest_entry': email.get('processed_date'),
                        'newest_entry': email.get('processed_date')
                    }
                model_stats[model_version]['entries'] += 1

                # Update oldest/newest
                processed_date = email.get('processed_date')
                if processed_date:
                    if processed_date < model_stats[model_version]['oldest_entry']:
                        model_stats[model_version]['oldest_entry'] = processed_date
                    if processed_date > model_stats[model_version]['newest_entry']:
                        model_stats[model_version]['newest_entry'] = processed_date

            by_model = list(model_stats.values())

            return {
                'total_entries': total_entries,
                'total_size_mb': total_size_mb,
                'by_model': by_model
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                'total_entries': 0,
                'total_size_mb': 0.0,
                'by_model': [],
                'error': str(e)
            }

    def evict_lru(self, max_entries: int) -> int:
        """
        Evict oldest cache entries (simplified LRU using processed_date).

        Note: This uses processed_date instead of last_accessed since the
        email_analysis table doesn't track access times.

        Args:
            max_entries: Maximum number of entries to keep

        Returns:
            Number of entries evicted
        """
        try:
            # Get all emails sorted by processed date (oldest first)
            all_emails = self.db.query_emails(filters={}, limit=100000)
            current_count = len(all_emails)

            if current_count <= max_entries:
                return 0

            # Sort by processed_date (oldest first)
            sorted_emails = sorted(all_emails, key=lambda x: x.get('processed_date', ''))

            # Delete oldest entries
            entries_to_delete = current_count - max_entries
            deleted_count = 0

            for i in range(entries_to_delete):
                if self.db.delete_email_analysis(sorted_emails[i]['message_id']):
                    deleted_count += 1

            logger.info(f"LRU eviction: removed {deleted_count} entries (keeping {max_entries})")

            return deleted_count

        except Exception as e:
            logger.error(f"LRU eviction failed: {e}")
            return 0
