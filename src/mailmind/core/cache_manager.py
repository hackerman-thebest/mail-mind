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
import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path


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
        Initialize CacheManager with SQLite database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_database()

        logger.info(f"CacheManager initialized with database: {db_path}")

    def _init_database(self):
        """Initialize cache table with indexes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create analysis_cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_cache (
                message_id TEXT PRIMARY KEY,
                analysis_json TEXT NOT NULL,
                model_version TEXT NOT NULL,
                processing_time_ms INTEGER,
                cached_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        ''')

        # Index for fast lookups by message_id (already covered by PRIMARY KEY)
        # Index for cache invalidation by model version
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cache_model_version
            ON analysis_cache(model_version)
        ''')

        # Index for cache management (oldest entries for LRU)
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cache_last_accessed
            ON analysis_cache(last_accessed)
        ''')

        conn.commit()
        conn.close()

        logger.debug("Cache database schema initialized")

    def get_cached_analysis(self, message_id: str, current_model_version: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached analysis result if available and valid.

        Args:
            message_id: Unique identifier for email
            current_model_version: Current LLM model version

        Returns:
            Cached analysis dict or None if not cached/invalid
        """
        start_time = time.time()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT analysis_json, model_version, processing_time_ms
                FROM analysis_cache
                WHERE message_id = ?
            ''', (message_id,))

            row = cursor.fetchone()

            if row:
                analysis_json, cached_model_version, original_processing_time = row

                # Cache invalidation: model version mismatch
                if cached_model_version != current_model_version:
                    logger.info(f"Cache invalidated for {message_id}: model version mismatch "
                               f"({cached_model_version} != {current_model_version})")
                    self.invalidate_entry(message_id)
                    conn.close()
                    return None

                # Update access statistics
                cursor.execute('''
                    UPDATE analysis_cache
                    SET last_accessed = CURRENT_TIMESTAMP,
                        access_count = access_count + 1
                    WHERE message_id = ?
                ''', (message_id,))
                conn.commit()

                # Parse cached analysis
                analysis = json.loads(analysis_json)
                analysis['cache_hit'] = True
                analysis['cache_retrieval_time_ms'] = int((time.time() - start_time) * 1000)
                analysis['original_processing_time_ms'] = original_processing_time

                conn.close()

                logger.debug(f"Cache hit for {message_id} in {analysis['cache_retrieval_time_ms']}ms")

                return analysis

            conn.close()
            return None

        except Exception as e:
            logger.error(f"Cache retrieval failed for {message_id}: {e}")
            return None

    def cache_analysis(self, message_id: str, analysis: Dict[str, Any], model_version: str):
        """
        Store analysis result in cache.

        Args:
            message_id: Unique identifier for email
            analysis: Analysis results dictionary
            model_version: LLM model version used for analysis
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Remove cache_hit flag before storing (not part of original analysis)
            analysis_copy = analysis.copy()
            analysis_copy.pop('cache_hit', None)
            analysis_copy.pop('cache_retrieval_time_ms', None)
            analysis_copy.pop('original_processing_time_ms', None)

            analysis_json = json.dumps(analysis_copy)
            processing_time = analysis.get('processing_time_ms', 0)

            cursor.execute('''
                INSERT OR REPLACE INTO analysis_cache
                (message_id, analysis_json, model_version, processing_time_ms,
                 cached_date, last_accessed, access_count)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
            ''', (message_id, analysis_json, model_version, processing_time))

            conn.commit()
            conn.close()

            logger.debug(f"Cached analysis for {message_id}")

        except Exception as e:
            logger.error(f"Failed to cache analysis for {message_id}: {e}")

    def invalidate_entry(self, message_id: str):
        """
        Remove specific cache entry.

        Args:
            message_id: Unique identifier for email
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM analysis_cache WHERE message_id = ?', (message_id,))
            deleted = cursor.rowcount

            conn.commit()
            conn.close()

            if deleted > 0:
                logger.debug(f"Invalidated cache entry for {message_id}")

        except Exception as e:
            logger.error(f"Failed to invalidate cache entry {message_id}: {e}")

    def invalidate_by_model_version(self, old_model_version: str) -> int:
        """
        Invalidate all cache entries for a specific model version.

        Args:
            old_model_version: Model version to invalidate

        Returns:
            Number of entries deleted
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM analysis_cache WHERE model_version = ?
            ''', (old_model_version,))

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"Invalidated {deleted_count} cache entries for model {old_model_version}")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to invalidate cache by model version: {e}")
            return 0

    def clear_all(self) -> int:
        """
        Clear entire cache.

        Returns:
            Number of entries deleted
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM analysis_cache')
            count_before = cursor.fetchone()[0]

            cursor.execute('DELETE FROM analysis_cache')
            conn.commit()
            conn.close()

            logger.info(f"Cache cleared: {count_before} entries removed")

            return count_before

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Statistics dictionary with:
            - total_entries: Total number of cached analyses
            - total_size_mb: Total size of cache in MB
            - oldest_entry: Timestamp of oldest cache entry
            - newest_entry: Timestamp of newest cache entry
            - by_model: List of stats grouped by model version
            - hit_rate_estimate: Estimated cache hit rate (from access_count)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Overall stats
            cursor.execute('''
                SELECT
                    COUNT(*) as total_entries,
                    SUM(LENGTH(analysis_json)) as total_size_bytes,
                    MIN(cached_date) as oldest_entry,
                    MAX(cached_date) as newest_entry,
                    AVG(access_count) as avg_access_count
                FROM analysis_cache
            ''')

            row = cursor.fetchone()

            total_entries = row[0] or 0
            total_size_bytes = row[1] or 0
            oldest_entry = row[2]
            newest_entry = row[3]
            avg_access_count = row[4] or 0.0

            # Stats by model version
            cursor.execute('''
                SELECT
                    model_version,
                    COUNT(*) as entries,
                    MIN(cached_date) as oldest_entry,
                    MAX(cached_date) as newest_entry
                FROM analysis_cache
                GROUP BY model_version
            ''')

            by_model = []
            for row in cursor.fetchall():
                by_model.append({
                    'model_version': row[0],
                    'entries': row[1],
                    'oldest_entry': row[2],
                    'newest_entry': row[3]
                })

            conn.close()

            # Calculate estimated hit rate
            # If average access count > 0, some entries were accessed multiple times
            hit_rate_estimate = min(avg_access_count / (avg_access_count + 1) * 100, 100) if avg_access_count > 0 else 0

            return {
                'total_entries': total_entries,
                'total_size_mb': round(total_size_bytes / (1024 * 1024), 2),
                'oldest_entry': oldest_entry,
                'newest_entry': newest_entry,
                'by_model': by_model,
                'avg_access_count': round(avg_access_count, 2),
                'hit_rate_estimate_percent': round(hit_rate_estimate, 2)
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
        Evict least recently used (LRU) cache entries.

        Args:
            max_entries: Maximum number of entries to keep

        Returns:
            Number of entries evicted
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Count current entries
            cursor.execute('SELECT COUNT(*) FROM analysis_cache')
            current_count = cursor.fetchone()[0]

            if current_count <= max_entries:
                conn.close()
                return 0

            # Delete oldest accessed entries
            entries_to_delete = current_count - max_entries

            cursor.execute('''
                DELETE FROM analysis_cache
                WHERE message_id IN (
                    SELECT message_id
                    FROM analysis_cache
                    ORDER BY last_accessed ASC
                    LIMIT ?
                )
            ''', (entries_to_delete,))

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"LRU eviction: removed {deleted_count} entries (keeping {max_entries})")

            return deleted_count

        except Exception as e:
            logger.error(f"LRU eviction failed: {e}")
            return 0
