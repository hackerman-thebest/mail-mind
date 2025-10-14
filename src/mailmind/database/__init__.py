"""
MailMind Database Package

This package provides centralized database management for MailMind, consolidating
all SQLite operations for email analysis, performance metrics, user preferences,
and system configuration.

Main Components:
- DatabaseManager: Single entry point for all database operations
- schema: SQL schema definitions for all tables
- migrations: Database migration framework
- backup_manager: Backup and restore functionality
- encryption: Optional SQLCipher encryption support

Integration:
- Story 1.3 (EmailAnalysisEngine): Refactored to use DatabaseManager
- Story 1.6 (CacheManager): Delegates to DatabaseManager
- Story 2.1 (OutlookConnector): Email metadata storage via DatabaseManager
- Story 2.4 (Settings System): User preferences via DatabaseManager

Usage:
    from mailmind.database import DatabaseManager

    # Context manager pattern
    with DatabaseManager() as db:
        db.insert_email_analysis(message_id, analysis_data)
        metrics = db.get_performance_metrics(days=7)

    # Singleton pattern
    db = DatabaseManager.get_instance()
    db.set_preference("theme", "dark")
"""

__version__ = "1.0.0"

# Core exports
from .database_manager import (
    DatabaseManager,
    DatabaseError,
    ConnectionError,
    QueryError,
    DataNotFoundError,
)
from .schema import (
    get_schema_statements,
    get_initial_data_statements,
    get_current_schema_version,
)

__all__ = [
    "DatabaseManager",
    "DatabaseError",
    "ConnectionError",
    "QueryError",
    "DataNotFoundError",
    "get_schema_statements",
    "get_initial_data_statements",
    "get_current_schema_version",
]
