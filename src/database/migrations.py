"""
Database migration utilities for the Ingress leaderboard bot.

This module provides helper functions for managing database migrations
using Alembic, including migration status checking, health monitoring,
and integration with the application lifecycle.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .connection import get_database_connection, get_db_session

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations using Alembic."""

    def __init__(self, alembic_config_path: Optional[str] = None):
        """
        Initialize migration manager.

        Args:
            alembic_config_path: Path to alembic.ini file
        """
        if alembic_config_path is None:
            # Default to alembic.ini in project root
            project_root = Path(__file__).parent.parent.parent
            alembic_config_path = str(project_root / "alembic.ini")

        self.config_path = alembic_config_path
        self.alembic_cfg = Config(alembic_config_path)
        self.script_dir = ScriptDirectory.from_config(self.alembic_cfg)

    def get_current_revision(self) -> Optional[str]:
        """
        Get the current database migration revision.

        Returns:
            Current revision ID or None if no migrations applied
        """
        try:
            with get_db_session() as session:
                # Check if alembic_version table exists
                result = session.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'alembic_version'
                    )
                """))
                table_exists = result.scalar()

                if not table_exists:
                    return None

                # Get current revision
                result = session.execute(text("SELECT version_num FROM alembic_version"))
                revision = result.scalar()
                return revision

        except SQLAlchemyError as e:
            logger.error(f"Error getting current revision: {e}")
            return None

    def get_head_revision(self) -> Optional[str]:
        """
        Get the head revision from migration files.

        Returns:
            Head revision ID or None if no migrations exist
        """
        try:
            return self.script_dir.get_current_head()
        except Exception as e:
            logger.error(f"Error getting head revision: {e}")
            return None

    def get_pending_migrations(self) -> List[str]:
        """
        Get list of pending migrations.

        Returns:
            List of pending revision IDs
        """
        try:
            current = self.get_current_revision()
            head = self.get_head_revision()

            if not head:
                return []

            if current == head:
                return []

            # Get all pending migrations
            pending = []
            for revision in self.script_dir.walk_revisions("head", current):
                pending.append(revision.revision)

            return pending

        except Exception as e:
            logger.error(f"Error getting pending migrations: {e}")
            return []

    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get comprehensive migration status.

        Returns:
            Dictionary with migration status information
        """
        current = self.get_current_revision()
        head = self.get_head_revision()
        pending = self.get_pending_migrations()

        status = {
            "current_revision": current,
            "head_revision": head,
            "is_up_to_date": current == head,
            "pending_migrations": len(pending),
            "pending_migration_ids": pending,
            "needs_migration": len(pending) > 0,
            "has_migrations": head is not None,
        }

        return status

    def check_migration_health(self) -> Dict[str, Any]:
        """
        Check migration system health.

        Returns:
            Dictionary with health status
        """
        health = {"status": "healthy", "issues": [], "recommendations": []}

        try:
            # Check if alembic.ini exists
            if not Path(self.config_path).exists():
                health["status"] = "unhealthy"
                health["issues"].append("alembic.ini file not found")
                return health

            # Check migration directory structure
            versions_dir = Path(self.config_path).parent / "alembic" / "versions"
            if not versions_dir.exists():
                health["status"] = "unhealthy"
                health["issues"].append("Migration versions directory not found")
                return health

            # Check database connectivity
            db = get_database_connection()
            if not db.test_connection():
                health["status"] = "unhealthy"
                health["issues"].append("Database connection failed")
                return health

            # Check migration status
            migration_status = self.get_migration_status()
            if migration_status["needs_migration"]:
                health["status"] = "warning"
                health["recommendations"].append(f"{len(pending)} migrations pending")
                health["pending_count"] = len(pending)

            # Check for missing alembic_version table
            current = self.get_current_revision()
            if migration_status["has_migrations"] and current is None:
                health["status"] = "warning"
                health["recommendations"].append("Database not initialized with migrations")

        except Exception as e:
            health["status"] = "error"
            health["issues"].append(f"Migration health check failed: {e}")

        return health

    def create_migration(self, message: str, autogenerate: bool = True) -> Optional[str]:
        """
        Create a new migration file.

        Args:
            message: Migration message/description
            autogenerate: Whether to autogenerate migration from models

        Returns:
            Path to created migration file or None if failed
        """
        try:
            logger.info(f"Creating migration: {message}")

            if autogenerate:
                command.revision(self.alembic_cfg, message=message, autogenerate=True)
            else:
                command.revision(self.alembic_cfg, message=message, autogenerate=False)

            logger.info("Migration created successfully")
            return "Migration created successfully"

        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            return None

    def run_migrations(self, revision: str = "head") -> bool:
        """
        Run database migrations.

        Args:
            revision: Target revision (default: head)

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Running migrations to {revision}")

            # Check current status first
            status = self.get_migration_status()
            if status["is_up_to_date"]:
                logger.info("Database is already up to date")
                return True

            # Run upgrade
            command.upgrade(self.alembic_cfg, revision)

            # Verify migration completed
            new_status = self.get_migration_status()
            if new_status["is_up_to_date"]:
                logger.info("Migrations completed successfully")
                return True
            else:
                logger.error("Migrations did not complete successfully")
                return False

        except Exception as e:
            logger.error(f"Failed to run migrations: {e}")
            return False

    def rollback_migration(self, revision: str = "-1") -> bool:
        """
        Rollback database migrations.

        Args:
            revision: Target revision (default: one revision back)

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Rolling back migrations to {revision}")

            command.downgrade(self.alembic_cfg, revision)

            logger.info("Migration rollback completed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback migrations: {e}")
            return False

    def get_migration_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get migration history.

        Args:
            limit: Maximum number of migrations to return

        Returns:
            List of migration information dictionaries
        """
        try:
            history = []

            for revision in self.script_dir.walk_revisions("head", "base"):
                if len(history) >= limit:
                    break

                rev_doc = revision.doc
                history.append({
                    "revision": revision.revision,
                    "down_revision": revision.down_revision,
                    "branch_labels": list(revision.branch_labels) if revision.branch_labels else [],
                    "depends_on": list(revision.depends_on) if revision.depends_on else [],
                    "doc": rev_doc or "No description",
                })

            return history

        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []


# Global migration manager instance
_migration_manager = None


def get_migration_manager() -> MigrationManager:
    """
    Get or create the global migration manager instance.

    Returns:
        MigrationManager instance
    """
    global _migration_manager

    if _migration_manager is None:
        _migration_manager = MigrationManager()

    return _migration_manager


def check_and_run_migrations(auto_run: bool = False) -> Dict[str, Any]:
    """
    Check for pending migrations and optionally run them.

    Args:
        auto_run: Whether to automatically run pending migrations

    Returns:
        Dictionary with migration status and results
    """
    manager = get_migration_manager()

    try:
        # Check migration health first
        health = manager.check_migration_health()
        if health["status"] in ["unhealthy", "error"]:
            return {
                "status": "failed",
                "health": health,
                "error": "Migration system unhealthy, cannot proceed"
            }

        # Get current migration status
        status = manager.get_migration_status()

        result = {
            "status": "success",
            "migration_status": status,
            "health": health
        }

        # Run migrations if needed and auto_run is enabled
        if status["needs_migration"]:
            if auto_run:
                logger.info(f"Running {status['pending_migrations']} pending migrations")
                success = manager.run_migrations()

                if success:
                    result["auto_ran"] = True
                    result["ran_count"] = status["pending_migrations"]
                    logger.info("Auto-migration completed successfully")
                else:
                    result["status"] = "failed"
                    result["error"] = "Auto-migration failed"
                    logger.error("Auto-migration failed")
            else:
                result["auto_ran"] = False
                result["pending_count"] = status["pending_migrations"]
                logger.info(f"{status['pending_migrations']} migrations pending (auto_run=False)")

        return result

    except Exception as e:
        logger.error(f"Migration check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def initialize_database_with_migrations() -> bool:
    """
    Initialize database with migrations for the first time.

    Returns:
        True if successful, False otherwise
    """
    try:
        manager = get_migration_manager()

        # Check if database is already initialized
        current = manager.get_current_revision()
        if current is not None:
            logger.info("Database already initialized with migrations")
            return True

        # Run initial migration
        success = manager.run_migrations("head")

        if success:
            logger.info("Database initialized successfully with migrations")
        else:
            logger.error("Failed to initialize database with migrations")

        return success

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


# CLI helper functions
def run_migration_cli():
    """
    Run migration CLI commands from the command line.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Database migration CLI")
    parser.add_argument("action", choices=["status", "upgrade", "downgrade", "create"],
                       help="Migration action")
    parser.add_argument("--message", "-m", help="Migration message (for create)")
    parser.add_argument("--revision", "-r", default="head", help="Target revision")
    parser.add_argument("--autogenerate", action="store_true", help="Autogenerate migration")

    args = parser.parse_args()

    manager = get_migration_manager()

    if args.action == "status":
        status = manager.get_migration_status()
        print("Migration Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")

    elif args.action == "upgrade":
        success = manager.run_migrations(args.revision)
        print(f"Upgrade {'succeeded' if success else 'failed'}")

    elif args.action == "downgrade":
        success = manager.rollback_migration(args.revision)
        print(f"Downgrade {'succeeded' if success else 'failed'}")

    elif args.action == "create":
        if not args.message:
            print("Error: --message required for create action")
            sys.exit(1)

        result = manager.create_migration(args.message, args.autogenerate)
        print(f"Migration creation {'succeeded' if result else 'failed'}")


if __name__ == "__main__":
    run_migration_cli()