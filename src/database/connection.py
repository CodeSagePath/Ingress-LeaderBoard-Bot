"""
Database connection manager for Ingress Prime leaderboard bot.

This module handles database connections, session management,
and connection pooling for PostgreSQL.
"""

import os
import logging
from typing import Optional
from contextlib import contextmanager

import psycopg2
from psycopg2.pool import SimpleConnectionPool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connections and sessions."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            database_url: Full database connection URL or None to build from environment
        """
        if not database_url:
            database_url = self._build_database_url()

        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self.connection_pool = None

    def _build_database_url(self) -> str:
        """Build database URL from environment variables."""
        try:
            # Get configuration from environment
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = os.getenv('DB_PORT', '5432')
            db_name = os.getenv('DB_NAME', 'ingress_leaderboard')
            db_user = os.getenv('DB_USER', 'postgres')
            db_password = os.getenv('DB_PASSWORD')

            if not db_password:
                raise ValueError("DB_PASSWORD environment variable is required")

            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

        except Exception as e:
            logger.error(f"Error building database URL: {e}")
            raise

    def initialize(self, pool_size: int = 5, max_overflow: int = 10) -> None:
        """
        Initialize database engine and connection pool.

        Args:
            pool_size: Number of connections to keep in pool
            max_overflow: Maximum number of connections beyond pool size
        """
        try:
            # Create SQLAlchemy engine with connection pooling
            self.engine = create_engine(
                self.database_url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,  # Test connections before use
                pool_recycle=3600,  # Recycle connections after 1 hour
                echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
            )

            # Create session factory
            self.session_factory = sessionmaker(bind=self.engine)

            # Create raw connection pool for direct SQL when needed
            self.connection_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=pool_size,
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'ingress_leaderboard'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', '5432')
            )

            logger.info("Database connection initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise

    def create_tables(self) -> None:
        """Create all database tables from models."""
        try:
            if not self.engine:
                raise RuntimeError("Database not initialized. Call initialize() first.")

            # Import all models to ensure they're registered
            from ..database import models  # noqa

            # Create all tables
            models.Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")

        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {e}")
            raise

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            SQLAlchemy session instance
        """
        if not self.session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        return self.session_factory()

    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope for database operations.

        Yields:
            SQLAlchemy session that's automatically committed or rolled back
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction rolled back: {e}")
            raise
        finally:
            session.close()

    def execute_raw_query(self, query: str, params: Optional[tuple] = None) -> list:
        """
        Execute raw SQL query using psycopg2 connection pool.

        Args:
            query: SQL query string
            params: Optional tuple of query parameters

        Returns:
            List of query result rows
        """
        if not self.connection_pool:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        conn = None
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            results = cursor.fetchall()
            return results

        except Exception as e:
            logger.error(f"Error executing raw query: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def test_connection(self) -> bool:
        """
        Test database connection health.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            with self.session_scope() as session:
                session.execute("SELECT 1")
                logger.debug("Database connection test successful")
                return True

        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def get_connection_stats(self) -> dict:
        """
        Get connection pool statistics.

        Returns:
            Dictionary with pool statistics
        """
        if not self.connection_pool:
            return {'error': 'Connection pool not initialized'}

        try:
            pool = self.connection_pool
            return {
                'pool_size': pool.minconn,
                'max_connections': pool.maxconn,
                'connections_in_use': pool._used,
                'available_connections': pool._pool.qsize() if hasattr(pool._pool, 'qsize') else 'unknown'
            }
        except Exception as e:
            logger.error(f"Error getting connection stats: {e}")
            return {'error': str(e)}

    def close(self) -> None:
        """Close all database connections and clean up resources."""
        try:
            if self.connection_pool:
                self.connection_pool.closeall()
                logger.info("Connection pool closed")

            if self.engine:
                self.engine.dispose()
                logger.info("SQLAlchemy engine disposed")

            self.connection_pool = None
            self.engine = None
            self.session_factory = None

        except Exception as e:
            logger.error(f"Error closing database connections: {e}")


# Global database connection instance
_db_connection = None


def get_database_connection(database_url: Optional[str] = None) -> DatabaseConnection:
    """
    Get or create global database connection instance.

    Args:
        database_url: Database URL to use

    Returns:
        DatabaseConnection instance
    """
    global _db_connection

    if _db_connection is None:
        _db_connection = DatabaseConnection(database_url)
        _db_connection.initialize()

    return _db_connection


def initialize_database(database_url: Optional[str] = None,
                     create_tables: bool = True) -> DatabaseConnection:
    """
    Initialize database connection and optionally create tables.

    Args:
        database_url: Database URL to use
        create_tables: Whether to create database tables

    Returns:
        Initialized DatabaseConnection instance
    """
    db = get_database_connection(database_url)

    if create_tables:
        db.create_tables()

    return db


def get_db_session() -> Session:
    """
    Get a database session from the global connection.

    Returns:
        SQLAlchemy session
    """
    db = get_database_connection()
    return db.get_session()


def with_db_session(func):
    """
    Decorator to provide database session to functions.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with database session
    """
    def wrapper(*args, **kwargs):
        db = get_database_connection()
        with db.session_scope() as session:
            return func(session, *args, **kwargs)

    return wrapper


# Database health check functions
def check_database_health() -> dict:
    """
    Check overall database health and return status.

    Returns:
        Dictionary with health status information
    """
    try:
        db = get_database_connection()

        # Test basic connection
        is_healthy = db.test_connection()

        # Get connection stats
        conn_stats = db.get_connection_stats()

        # Test table access
        tables_status = check_tables_access(db)

        return {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'connection_test': is_healthy,
            'connection_stats': conn_stats,
            'tables_status': tables_status,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


def check_tables_access(db: DatabaseConnection) -> dict:
    """
    Check if required database tables exist and are accessible.

    Args:
        db: DatabaseConnection instance

    Returns:
        Dictionary with table access status
    """
    tables_to_check = [
        'users', 'agents', 'stats_submissions',
        'agent_stats', 'leaderboard_cache'
    ]

    status = {}

    try:
        with db.session_scope() as session:
            for table_name in tables_to_check:
                try:
                    # Simple query to test table access
                    session.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                    status[table_name] = 'accessible'
                except SQLAlchemyError as e:
                    if 'does not exist' in str(e).lower():
                        status[table_name] = 'missing'
                    else:
                        status[table_name] = f'error: {str(e)}'
                except Exception as e:
                    status[table_name] = f'exception: {str(e)}'

    except Exception as e:
        return {'overall_error': str(e)}

    return status


# Migration and version tracking
def get_database_version(session: Session) -> Optional[str]:
    """
    Get current database version.

    Args:
        session: SQLAlchemy session

    Returns:
        Version string or None if not found
    """
    try:
        # Try to query version from migrations table
        result = session.execute("SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1")
        return result.scalar()
    except Exception:
        # Table doesn't exist, assume fresh database
        return None


def update_database_version(session: Session, version: str) -> None:
    """
    Update database version in migrations table.

    Args:
        session: SQLAlchemy session
        version: New version string
    """
    try:
        # Create migrations table if it doesn't exist
        session.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(20) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert or update version
        session.execute(
            "INSERT INTO schema_migrations (version) VALUES (:version) "
            "ON CONFLICT (version) DO UPDATE SET applied_at = CURRENT_TIMESTAMP",
            {'version': version}
        )

    except Exception as e:
        logger.error(f"Error updating database version: {e}")
        raise