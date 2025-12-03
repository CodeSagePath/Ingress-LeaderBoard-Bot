"""
Production-specific configuration management and utilities.

This module provides production-ready configurations, validation,
and utilities for deploying the Ingress Prime leaderboard bot.
"""

import logging
import os
import ssl
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from cryptography.fernet import Fernet
import hashlib
import secrets


logger = logging.getLogger(__name__)


@dataclass
class SSLConfiguration:
    """SSL/TLS configuration for production deployments."""
    cert_path: Optional[str] = None
    key_path: Optional[str] = None
    ca_path: Optional[str] = None
    verify_mode: str = "required"
    protocol_version: int = ssl.PROTOCOL_TLS_SERVER
    ciphers: str = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
    require_client_cert: bool = False


@dataclass
class DatabaseConfiguration:
    """Production database configuration with security and performance optimizations."""
    max_connections: int = 50
    min_connections: int = 5
    connection_timeout: int = 60
    idle_timeout: int = 300
    max_lifetime: int = 3600
    health_check_period: int = 30
    ssl_mode: str = "require"
    statement_timeout: int = 30000
    application_name: str = "ingress_leaderbot"


@dataclass
class SecurityConfiguration:
    """Enhanced security configuration for production."""
    session_timeout: int = 3600
    max_login_attempts: int = 5
    lockout_duration: int = 900
    password_min_length: int = 12
    rate_limit_window: int = 60
    audit_logging: bool = True
    encryption_at_rest: bool = True


class ProductionValidator:
    """Production environment validation and security checks."""

    def __init__(self):
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def validate_production_setup(self, settings: Any) -> Dict[str, Any]:
        """
        Validate production environment setup.

        Args:
            settings: Application settings instance

        Returns:
            Dictionary containing validation results
        """
        self.warnings.clear()
        self.errors.clear()

        # Validate environment
        self._validate_environment(settings)

        # Validate security settings
        self._validate_security(settings)

        # Validate database configuration
        self._validate_database(settings)

        # Validate SSL configuration
        self._validate_ssl(settings)

        # Validate monitoring setup
        self._validate_monitoring(settings)

        # Validate backup configuration
        self._validate_backups(settings)

        return {
            'valid': len(self.errors) == 0,
            'warnings': self.warnings,
            'errors': self.errors,
            'critical_issues': len([e for e in self.errors if 'critical' in e.lower()])
        }

    def _validate_environment(self, settings: Any) -> None:
        """Validate environment settings."""
        if not settings.is_production():
            self.errors.append("Not running in production mode")

        if settings.is_debug():
            self.warnings.append("Debug mode is enabled in production")

        # Check for required environment variables
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'SECRET_KEY',
            'DB_PASSWORD'
        ]

        for var in required_vars:
            if not os.getenv(var):
                self.errors.append(f"Critical: Missing required environment variable: {var}")

    def _validate_security(self, settings: Any) -> None:
        """Validate security configuration."""
        if not hasattr(settings, 'security') or not settings.security:
            self.errors.append("Security configuration is missing")
            return

        security = settings.security

        if not security.secret_key:
            self.errors.append("Critical: SECRET_KEY is not configured")
        elif len(security.secret_key) < 32:
            self.warnings.append("SECRET_KEY should be at least 32 characters")

        if security.ssl_verify is False:
            self.warnings.append("SSL verification is disabled")

        if not hasattr(settings, 'performance') or not settings.performance:
            self.warnings.append("Performance configuration is missing")
            return

        performance = settings.performance

        if not performance.rate_limit_enabled:
            self.warnings.append("Rate limiting is disabled")

        if performance.rate_limit_requests_per_minute > 1000:
            self.warnings.append("Rate limit is very high, consider reducing")

    def _validate_database(self, settings: Any) -> None:
        """Validate database configuration."""
        if not hasattr(settings, 'database') or not settings.database:
            self.errors.append("Database configuration is missing")
            return

        database = settings.database

        if not database.url:
            self.errors.append("Critical: Database URL is not configured")
        elif database.url.startswith('sqlite:///'):
            self.warnings.append("SQLite should not be used in production")
        elif 'localhost' in database.url or '127.0.0.1' in database.url:
            self.warnings.append("Using localhost database in production")

        if database.pool_size < 10:
            self.warnings.append("Database pool size is low for production")

        if database.connection_timeout < 30:
            self.warnings.append("Database connection timeout is low")

    def _validate_ssl(self, settings: Any) -> None:
        """Validate SSL/TLS configuration."""
        if not hasattr(settings, 'security') or not settings.security:
            self.errors.append("Security configuration required for SSL validation")
            return

        security = settings.security

        if security.ssl_cert_path and security.ssl_key_path:
            # Validate SSL certificate files exist
            if not os.path.exists(security.ssl_cert_path):
                self.errors.append(f"SSL certificate file not found: {security.ssl_cert_path}")

            if not os.path.exists(security.ssl_key_path):
                self.errors.append(f"SSL key file not found: {security.ssl_key_path}")
        elif settings.is_production():
            self.warnings.append("SSL certificates not configured for production")

    def _validate_monitoring(self, settings: Any) -> None:
        """Validate monitoring configuration."""
        if not hasattr(settings, 'monitoring') or not settings.monitoring:
            self.warnings.append("Monitoring configuration is missing")
            return

        monitoring = settings.monitoring

        if not monitoring.enabled:
            self.warnings.append("Monitoring is disabled in production")

        if not monitoring.health_check_enabled:
            self.warnings.append("Health checks are disabled")

        if not monitoring.metrics_enabled:
            self.warnings.append("Metrics collection is disabled")

    def _validate_backups(self, settings: Any) -> None:
        """Validate backup configuration."""
        if not hasattr(settings, 'backup') or not settings.backup:
            self.warnings.append("Backup configuration is missing")
            return

        backup = settings.backup

        if not backup.enabled:
            self.errors.append("Critical: Backups are disabled in production")

        if backup.enabled and not backup.s3_bucket:
            self.warnings.append("No S3 bucket configured for backups")


class ProductionSecurity:
    """Production security utilities and configurations."""

    @staticmethod
    def generate_secret_key(length: int = 64) -> str:
        """
        Generate a cryptographically secure secret key.

        Args:
            length: Length of the secret key

        Returns:
            Hexadecimal secret key
        """
        return secrets.token_hex(length)

    @staticmethod
    def generate_encryption_key() -> str:
        """
        Generate a Fernet encryption key.

        Returns:
            Base64-encoded encryption key
        """
        return Fernet.generate_key().decode()

    @staticmethod
    def hash_api_key(api_key: str, salt: Optional[str] = None) -> str:
        """
        Hash an API key with salt.

        Args:
            api_key: API key to hash
            salt: Optional salt, generates if None

        Returns:
            Hashed API key with salt
        """
        if salt is None:
            salt = secrets.token_hex(16)

        combined = f"{salt}:{api_key}"
        return hashlib.sha256(combined.encode()).hexdigest()

    @staticmethod
    def validate_ssl_certificates(cert_path: str, key_path: str) -> Dict[str, Any]:
        """
        Validate SSL certificate and key files.

        Args:
            cert_path: Path to SSL certificate
            key_path: Path to SSL private key

        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': False,
            'cert_exists': os.path.exists(cert_path),
            'key_exists': os.path.exists(key_path),
            'errors': []
        }

        if not result['cert_exists']:
            result['errors'].append(f"Certificate file not found: {cert_path}")

        if not result['key_exists']:
            result['errors'].append(f"Key file not found: {key_path}")

        if result['cert_exists'] and result['key_exists']:
            try:
                # Load and validate certificate
                context = ssl.create_default_context()
                context.load_cert_chain(cert_path, key_path)
                result['valid'] = True
            except Exception as e:
                result['errors'].append(f"SSL certificate validation failed: {e}")

        return result

    @staticmethod
    def get_ssl_context(ssl_config: SSLConfiguration) -> ssl.SSLContext:
        """
        Create SSL context from configuration.

        Args:
            ssl_config: SSL configuration

        Returns:
            Configured SSL context
        """
        context = ssl.SSLContext(ssl_config.protocol_version)

        # Configure ciphers
        context.set_ciphers(ssl_config.ciphers)

        # Load certificates if provided
        if ssl_config.cert_path and ssl_config.key_path:
            context.load_cert_chain(ssl_config.cert_path, ssl_config.key_path)

        # Configure verification mode
        verify_modes = {
            'none': ssl.CERT_NONE,
            'optional': ssl.CERT_OPTIONAL,
            'required': ssl.CERT_REQUIRED
        }
        context.verify_mode = verify_modes.get(ssl_config.verify_mode, ssl.CERT_REQUIRED)

        # Load CA certificate if provided
        if ssl_config.ca_path:
            context.load_verify_locations(ssl_config.ca_path)

        # Configure client certificate requirement
        if ssl_config.require_client_cert:
            context.verify_mode = ssl.CERT_REQUIRED

        return context


class ProductionOptimizer:
    """Production performance optimization utilities."""

    @staticmethod
    def optimize_database_config(database_config: DatabaseConfiguration) -> Dict[str, Any]:
        """
        Generate optimized database configuration.

        Args:
            database_config: Base database configuration

        Returns:
            Optimized database configuration
        """
        return {
            'max_connections': min(database_config.max_connections, 100),
            'min_connections': max(database_config.min_connections, 5),
            'connection_timeout': database_config.connection_timeout,
            'idle_timeout': database_config.idle_timeout,
            'max_lifetime': database_config.max_lifetime,
            'health_check_period': database_config.health_check_period,
            'ssl_mode': database_config.ssl_mode,
            'statement_timeout': database_config.statement_timeout,
            'application_name': database_config.application_name,
            'pool_pre_ping': True,
            'pool_recycle': database_config.max_lifetime
        }

    @staticmethod
    def get_recommended_config() -> Dict[str, Any]:
        """
        Get recommended production configuration.

        Returns:
            Dictionary with recommended settings
        """
        return {
            'database': {
                'pool_size': 20,
                'max_overflow': 40,
                'connection_timeout': 60,
                'pool_recycle': 7200,
                'ssl_mode': 'require'
            },
            'telegram': {
                'request_timeout': 60,
                'connection_pool_size': 16,
                'read_timeout': 60,
                'write_timeout': 60,
                'connect_timeout': 30
            },
            'performance': {
                'cache_enabled': True,
                'cache_ttl': 600,
                'max_workers': 8,
                'worker_timeout': 300,
                'rate_limit_enabled': True,
                'rate_limit_requests_per_minute': 100,
                'rate_limit_burst': 200
            },
            'logging': {
                'level': 'INFO',
                'max_file_size_mb': 100,
                'backup_count': 30
            },
            'monitoring': {
                'enabled': True,
                'health_check_enabled': True,
                'metrics_enabled': True,
                'health_check_interval': 30,
                'health_check_timeout': 10
            },
            'backup': {
                'enabled': True,
                'schedule': '0 2 * * *',
                'retention_days': 30
            }
        }


def create_production_checklist() -> List[Dict[str, Any]]:
    """
    Create a production deployment checklist.

    Returns:
        List of checklist items
    """
    return [
        {
            'category': 'Security',
            'items': [
                'Generate and configure SECRET_KEY',
                'Generate and configure ENCRYPTION_KEY',
                'Set up SSL certificates',
                'Configure allowed chat IDs',
                'Enable rate limiting',
                'Set up monitoring and alerts'
            ]
        },
        {
            'category': 'Database',
            'items': [
                'Configure production PostgreSQL',
                'Set up connection pooling',
                'Enable SSL for database connections',
                'Configure backup strategy',
                'Set up database monitoring'
            ]
        },
        {
            'category': 'Performance',
            'items': [
                'Configure caching',
                'Set up load balancing',
                'Optimize database connections',
                'Configure worker processes',
                'Set up monitoring'
            ]
        },
        {
            'category': 'Deployment',
            'items': [
                'Set up CI/CD pipeline',
                'Configure environment variables',
                'Set up health checks',
                'Configure log rotation',
                'Set up backup automation'
            ]
        },
        {
            'category': 'Monitoring',
            'items': [
                'Set up application metrics',
                'Configure error tracking',
                'Set up uptime monitoring',
                'Configure alert notifications',
                'Set up log aggregation'
            ]
        }
    ]


def validate_production_ready() -> Dict[str, Any]:
    """
    Quick check if production environment is properly configured.

    Returns:
        Dictionary with validation results
    """
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'SECRET_KEY',
        'DB_PASSWORD',
        'DB_HOST'
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    return {
        'ready': len(missing_vars) == 0,
        'missing_variables': missing_vars,
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'production_mode': os.getenv('PRODUCTION', 'false').lower() in ('true', '1'),
        'debug_mode': os.getenv('DEBUG', 'false').lower() in ('true', '1')
    }