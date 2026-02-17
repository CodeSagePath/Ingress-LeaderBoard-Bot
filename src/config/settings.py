"""
Settings and configuration management for Ingress Prime leaderboard bot.

This module handles all application settings, environment variables,
and configuration validation.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass
class BotSettings:
    """Bot-specific settings."""
    token: str
    debug: bool = False
    webhook_url: Optional[str] = None
    webhook_port: int = 8443
    allowed_chat_ids: Optional[List[int]] = None
    rate_limit_per_minute: int = 5
    rate_limit_per_hour: int = 60


@dataclass
class DatabaseSettings:
    """Database-specific settings."""
    url: str
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    connection_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class LeaderboardSettings:
    """Leaderboard-specific settings."""
    cache_timeout_seconds: int = 300  # 5 minutes
    max_entries_per_category: int = 100
    default_leaderboard_limit: int = 20
    min_progress_days: int = 7
    max_progress_days: int = 90
    enable_monthly_leaderboards: bool = True
    enable_weekly_leaderboards: bool = True
    enable_daily_leaderboards: bool = True


@dataclass
class LoggingSettings:
    """Logging configuration settings."""
    level: str = "INFO"
    log_file: str = "bot.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    basic_mode: bool = False  # Simplified logging mode for easy setup


@dataclass
class TelegramSettings:
    """Telegram API specific settings."""
    api_url: str = "https://api.telegram.org"
    request_timeout: int = 30
    connection_pool_size: int = 8
    read_timeout: int = 30
    write_timeout: int = 30
    connect_timeout: int = 10


@dataclass
class MonitoringSettings:
    """Monitoring and health check settings."""
    enabled: bool = False
    health_check_enabled: bool = False
    metrics_enabled: bool = False
    metrics_port: int = 9090
    health_check_interval: int = 30
    health_check_timeout: int = 10
    health_check_failure_threshold: int = 3


@dataclass
class SecuritySettings:
    """Security and encryption settings."""
    cors_enabled: bool = False
    ssl_verify: bool = True
    secret_key: Optional[str] = None
    encryption_key: Optional[str] = None
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    ssl_ca_path: Optional[str] = None


@dataclass
class PerformanceSettings:
    """Performance and caching settings."""
    cache_enabled: bool = False
    cache_ttl: int = 300
    max_workers: int = 4
    worker_timeout: int = 120
    rate_limit_enabled: bool = False
    rate_limit_requests_per_minute: int = 100
    rate_limit_burst: int = 200


@dataclass
class BackupSettings:
    """Backup and recovery settings."""
    enabled: bool = False
    schedule: str = "0 2 * * *"  # Daily at 2 AM
    retention_days: int = 30
    s3_bucket: Optional[str] = None
    s3_region: Optional[str] = None


@dataclass
class AlertSettings:
    """Alert and notification settings."""
    enabled: bool = False
    webhook_url: Optional[str] = None
    email_enabled: bool = False
    email_smtp_host: Optional[str] = None
    email_smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_to: Optional[str] = None


@dataclass
class EnvironmentSettings:
    """Environment-specific settings."""
    name: str = "development"
    production: bool = False
    debug: bool = False


class Settings:
    """Main application settings manager."""

    def __init__(self, env_file: Optional[str] = None, environment: Optional[str] = None):
        """
        Initialize settings from environment variables.

        Args:
            env_file: Optional path to .env file
            environment: Optional environment name (development, staging, production)
        """
        self.environment = environment or os.getenv('ENVIRONMENT', 'development').lower()
        self._load_environment(env_file)
        self._initialize_settings()
        self._validate_settings()

    def _load_environment(self, env_file: Optional[str]) -> None:
        """Load environment variables from .env file if provided."""
        env_files = []

        # Determine which environment files to load
        if env_file:
            env_files.append(env_file)
        else:
            # Load base .env file first (if exists)
            if os.path.exists('.env'):
                env_files.append('.env')

            # Then load environment-specific file
            env_specific_file = f'.env.{self.environment}'
            if os.path.exists(env_specific_file):
                env_files.append(env_specific_file)

        # Load each environment file in order
        for env_file_path in env_files:
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file_path)
                logger.info(f"Loaded environment variables from {env_file_path}")
            except ImportError:
                logger.warning("python-dotenv not installed, skipping .env file loading")
                break
            except Exception as e:
                logger.error(f"Error loading {env_file_path}: {e}")

    def _initialize_settings(self) -> None:
        """Initialize all settings categories."""
        self.bot = BotSettings(
            token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            debug=self._get_bool('BOT_DEBUG', False),
            webhook_url=os.getenv('TELEGRAM_WEBHOOK_URL'),
            webhook_port=self._get_int('TELEGRAM_WEBHOOK_PORT', 8443),
            allowed_chat_ids=self._get_int_list('TELEGRAM_ALLOWED_CHAT_IDS'),
            rate_limit_per_minute=self._get_int('BOT_RATE_LIMIT_PER_MINUTE', 5),
            rate_limit_per_hour=self._get_int('BOT_RATE_LIMIT_PER_HOUR', 60)
        )

        self.database = DatabaseSettings(
            url=self._build_database_url(),
            echo=self._get_bool('DB_ECHO', False),
            pool_size=self._get_int('DB_POOL_SIZE', 5),
            max_overflow=self._get_int('DB_MAX_OVERFLOW', 10),
            connection_timeout=self._get_int('DB_CONNECTION_TIMEOUT', 30),
            pool_recycle=self._get_int('DB_POOL_RECYCLE', 3600)
        )

        self.leaderboard = LeaderboardSettings(
            cache_timeout_seconds=self._get_int('LEADERBOARD_CACHE_TIMEOUT', 300),
            max_entries_per_category=self._get_int('LEADERBOARD_MAX_ENTRIES', 100),
            default_leaderboard_limit=self._get_int('LEADERBOARD_DEFAULT_LIMIT', 20),
            min_progress_days=self._get_int('LEADERBOARD_MIN_PROGRESS_DAYS', 7),
            max_progress_days=self._get_int('LEADERBOARD_MAX_PROGRESS_DAYS', 90),
            enable_monthly_leaderboards=self._get_bool('LEADERBOARD_ENABLE_MONTHLY', True),
            enable_weekly_leaderboards=self._get_bool('LEADERBOARD_ENABLE_WEEKLY', True),
            enable_daily_leaderboards=self._get_bool('LEADERBOARD_ENABLE_DAILY', True)
        )

        self.logging = LoggingSettings(
            level=os.getenv('LOG_LEVEL', 'INFO').upper(),
            log_file=os.getenv('LOG_FILE', 'bot.log'),
            max_file_size_mb=self._get_int('LOG_MAX_FILE_SIZE_MB', 10),
            backup_count=self._get_int('LOG_BACKUP_COUNT', 5),
            format=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            basic_mode=self._get_bool('LOG_BASIC_MODE', False)
        )

        self.telegram = TelegramSettings(
            api_url=os.getenv('TELEGRAM_API_URL', 'https://api.telegram.org'),
            request_timeout=self._get_int('TELEGRAM_REQUEST_TIMEOUT', 30),
            connection_pool_size=self._get_int('TELEGRAM_CONNECTION_POOL_SIZE', 8),
            read_timeout=self._get_int('TELEGRAM_READ_TIMEOUT', 30),
            write_timeout=self._get_int('TELEGRAM_WRITE_TIMEOUT', 30),
            connect_timeout=self._get_int('TELEGRAM_CONNECT_TIMEOUT', 10)
        )

        # Initialize new production settings
        self.environment_settings = EnvironmentSettings(
            name=self.environment,
            production=self._get_bool('PRODUCTION', self.environment == 'production'),
            debug=self._get_bool('DEBUG', self.environment == 'development')
        )

        self.monitoring = MonitoringSettings(
            enabled=self._get_bool('MONITORING_ENABLED', self.environment == 'production'),
            health_check_enabled=self._get_bool('HEALTH_CHECK_ENABLED', self.environment == 'production'),
            metrics_enabled=self._get_bool('METRICS_ENABLED', self.environment == 'production'),
            metrics_port=self._get_int('METRICS_PORT', 9090),
            health_check_interval=self._get_int('HEALTH_CHECK_INTERVAL', 30),
            health_check_timeout=self._get_int('HEALTH_CHECK_TIMEOUT', 10),
            health_check_failure_threshold=self._get_int('HEALTH_CHECK_FAILURE_THRESHOLD', 3)
        )

        self.security = SecuritySettings(
            cors_enabled=self._get_bool('CORS_ENABLED', False),
            ssl_verify=self._get_bool('SSL_VERIFY', True),
            secret_key=os.getenv('SECRET_KEY'),
            encryption_key=os.getenv('ENCRYPTION_KEY'),
            ssl_cert_path=os.getenv('SSL_CERT_PATH'),
            ssl_key_path=os.getenv('SSL_KEY_PATH'),
            ssl_ca_path=os.getenv('SSL_CA_PATH')
        )

        self.performance = PerformanceSettings(
            cache_enabled=self._get_bool('CACHE_ENABLED', self.environment == 'production'),
            cache_ttl=self._get_int('CACHE_TTL', 600 if self.environment == 'production' else 300),
            max_workers=self._get_int('MAX_WORKERS', 8 if self.environment == 'production' else 4),
            worker_timeout=self._get_int('WORKER_TIMEOUT', 300 if self.environment == 'production' else 120),
            rate_limit_enabled=self._get_bool('RATE_LIMIT_ENABLED', self.environment == 'production'),
            rate_limit_requests_per_minute=self._get_int('RATE_LIMIT_REQUESTS_PER_MINUTE', 100),
            rate_limit_burst=self._get_int('RATE_LIMIT_BURST', 200)
        )

        self.backup = BackupSettings(
            enabled=self._get_bool('BACKUP_ENABLED', self.environment == 'production'),
            schedule=os.getenv('BACKUP_SCHEDULE', '0 2 * * *'),
            retention_days=self._get_int('BACKUP_RETENTION_DAYS', 30),
            s3_bucket=os.getenv('BACKUP_S3_BUCKET'),
            s3_region=os.getenv('BACKUP_S3_REGION')
        )

        self.alerts = AlertSettings(
            enabled=self._get_bool('ALERT_ENABLED', self.environment == 'production'),
            webhook_url=os.getenv('ALERT_WEBHOOK_URL'),
            email_enabled=self._get_bool('ALERT_EMAIL_ENABLED', False),
            email_smtp_host=os.getenv('ALERT_EMAIL_SMTP_HOST'),
            email_smtp_port=self._get_int('ALERT_EMAIL_SMTP_PORT', 587),
            email_username=os.getenv('ALERT_EMAIL_USERNAME'),
            email_password=os.getenv('ALERT_EMAIL_PASSWORD'),
            email_to=os.getenv('ALERT_EMAIL_TO')
        )

    def _build_database_url(self) -> str:
        """Build database URL from components."""
        # Check if full URL is provided
        if os.getenv('DATABASE_URL'):
            return os.getenv('DATABASE_URL')

        # Build from individual components
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'ingress_leaderboard')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD')

        if not db_password:
            raise ValueError("DB_PASSWORD environment variable is required")

        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    def _validate_settings(self) -> None:
        """Validate critical settings."""
        errors = []

        # Validate bot token (allow placeholders for testing)
        if not self.bot.token:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        elif not (self.bot.token[0].isdigit() or self.bot.token.startswith('YOUR_TELEGRAM_BOT_TOKEN')):
            errors.append("TELEGRAM_BOT_TOKEN appears invalid (should start with a digit)")

        # Validate database URL
        if not self.database.url:
            errors.append("Database configuration is incomplete")
        elif not self.database.url.startswith(('postgresql://', 'sqlite:///')):
            errors.append("DATABASE_URL must start with postgresql:// or sqlite:///")

        # Validate logging level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.logging.level not in valid_levels:
            errors.append(f"LOG_LEVEL must be one of: {valid_levels}")

        # Validate numeric settings
        if self.bot.rate_limit_per_minute <= 0:
            errors.append("BOT_RATE_LIMIT_PER_MINUTE must be positive")
        if self.bot.rate_limit_per_hour <= 0:
            errors.append("BOT_RATE_LIMIT_PER_HOUR must be positive")
        if self.leaderboard.cache_timeout_seconds <= 0:
            errors.append("LEADERBOARD_CACHE_TIMEOUT must be positive")

        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"• {error}" for error in errors)
            logger.error(error_message)
            raise ValueError(error_message)

        logger.info("Settings validation passed")

    def _get_bool(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')

    def _get_int(self, key: str, default: int) -> int:
        """Get integer value from environment variable."""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid integer value for {key}, using default {default}")
            return default

    def _get_int_list(self, key: str) -> Optional[List[int]]:
        """Get comma-separated list of integers from environment variable."""
        value = os.getenv(key)
        if not value:
            return None

        try:
            return [int(x.strip()) for x in value.split(',') if x.strip()]
        except ValueError:
            logger.warning(f"Invalid integer list for {key}")
            return None

    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all settings as a dictionary.

        Returns:
            Dictionary containing all settings
        """
        return {
            'environment': {
                'name': self.environment_settings.name,
                'production': self.environment_settings.production,
                'debug': self.environment_settings.debug
            },
            'bot': {
                'token': f"{'*' * len(self.bot.token)}" if self.bot.token else None,
                'debug': self.bot.debug,
                'webhook_url': self.bot.webhook_url,
                'webhook_port': self.bot.webhook_port,
                'allowed_chat_ids': self.bot.allowed_chat_ids,
                'rate_limit_per_minute': self.bot.rate_limit_per_minute,
                'rate_limit_per_hour': self.bot.rate_limit_per_hour
            },
            'database': {
                'url': f"{'*' * len(self.database.url)}" if self.database.url else None,
                'echo': self.database.echo,
                'pool_size': self.database.pool_size,
                'max_overflow': self.database.max_overflow,
                'connection_timeout': self.database.connection_timeout,
                'pool_recycle': self.database.pool_recycle
            },
            'leaderboard': {
                'cache_timeout_seconds': self.leaderboard.cache_timeout_seconds,
                'max_entries_per_category': self.leaderboard.max_entries_per_category,
                'default_leaderboard_limit': self.leaderboard.default_leaderboard_limit,
                'min_progress_days': self.leaderboard.min_progress_days,
                'max_progress_days': self.leaderboard.max_progress_days,
                'enable_monthly_leaderboards': self.leaderboard.enable_monthly_leaderboards,
                'enable_weekly_leaderboards': self.leaderboard.enable_weekly_leaderboards,
                'enable_daily_leaderboards': self.leaderboard.enable_daily_leaderboards
            },
            'logging': {
                'level': self.logging.level,
                'log_file': self.logging.log_file,
                'max_file_size_mb': self.logging.max_file_size_mb,
                'backup_count': self.logging.backup_count,
                'format': self.logging.format,
                'basic_mode': self.logging.basic_mode
            },
            'telegram': {
                'api_url': self.telegram.api_url,
                'request_timeout': self.telegram.request_timeout,
                'connection_pool_size': self.telegram.connection_pool_size,
                'read_timeout': self.telegram.read_timeout,
                'write_timeout': self.telegram.write_timeout,
                'connect_timeout': self.telegram.connect_timeout
            },
            'monitoring': {
                'enabled': self.monitoring.enabled,
                'health_check_enabled': self.monitoring.health_check_enabled,
                'metrics_enabled': self.monitoring.metrics_enabled,
                'metrics_port': self.monitoring.metrics_port,
                'health_check_interval': self.monitoring.health_check_interval,
                'health_check_timeout': self.monitoring.health_check_timeout,
                'health_check_failure_threshold': self.monitoring.health_check_failure_threshold
            },
            'security': {
                'cors_enabled': self.security.cors_enabled,
                'ssl_verify': self.security.ssl_verify,
                'secret_key': f"{'*' * len(self.security.secret_key)}" if self.security.secret_key else None,
                'encryption_key': f"{'*' * len(self.security.encryption_key)}" if self.security.encryption_key else None,
                'ssl_cert_path': self.security.ssl_cert_path,
                'ssl_key_path': self.security.ssl_key_path,
                'ssl_ca_path': self.security.ssl_ca_path
            },
            'performance': {
                'cache_enabled': self.performance.cache_enabled,
                'cache_ttl': self.performance.cache_ttl,
                'max_workers': self.performance.max_workers,
                'worker_timeout': self.performance.worker_timeout,
                'rate_limit_enabled': self.performance.rate_limit_enabled,
                'rate_limit_requests_per_minute': self.performance.rate_limit_requests_per_minute,
                'rate_limit_burst': self.performance.rate_limit_burst
            },
            'backup': {
                'enabled': self.backup.enabled,
                'schedule': self.backup.schedule,
                'retention_days': self.backup.retention_days,
                's3_bucket': self.backup.s3_bucket,
                's3_region': self.backup.s3_region
            },
            'alerts': {
                'enabled': self.alerts.enabled,
                'webhook_url': self.alerts.webhook_url,
                'email_enabled': self.alerts.email_enabled,
                'email_smtp_host': self.alerts.email_smtp_host,
                'email_smtp_port': self.alerts.email_smtp_port,
                'email_username': self.alerts.email_username,
                'email_to': self.alerts.email_to
            }
        }

    def is_production(self) -> bool:
        """
        Check if running in production mode.

        Returns:
            True if production mode, False otherwise
        """
        return self.environment_settings.production

    def is_debug(self) -> bool:
        """
        Check if debug mode is enabled.

        Returns:
            True if debug mode, False otherwise
        """
        return self.environment_settings.debug or self.bot.debug

    def get_cache_duration(self, cache_type: str = 'leaderboard') -> int:
        """
        Get cache duration for different cache types.

        Args:
            cache_type: Type of cache ('leaderboard', 'stats', 'etc.')

        Returns:
            Cache duration in seconds
        """
        cache_durations = {
            'leaderboard': self.leaderboard.cache_timeout_seconds,
            'stats': self.leaderboard.cache_timeout_seconds * 2,  # Stats cached longer
            'user': 600,  # 10 minutes
            'faction': self.leaderboard.cache_timeout_seconds
        }

        return cache_durations.get(cache_type, self.leaderboard.cache_timeout_seconds)

    def validate_chat_id(self, chat_id: int) -> bool:
        """
        Validate if chat ID is allowed to use the bot.

        Args:
            chat_id: Telegram chat ID

        Returns:
            True if allowed, False otherwise
        """
        # If no allowed chat IDs are specified, allow all chats
        if not self.bot.allowed_chat_ids:
            return True

        return chat_id in self.bot.allowed_chat_ids

    def get_environment_info(self) -> Dict[str, Any]:
        """
        Get information about the current environment.

        Returns:
            Dictionary with environment information
        """
        return {
            'environment': self.environment_settings.name,
            'production': self.environment_settings.production,
            'debug': self.environment_settings.debug,
            'working_directory': str(Path.cwd()),
            'python_path': str(Path(__file__).parent.parent),
            'config_loaded': bool(self.bot.token),
            'database_configured': bool(self.database.url),
            'monitoring_enabled': self.monitoring.enabled,
            'metrics_enabled': self.monitoring.metrics_enabled,
            'health_check_enabled': self.monitoring.health_check_enabled,
            'backup_enabled': self.backup.enabled,
            'alerts_enabled': self.alerts.enabled,
            'timezone': os.getenv('TZ', 'UTC'),
            'locale': os.getenv('LC_ALL', 'en_US.UTF-8')
        }


# Global settings instance
_settings = None


def get_settings(env_file: Optional[str] = None) -> Settings:
    """
    Get or create global settings instance.

    Args:
        env_file: Optional path to .env file

    Returns:
        Settings instance
    """
    global _settings

    if _settings is None:
        _settings = Settings(env_file)

    return _settings


def initialize_settings(env_file: Optional[str] = None) -> Settings:
    """
    Initialize global settings instance.

    Args:
        env_file: Optional path to .env file

    Returns:
        Initialized Settings instance
    """
    return get_settings(env_file)


# Environment validation functions
def validate_environment() -> List[str]:
    """
    Validate the current environment setup.

    Returns:
        List of validation warnings/errors
    """
    warnings = []

    # Check required environment variables
    required_vars = ['TELEGRAM_BOT_TOKEN', 'DB_PASSWORD']
    for var in required_vars:
        if not os.getenv(var):
            warnings.append(f"Missing required environment variable: {var}")

    # Check optional but recommended variables
    optional_vars = [
        ('DB_HOST', 'localhost'),
        ('DB_NAME', 'ingress_leaderboard'),
        ('DB_USER', 'postgres'),
        ('LOG_LEVEL', 'INFO')
    ]

    for var, default in optional_vars:
        value = os.getenv(var, default)
        if not value:
            warnings.append(f"Using default for {var}: {default}")

    # Check for common configuration issues
    if os.getenv('PRODUCTION', 'false').lower() in ('true', '1'):
        if os.getenv('BOT_DEBUG', 'false').lower() in ('true', '1'):
            warnings.append("Debug mode is enabled in production environment")

        if not os.getenv('DATABASE_URL'):
            warnings.append("DATABASE_URL should be set in production")

    return warnings


def print_environment_info(settings: Settings) -> None:
    """
    Print environment information for debugging.

    Args:
        settings: Settings instance
    """
    env_info = settings.get_environment_info()

    print("Environment Information:")
    print(f"  Environment: {env_info['environment']}")
    print(f"  Debug Mode: {env_info['debug']}")
    print(f"  Working Directory: {env_info['working_directory']}")
    print(f"  Config Loaded: {env_info['config_loaded']}")
    print(f"  Database Configured: {env_info['database_configured']}")

    if env_info['timezone']:
        print(f"  Timezone: {env_info['timezone']}")
    if env_info['locale']:
        print(f"  Locale: {env_info['locale']}")

    print()  # Empty line