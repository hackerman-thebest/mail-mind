"""
Database Schema Definitions for MailMind

This module defines the complete production SQLite database schema for MailMind,
including all tables, indexes, constraints, and performance optimizations.

Schema Version: 1.0
Tables:
- schema_version: Migration tracking
- email_analysis: Email AI analysis results with full metadata
- performance_metrics: System performance tracking and trends
- user_preferences: Application settings and user choices
- user_corrections: User feedback for ML improvement

Features:
- WAL (Write-Ahead Logging) mode for better concurrency
- CHECK constraints for data validation
- Foreign key constraints for referential integrity
- Optimized indexes for common query patterns
- Prepared for optional SQLCipher encryption

Integration:
- Extends Story 1.3 (EmailAnalysisEngine) schema
- Extends Story 1.6 (CacheManager) patterns
- Consolidates all database operations from Epic 1
"""

# Enable Write-Ahead Logging mode for better concurrency
PRAGMA_STATEMENTS = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;
"""

# Schema version tracking table
SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
"""

# Email analysis results table (extends Story 1.3 schema)
EMAIL_ANALYSIS_TABLE = """
CREATE TABLE IF NOT EXISTS email_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,
    subject TEXT,
    sender TEXT,
    received_date DATETIME,

    -- Analysis results (JSON string)
    analysis_json TEXT NOT NULL,

    -- Denormalized fields for fast queries
    priority TEXT CHECK(priority IN ('High', 'Medium', 'Low')),
    suggested_folder TEXT,
    confidence_score REAL CHECK(confidence_score >= 0 AND confidence_score <= 1.0),
    sentiment TEXT CHECK(sentiment IN ('positive', 'neutral', 'negative', 'urgent')),

    -- Performance tracking
    processing_time_ms INTEGER,
    model_version TEXT NOT NULL,
    hardware_profile TEXT,

    -- Metadata
    processed_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_feedback TEXT  -- For future learning
);
"""

# Performance metrics table (extends Story 1.6 schema)
PERFORMANCE_METRICS_TABLE = """
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,  -- 'email_analysis', 'batch_processing', 'outlook_fetch', etc.
    hardware_config TEXT NOT NULL,
    model_version TEXT,
    tokens_per_second REAL,
    memory_usage_mb INTEGER,
    processing_time_ms INTEGER,
    database_size_mb INTEGER,  -- For size monitoring (AC8)
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

# User preferences table for all settings
USER_PREFERENCES_TABLE = """
CREATE TABLE IF NOT EXISTS user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    default_value TEXT,
    value_type TEXT CHECK(value_type IN ('string', 'int', 'float', 'bool', 'json')),
    category TEXT,  -- 'general', 'ai_model', 'performance', 'privacy', 'advanced'
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

# User corrections table for learning system (Story 1.4 integration)
USER_CORRECTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS user_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,
    correction_type TEXT NOT NULL,  -- 'priority', 'folder', 'sentiment', etc.
    original_suggestion TEXT,
    user_choice TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (message_id) REFERENCES email_analysis(message_id)
);
"""

# Indexes for email_analysis table (optimized for common queries)
EMAIL_ANALYSIS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_email_message_id ON email_analysis(message_id);
CREATE INDEX IF NOT EXISTS idx_email_priority ON email_analysis(priority);
CREATE INDEX IF NOT EXISTS idx_email_received_date ON email_analysis(received_date);
CREATE INDEX IF NOT EXISTS idx_email_processed_date ON email_analysis(processed_date);
"""

# Indexes for performance_metrics table
PERFORMANCE_METRICS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_perf_operation ON performance_metrics(operation);
CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON performance_metrics(timestamp);
"""

# Indexes for user_preferences table
USER_PREFERENCES_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_pref_category ON user_preferences(category);
"""

# Indexes for user_corrections table
USER_CORRECTIONS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_corr_message_id ON user_corrections(message_id);
CREATE INDEX IF NOT EXISTS idx_corr_correction_type ON user_corrections(correction_type);
CREATE INDEX IF NOT EXISTS idx_corr_timestamp ON user_corrections(timestamp);
"""

# Complete schema initialization sequence
FULL_SCHEMA = [
    PRAGMA_STATEMENTS,
    SCHEMA_VERSION_TABLE,
    EMAIL_ANALYSIS_TABLE,
    PERFORMANCE_METRICS_TABLE,
    USER_PREFERENCES_TABLE,
    USER_CORRECTIONS_TABLE,
    EMAIL_ANALYSIS_INDEXES,
    PERFORMANCE_METRICS_INDEXES,
    USER_PREFERENCES_INDEXES,
    USER_CORRECTIONS_INDEXES,
]

# Initial schema version entry
INITIAL_SCHEMA_VERSION = """
INSERT OR IGNORE INTO schema_version (version, description)
VALUES (1, 'Initial schema: 5 core tables with indexes and constraints');
"""

# Default user preferences to initialize on first run
DEFAULT_PREFERENCES = [
    ("theme", "light", "light", "string", "general"),
    ("language", "en", "en", "string", "general"),
    ("email_batch_size", "50", "50", "int", "performance"),
    ("enable_encryption", "false", "false", "bool", "privacy"),
    ("auto_backup_enabled", "true", "true", "bool", "privacy"),
    ("backup_retention_days", "7", "7", "int", "privacy"),
    ("database_size_warning_mb", "1024", "1024", "int", "advanced"),
    ("query_timeout_ms", "100", "100", "int", "advanced"),
    ("enable_query_logging", "false", "false", "bool", "advanced"),
]


def get_schema_statements():
    """
    Get all SQL statements needed to initialize the database schema.

    Returns:
        list: List of SQL statement strings to execute in order
    """
    return FULL_SCHEMA


def get_initial_data_statements():
    """
    Get SQL statements for initial data (schema version, default preferences).

    Returns:
        list: List of SQL statement strings for initial data
    """
    statements = [INITIAL_SCHEMA_VERSION]

    # Add default user preferences
    for key, value, default, value_type, category in DEFAULT_PREFERENCES:
        statement = f"""
        INSERT OR IGNORE INTO user_preferences (key, value, default_value, value_type, category)
        VALUES ('{key}', '{value}', '{default}', '{value_type}', '{category}');
        """
        statements.append(statement)

    return statements


def validate_schema_version(conn):
    """
    Validate that the schema version table exists and has the expected structure.

    Args:
        conn: SQLite connection object

    Returns:
        bool: True if schema version table is valid, False otherwise
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT version, applied_date, description FROM schema_version WHERE version = 1")
        result = cursor.fetchone()
        return result is not None
    except Exception:
        return False


def get_current_schema_version(conn):
    """
    Get the current schema version from the database.

    Args:
        conn: SQLite connection object

    Returns:
        int: Current schema version, or 0 if not found
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0
    except Exception:
        return 0
