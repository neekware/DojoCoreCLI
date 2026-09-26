"""Configuration management system for Dojo Core CLI.

This module provides a flexible configuration system that supports:
- Multiple configuration sources (files, env vars, CLI args)
- Hierarchical configuration with overrides
- Type validation and schema enforcement
- Secure handling of sensitive values
"""

import json
import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

import click
import tomli  # For reading TOML files (Python 3.11+ has tomllib built-in)
import yaml

from commands.utils.exceptions import (
    ConfigurationError,
    InvalidConfigError,
)
from commands.utils.logging import get_logger

# Type variable for configuration classes
T = TypeVar("T", bound="BaseConfig")


class ConfigFormat(Enum):
    """Supported configuration file formats."""

    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    ENV = "env"


class ConfigSource(Enum):
    """Configuration sources in order of precedence (lowest to highest)."""

    DEFAULT = 1
    GLOBAL = 2
    PROJECT = 3
    USER = 4
    ENVIRONMENT = 5
    CLI = 6


@dataclass
class BaseConfig:
    """Base configuration class that all configs should inherit from."""

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            InvalidConfigError: If configuration is invalid
        """
        pass  # Override in subclasses

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """Create configuration from dictionary.

        Args:
            data: Configuration data

        Returns:
            Configuration instance
        """
        return cls(**data)

    def merge(self, other: "BaseConfig") -> None:
        """Merge another configuration into this one.

        Args:
            other: Configuration to merge
        """
        for key, value in other.to_dict().items():
            if value is not None:
                setattr(self, key, value)


@dataclass
class CoreConfig(BaseConfig):
    """Core CLI configuration."""

    # General settings
    project_name: str = "Dojo Core CLI"
    debug: bool = False
    verbose: int = 0
    quiet: bool = False
    color: bool = True
    json_output: bool = False

    # Paths
    project_root: Optional[Path] = None
    config_dir: Optional[Path] = None
    cache_dir: Optional[Path] = None
    log_dir: Optional[Path] = None
    plugin_dir: Optional[Path] = None

    # Logging
    log_level: str = "INFO"
    log_format: str = "colored"
    log_to_file: bool = False
    audit_logging: bool = True

    # Performance
    max_workers: int = 4
    timeout: int = 60
    retry_count: int = 3
    retry_delay: int = 1

    # Security
    allow_unsafe_commands: bool = False
    require_authentication: bool = False
    encryption_enabled: bool = True

    # Telemetry (opt-in)
    telemetry_enabled: bool = False
    telemetry_endpoint: Optional[str] = None
    anonymous_id: Optional[str] = None

    # Plugin settings
    plugins_enabled: bool = True
    auto_load_plugins: bool = True
    trusted_plugins: list[str] = field(default_factory=list)

    # Update checking
    auto_update_check: bool = False
    update_check_interval: int = 86400  # 24 hours in seconds

    def validate(self) -> None:
        """Validate core configuration."""
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise InvalidConfigError(
                f"Invalid log level: {self.log_level}",
                suggestions=[f"Use one of: {', '.join(valid_levels)}"],
            )

        # Validate paths exist if specified
        for path_attr in [
            "project_root",
            "config_dir",
            "cache_dir",
            "log_dir",
            "plugin_dir",
        ]:
            path_value = getattr(self, path_attr)
            if path_value and not Path(path_value).exists():
                Path(path_value).mkdir(parents=True, exist_ok=True)

        # Validate numeric ranges
        if self.max_workers < 1:
            raise InvalidConfigError("max_workers must be at least 1")

        if self.timeout < 1:
            raise InvalidConfigError("timeout must be at least 1 second")

        if self.retry_count < 0:
            raise InvalidConfigError("retry_count cannot be negative")


@dataclass
class DevelopmentConfig(BaseConfig):
    """Development-specific configuration."""

    # Code formatting
    format_on_save: bool = True
    use_black: bool = True
    use_ruff: bool = True
    use_mypy: bool = True

    # Testing
    test_coverage_threshold: float = 80.0
    fail_on_coverage_drop: bool = True
    parallel_testing: bool = True

    # Pre-commit
    pre_commit_enabled: bool = True
    auto_fix: bool = False

    # Development server
    hot_reload: bool = True
    dev_port: int = 8000
    dev_host: str = "localhost"


@dataclass
class BuildConfig(BaseConfig):
    """Build configuration."""

    # Build settings
    optimization_level: str = "O2"
    parallel_build: bool = True
    clean_before_build: bool = False

    # Output settings
    output_dir: Path = Path("build")
    dist_dir: Path = Path("dist")

    # Target platforms
    target_platforms: list[str] = field(
        default_factory=lambda: ["linux", "macos", "windows"]
    )
    cross_compile: bool = False


class ConfigManager:
    """Manages application configuration from multiple sources."""

    def __init__(
        self,
        config_class: type[BaseConfig] = CoreConfig,
        app_name: str = "dojo",
    ):
        """Initialize configuration manager.

        Args:
            config_class: Configuration class to use
            app_name: Application name for config paths
        """
        self.logger = get_logger(__name__)
        self.config_class = config_class
        self.app_name = app_name
        self.config: BaseConfig = config_class()
        self.config_sources: dict[ConfigSource, dict[str, Any]] = {}
        self._initialize_paths()

    def _initialize_paths(self) -> None:
        """Initialize configuration paths."""
        # Global config directory
        self.global_config_dir = Path("/etc") / self.app_name

        # User config directory
        self.user_config_dir = Path.home() / f".{self.app_name}"

        # Project config (if in project)
        self.project_config_file = Path.cwd() / f".{self.app_name}.toml"

        # Environment variable prefix
        self.env_prefix = self.app_name.upper()

    def load(self) -> BaseConfig:
        """Load configuration from all sources.

        Returns:
            Merged configuration object
        """
        self.logger.debug("Loading configuration from all sources")

        # Load in order of precedence
        self._load_defaults()
        self._load_global_config()
        self._load_project_config()
        self._load_user_config()
        self._load_env_vars()

        # Merge all sources
        self._merge_configs()

        # Validate final configuration
        self.config.validate()

        self.logger.debug(f"Configuration loaded: {self.config.to_dict()}")
        return self.config

    def _load_defaults(self) -> None:
        """Load default configuration."""
        self.config_sources[ConfigSource.DEFAULT] = self.config.to_dict()

    def _load_global_config(self) -> None:
        """Load global system configuration."""
        config_file = self.global_config_dir / "config.toml"
        if config_file.exists():
            try:
                data = self._read_config_file(config_file)
                self.config_sources[ConfigSource.GLOBAL] = data
                self.logger.debug(f"Loaded global config from {config_file}")
            except Exception as e:
                self.logger.warning(f"Failed to load global config: {e}")

    def _load_project_config(self) -> None:
        """Load project-specific configuration."""
        if self.project_config_file.exists():
            try:
                data = self._read_config_file(self.project_config_file)
                self.config_sources[ConfigSource.PROJECT] = data
                self.logger.debug(
                    f"Loaded project config from {self.project_config_file}"
                )
            except Exception as e:
                self.logger.warning(f"Failed to load project config: {e}")

    def _load_user_config(self) -> None:
        """Load user-specific configuration."""
        config_file = self.user_config_dir / "config.toml"
        if config_file.exists():
            try:
                data = self._read_config_file(config_file)
                self.config_sources[ConfigSource.USER] = data
                self.logger.debug(f"Loaded user config from {config_file}")
            except Exception as e:
                self.logger.warning(f"Failed to load user config: {e}")

    def _load_env_vars(self) -> None:
        """Load configuration from environment variables."""
        env_config = {}
        prefix = f"{self.env_prefix}_"

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert EHAYE_LOG_LEVEL to log_level
                config_key = key[len(prefix) :].lower()

                # Convert value types
                converted_value: Any = value
                if value.lower() in ("true", "false"):
                    converted_value = value.lower() == "true"
                elif value.isdigit():
                    converted_value = int(value)
                elif self._is_float(value):
                    converted_value = float(value)

                env_config[config_key] = converted_value

        if env_config:
            self.config_sources[ConfigSource.ENVIRONMENT] = env_config
            self.logger.debug(f"Loaded {len(env_config)} settings from environment")

    def _is_float(self, value: str) -> bool:
        """Check if string is a float."""
        try:
            float(value)
            return "." in value
        except ValueError:
            return False

    def _read_config_file(self, path: Path) -> dict[str, Any]:
        """Read configuration file based on extension.

        Args:
            path: Path to configuration file

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If file cannot be read
        """
        suffix = path.suffix.lower()

        try:
            if suffix == ".json":
                with open(path) as f:
                    data: dict[str, Any] = json.load(f)
                    return data
            elif suffix in [".yaml", ".yml"]:
                with open(path) as f:
                    data = yaml.load(f, Loader=yaml.Loader)
                    return dict(data) if data else {}
            elif suffix == ".toml":
                with open(path, "rb") as f:
                    data = tomli.load(f)
                    return data
            else:
                raise InvalidConfigError(f"Unsupported config format: {suffix}")
        except Exception as e:
            raise ConfigurationError(f"Failed to read config file {path}: {e}") from e

    def _merge_configs(self) -> None:
        """Merge all configuration sources in order of precedence."""
        merged = {}

        # Merge in order of precedence
        for source in ConfigSource:
            if source in self.config_sources:
                merged.update(self.config_sources[source])

        # Create new config instance from merged data
        self.config = self.config_class.from_dict(merged)

    def save(
        self,
        path: Optional[Path] = None,
        format: ConfigFormat = ConfigFormat.TOML,
        source: ConfigSource = ConfigSource.USER,
    ) -> None:
        """Save configuration to file.

        Args:
            path: Path to save to (default: user config)
            format: File format
            source: Configuration source level
        """
        if path is None:
            path = self.user_config_dir / f"config.{format.value}"

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Get configuration data
        data = self.config.to_dict()

        # Write based on format
        if format == ConfigFormat.JSON:
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        elif format == ConfigFormat.YAML:
            with open(path, "w") as f:
                yaml.safe_dump(data, f, default_flow_style=False)
        elif format == ConfigFormat.TOML:
            # For TOML, we need to use tomlkit for writing
            import tomlkit

            with open(path, "w") as f:
                tomlkit.dump(data, f)

        self.logger.info(f"Configuration saved to {path}")

    def update(self, **kwargs: Any) -> None:
        """Update configuration values.

        Args:
            **kwargs: Configuration values to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                self.logger.warning(f"Unknown configuration key: {key}")

        # Re-validate after update
        self.config.validate()

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return getattr(self.config, key, default)

    def reset(self, source: Optional[ConfigSource] = None) -> None:
        """Reset configuration to defaults.

        Args:
            source: Specific source to reset (None for all)
        """
        if source:
            self.config_sources.pop(source, None)
        else:
            self.config_sources.clear()
            self.config = self.config_class()

        self.load()


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager.

    Returns:
        Configuration manager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        _config_manager.load()
    return _config_manager


def get_config() -> CoreConfig:
    """Get the current configuration.

    Returns:
        Current configuration
    """
    manager = get_config_manager()
    return manager.config  # type: ignore


def update_config(**kwargs: Any) -> None:
    """Update configuration values.

    Args:
        **kwargs: Configuration values to update
    """
    manager = get_config_manager()
    manager.update(**kwargs)


# Click integration
def config_option(*args: Any, **kwargs: Any) -> Callable:
    """Decorator to add config file option to Click commands."""

    def decorator(f: Callable) -> Callable:
        return click.option(
            "--config",
            "-c",
            type=click.Path(exists=True, path_type=Path),
            help="Configuration file path",
            envvar="EHAYE_CONFIG",
        )(f)

    return decorator


def common_options(f: Callable) -> Callable:
    """Decorator to add common CLI options."""
    f = click.option("--debug", is_flag=True, help="Enable debug mode")(f)
    f = click.option("--verbose", "-v", count=True, help="Increase verbosity")(f)
    f = click.option("--quiet", "-q", is_flag=True, help="Suppress output")(f)
    f = click.option("--json", "json_output", is_flag=True, help="Output as JSON")(f)
    f = click.option("--no-color", is_flag=True, help="Disable colored output")(f)
    return f
