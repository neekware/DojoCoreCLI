"""Production-grade logging system for Dojo Core CLI.

This module provides structured logging with multiple handlers, formatters,
and output options suitable for both development and production use.
"""

import json
import logging
import logging.handlers
import os
import sys
import traceback
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

import click


class LogLevel(Enum):
    """Log levels for the application."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogFormat(Enum):
    """Available log formats."""

    PLAIN = "plain"
    JSON = "json"
    COLORED = "colored"
    STRUCTURED = "structured"


class ColorFormatter(logging.Formatter):
    """Custom formatter with color support for terminal output."""

    COLORS = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bright_red",
    }

    SYMBOLS = {
        "DEBUG": "🔍",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🔥",
    }

    def __init__(self, use_symbols: bool = True, show_time: bool = True) -> None:
        """Initialize color formatter.

        Args:
            use_symbols: Whether to use emoji symbols
            show_time: Whether to show timestamp
        """
        self.use_symbols = use_symbols
        self.show_time = show_time
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors.

        Args:
            record: Log record to format

        Returns:
            Formatted log message with colors
        """
        level_name = record.levelname
        color = self.COLORS.get(level_name, "white")

        # Build the message parts
        parts = []

        if self.show_time:
            time_str = datetime.now().strftime("%H:%M:%S")
            parts.append(click.style(f"[{time_str}]", fg="bright_black"))

        if self.use_symbols:
            symbol = self.SYMBOLS.get(level_name, "")
            parts.append(symbol)

        parts.append(click.style(level_name, fg=color, bold=True))

        # Add module info for debug level
        if record.levelno <= logging.DEBUG:
            module_info = f"{record.name}:{record.funcName}:{record.lineno}"
            parts.append(click.style(f"[{module_info}]", fg="bright_black"))

        # Format the message
        message = record.getMessage()

        # Add exception info if present
        if record.exc_info:
            exc_text = "".join(traceback.format_exception(*record.exc_info))
            message += f"\n{exc_text}"

        parts.append(message)

        return " ".join(parts)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log entry
        """
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "process": record.process,
            "thread": record.thread,
        }

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                log_obj[key] = value

        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": "".join(traceback.format_exception(*record.exc_info)),
            }

        return json.dumps(log_obj, default=str)


class StructuredFormatter(logging.Formatter):
    """Structured key-value formatter for easy parsing."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured key-value pairs.

        Args:
            record: Log record to format

        Returns:
            Structured log entry
        """
        parts = [
            f"time={datetime.now(timezone.utc).isoformat()}",
            f"level={record.levelname}",
            f"logger={record.name}",
            f'msg="{record.getMessage()}"',
        ]

        # Add debug info
        if record.levelno <= logging.DEBUG:
            parts.extend(
                [
                    f"module={record.module}",
                    f"function={record.funcName}",
                    f"line={record.lineno}",
                ]
            )

        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            exc_type = record.exc_info[0].__name__
            exc_msg = str(record.exc_info[1])
            parts.append(f'exception="{exc_type}: {exc_msg}"')

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                parts.append(f'{key}="{value}"')

        return " ".join(parts)


class LogManager:
    """Centralized log management for the application."""

    _instance: Optional["LogManager"] = None
    _initialized: bool = False

    def __new__(cls) -> "LogManager":
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize log manager."""
        if not self._initialized:
            self.loggers: dict[str, logging.Logger] = {}
            self.handlers: dict[str, logging.Handler] = {}
            self.log_dir: Optional[Path] = None
            self.default_level = LogLevel.INFO
            self.default_format = LogFormat.COLORED
            self._setup_root_logger()
            self._initialized = True

    def _setup_root_logger(self) -> None:
        """Set up the root logger configuration."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capture all, filter in handlers

        # Remove any existing handlers
        root_logger.handlers.clear()

        # Add null handler to prevent unwanted output
        root_logger.addHandler(logging.NullHandler())

    def get_logger(
        self,
        name: str,
        level: Optional[LogLevel] = None,
        format_type: Optional[LogFormat] = None,
    ) -> logging.Logger:
        """Get or create a logger with specified configuration.

        Args:
            name: Logger name (usually __name__)
            level: Log level
            format_type: Output format

        Returns:
            Configured logger instance
        """
        if name in self.loggers:
            return self.loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel((level or self.default_level).value)
        logger.propagate = False  # Don't propagate to root

        # Add console handler
        console_handler = self._get_console_handler(format_type or self.default_format)
        logger.addHandler(console_handler)

        # Add file handler if log directory is set
        if self.log_dir:
            file_handler = self._get_file_handler(name)
            logger.addHandler(file_handler)

        self.loggers[name] = logger
        return logger

    def _get_console_handler(self, format_type: LogFormat) -> logging.Handler:
        """Get or create console handler with specified format.

        Args:
            format_type: Output format

        Returns:
            Configured console handler
        """
        handler_key = f"console_{format_type.value}"

        if handler_key not in self.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setLevel(logging.DEBUG)

            # Set formatter based on type
            formatter: logging.Formatter
            if format_type == LogFormat.COLORED:
                formatter = ColorFormatter(use_symbols=True, show_time=True)
            elif format_type == LogFormat.JSON:
                formatter = JSONFormatter()
            elif format_type == LogFormat.STRUCTURED:
                formatter = StructuredFormatter()
            else:  # PLAIN
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )

            handler.setFormatter(formatter)
            self.handlers[handler_key] = handler

        return self.handlers[handler_key]

    def _get_file_handler(self, logger_name: str) -> logging.Handler:
        """Get or create file handler for logger.

        Args:
            logger_name: Name of the logger

        Returns:
            Configured file handler
        """
        if not self.log_dir:
            raise ValueError("Log directory not set")

        handler_key = f"file_{logger_name}"

        if handler_key not in self.handlers:
            # Create log file path
            log_file = self.log_dir / f"{logger_name.replace('.', '_')}.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Use rotating file handler
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            )
            handler.setLevel(logging.DEBUG)

            # Use JSON format for file logs
            formatter = JSONFormatter()
            handler.setFormatter(formatter)

            self.handlers[handler_key] = handler

        return self.handlers[handler_key]

    def configure(
        self,
        level: Optional[Union[LogLevel, str]] = None,
        format_type: Optional[Union[LogFormat, str]] = None,
        log_dir: Optional[Union[Path, str]] = None,
        enable_file_logging: bool = False,
    ) -> None:
        """Configure global logging settings.

        Args:
            level: Default log level
            format_type: Default output format
            log_dir: Directory for log files
            enable_file_logging: Whether to enable file logging
        """
        if level:
            if isinstance(level, str):
                level = LogLevel[level.upper()]
            self.default_level = level

        if format_type:
            if isinstance(format_type, str):
                format_type = LogFormat[format_type.upper()]
            self.default_format = format_type

        if enable_file_logging and log_dir:
            self.log_dir = Path(log_dir)
            self.log_dir.mkdir(parents=True, exist_ok=True)

        # Update existing loggers
        for logger in self.loggers.values():
            logger.setLevel(self.default_level.value)

    def set_verbosity(self, verbose: int) -> None:
        """Set verbosity level based on count.

        Args:
            verbose: Verbosity count (0=WARNING, 1=INFO, 2+=DEBUG)
        """
        if verbose <= 0:
            level = LogLevel.WARNING
        elif verbose == 1:
            level = LogLevel.INFO
        else:
            level = LogLevel.DEBUG

        self.configure(level=level)

    def disable_color(self) -> None:
        """Disable color output (useful for CI/CD)."""
        self.configure(format_type=LogFormat.PLAIN)

    def enable_json_output(self) -> None:
        """Enable JSON output (useful for log aggregation)."""
        self.configure(format_type=LogFormat.JSON)

    def get_audit_logger(self) -> logging.Logger:
        """Get special audit logger for security events.

        Returns:
            Audit logger instance
        """
        audit_logger = self.get_logger("audit", level=LogLevel.INFO)

        # Ensure audit logs always go to file
        if not self.log_dir:
            self.log_dir = Path.home() / ".dojo" / "logs"
            self.log_dir.mkdir(parents=True, exist_ok=True)

        # Add special audit file handler
        audit_file = self.log_dir / "audit.log"
        handler = logging.handlers.RotatingFileHandler(
            audit_file,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10,
            encoding="utf-8",
        )
        handler.setLevel(logging.INFO)
        handler.setFormatter(JSONFormatter())
        audit_logger.addHandler(handler)

        return audit_logger


# Singleton instance
_log_manager = LogManager()


# Convenience functions
def get_logger(name: str, **kwargs: Any) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)
        **kwargs: Additional configuration options

    Returns:
        Configured logger
    """
    return _log_manager.get_logger(name, **kwargs)


def configure_logging(**kwargs: Any) -> LogManager:
    """Configure global logging settings.

    Args:
        **kwargs: Configuration options
    """
    _log_manager.configure(**kwargs)
    return _log_manager


def set_verbosity(verbose: int) -> None:
    """Set logging verbosity.

    Args:
        verbose: Verbosity level
    """
    _log_manager.set_verbosity(verbose)


def disable_color() -> None:
    """Disable colored output."""
    _log_manager.disable_color()


def enable_json_output() -> None:
    """Enable JSON output."""
    _log_manager.enable_json_output()


def audit_log(event: str, **details: Any) -> None:
    """Log an audit event.

    Args:
        event: Event name
        **details: Event details
    """
    audit_logger = _log_manager.get_audit_logger()
    audit_logger.info(event, extra=details)


# CLI integration
class LoggingGroup(click.Group):
    """Click group with automatic logging setup."""

    def invoke(self, ctx: click.Context) -> Any:
        """Set up logging before invoking command.

        Args:
            ctx: Click context
        """
        # Get verbosity from context
        verbose = ctx.params.get("verbose", 0)
        quiet = ctx.params.get("quiet", False)
        debug = ctx.params.get("debug", False)
        json_output = ctx.params.get("json", False)

        # Configure logging
        if quiet:
            set_verbosity(-1)  # Only warnings and errors
        elif debug:
            set_verbosity(2)  # Debug level
        else:
            set_verbosity(verbose)

        if json_output:
            enable_json_output()

        # Check if running in CI/CD environment
        if any(env in os.environ for env in ["CI", "GITHUB_ACTIONS", "JENKINS_URL"]):
            disable_color()

        # Log command invocation for audit
        audit_log(
            "command_invoked",
            command=ctx.info_name,
            args=ctx.params,
            user=os.environ.get("USER", "unknown"),
        )

        return super().invoke(ctx)


# Example usage in commands
def example_command_with_logging() -> None:
    """Example of how to use logging in commands."""
    logger = get_logger(__name__)

    logger.debug("Starting operation")
    logger.info("Processing data")

    try:
        # Some operation
        result = {"status": "success", "items": 42}
        logger.info("Operation completed", extra={"result": result})
    except Exception:
        logger.error("Operation failed", exc_info=True)
        raise

    logger.warning("This is a warning")
    logger.debug("Debug information", extra={"details": {"key": "value"}})
