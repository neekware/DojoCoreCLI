"""Exception hierarchy for the Dojo Core CLI.

This module defines a comprehensive exception hierarchy for proper error
handling throughout the application.
"""

from typing import Any, Optional


class DojoError(Exception):
    """Base exception for all Dojo CLI errors."""

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
    ):
        """Initialize the exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code for programmatic handling
            details: Additional error details as key-value pairs
            suggestions: List of suggestions to resolve the error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.suggestions = suggestions or []

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for structured logging."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "suggestions": self.suggestions,
        }


# Configuration Errors
class ConfigurationError(DojoError):
    """Raised when there's a configuration problem."""

    pass


class MissingConfigError(ConfigurationError):
    """Raised when required configuration is missing."""

    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration is invalid."""

    pass


# Command Execution Errors
class CommandError(DojoError):
    """Base exception for command-related errors."""

    pass


class CommandNotFoundError(CommandError):
    """Raised when a command cannot be found."""

    pass


class CommandExecutionError(CommandError):
    """Raised when command execution fails."""

    def __init__(
        self,
        message: str,
        *,
        command: Optional[list[str]] = None,
        returncode: Optional[int] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize command execution error.

        Args:
            message: Error message
            command: Command that failed
            returncode: Exit code from command
            stdout: Standard output from command
            stderr: Standard error from command
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

        # Add to details
        self.details.update(
            {
                "command": command,
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
            }
        )


class CommandTimeoutError(CommandError):
    """Raised when a command times out."""

    def __init__(
        self,
        message: str,
        *,
        command: Optional[list[str]] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ):
        """Initialize timeout error.

        Args:
            message: Error message
            command: Command that timed out
            timeout: Timeout value in seconds
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.command = command
        self.timeout = timeout

        self.details.update(
            {
                "command": command,
                "timeout": timeout,
            }
        )


class InvalidCommandError(CommandError):
    """Raised when a command is invalid or unsafe."""

    pass


# File System Errors
class FileSystemError(DojoError):
    """Base exception for file system operations."""

    pass


class FileNotFoundError(FileSystemError):
    """Raised when a required file is not found."""

    def __init__(self, message: str, *, path: Optional[str] = None, **kwargs: Any):
        """Initialize file not found error.

        Args:
            message: Error message
            path: Path to the missing file
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.path = path
        self.details["path"] = path


class DirectoryNotFoundError(FileSystemError):
    """Raised when a required directory is not found."""

    def __init__(self, message: str, *, path: Optional[str] = None, **kwargs: Any):
        """Initialize directory not found error.

        Args:
            message: Error message
            path: Path to the missing directory
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.path = path
        self.details["path"] = path


class PermissionError(FileSystemError):
    """Raised when there's a permission issue."""

    pass


class DiskSpaceError(FileSystemError):
    """Raised when there's insufficient disk space."""

    pass


# Project Errors
class ProjectError(DojoError):
    """Base exception for project-related errors."""

    pass


class NotInProjectError(ProjectError):
    """Raised when command is run outside of a project."""

    def __init__(self, message: Optional[str] = None, **kwargs: Any):
        """Initialize not in project error."""
        default_message = (
            "This command must be run from within a project directory. "
            "Look for a directory containing 'pyproject.toml' or similar project files."
        )
        super().__init__(message or default_message, **kwargs)
        self.suggestions = [
            "Navigate to your project directory",
            "Run 'cli init' to initialize a new project",
            "Check that you're in the correct directory",
        ]


class ProjectNotInitializedError(ProjectError):
    """Raised when project is not properly initialized."""

    def __init__(self, message: Optional[str] = None, **kwargs: Any):
        """Initialize project not initialized error."""
        default_message = "Project is not properly initialized."
        super().__init__(message or default_message, **kwargs)
        self.suggestions = [
            "Run 'cli init' to initialize the project",
            "Check that all required project files exist",
            "Verify project configuration",
        ]


# Dependency Errors
class DependencyError(DojoError):
    """Base exception for dependency-related errors."""

    pass


class MissingDependencyError(DependencyError):
    """Raised when a required dependency is missing."""

    def __init__(
        self,
        message: str,
        *,
        dependency: Optional[str] = None,
        install_command: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize missing dependency error.

        Args:
            message: Error message
            dependency: Name of missing dependency
            install_command: Command to install the dependency
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.dependency = dependency
        self.install_command = install_command

        self.details["dependency"] = dependency

        if install_command:
            self.suggestions.append(f"Install with: {install_command}")


class IncompatibleDependencyError(DependencyError):
    """Raised when dependencies are incompatible."""

    pass


# Network Errors
class NetworkError(DojoError):
    """Base exception for network-related errors."""

    pass


class ConnectionError(NetworkError):
    """Raised when network connection fails."""

    pass


class TimeoutError(NetworkError):
    """Raised when network operation times out."""

    pass


# Build Errors
class BuildError(DojoError):
    """Base exception for build-related errors."""

    pass


class CompilationError(BuildError):
    """Raised when compilation fails."""

    pass


class LinkError(BuildError):
    """Raised when linking fails."""

    pass


class TestFailureError(BuildError):
    """Raised when tests fail."""

    def __init__(
        self,
        message: str,
        *,
        failed_tests: Optional[list[str]] = None,
        test_output: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize test failure error.

        Args:
            message: Error message
            failed_tests: List of failed test names
            test_output: Full test output
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.failed_tests = failed_tests or []
        self.test_output = test_output

        self.details.update(
            {
                "failed_tests": self.failed_tests,
                "test_output": test_output,
            }
        )


# Plugin Errors
class PluginError(DojoError):
    """Base exception for plugin-related errors."""

    pass


class PluginNotFoundError(PluginError):
    """Raised when a plugin cannot be found."""

    pass


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""

    pass


class PluginExecutionError(PluginError):
    """Raised when plugin execution fails."""

    pass


# Validation Errors
class ValidationError(DojoError):
    """Base exception for validation errors."""

    pass


class InputValidationError(ValidationError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        *,
        field: Optional[str] = None,
        value: Any = None,
        expected_type: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize input validation error.

        Args:
            message: Error message
            field: Field that failed validation
            value: Invalid value
            expected_type: Expected type or format
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.field = field
        self.value = value
        self.expected_type = expected_type

        self.details.update(
            {
                "field": field,
                "value": str(value),
                "expected_type": expected_type,
            }
        )


class SchemaValidationError(ValidationError):
    """Raised when schema validation fails."""

    pass


# Authentication/Authorization Errors
class SecurityError(DojoError):
    """Base exception for security-related errors."""

    pass


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(SecurityError):
    """Raised when authorization fails."""

    pass


class TokenExpiredError(SecurityError):
    """Raised when a token has expired."""

    pass


# Resource Errors
class ResourceError(DojoError):
    """Base exception for resource-related errors."""

    pass


class ResourceNotFoundError(ResourceError):
    """Raised when a resource cannot be found."""

    pass


class ResourceLimitError(ResourceError):
    """Raised when a resource limit is exceeded."""

    pass


class ResourceBusyError(ResourceError):
    """Raised when a resource is busy."""

    pass


# User Errors
class UserError(DojoError):
    """Base exception for user-caused errors."""

    pass


class UserCancelledError(UserError):
    """Raised when user cancels an operation."""

    def __init__(self, message: Optional[str] = None, **kwargs: Any):
        """Initialize user cancelled error."""
        super().__init__(message or "Operation cancelled by user", **kwargs)


class InvalidInputError(UserError):
    """Raised when user provides invalid input."""

    pass


# Internal Errors
class InternalError(DojoError):
    """Base exception for internal errors."""

    def __init__(self, message: str, **kwargs: Any):
        """Initialize internal error."""
        super().__init__(message, **kwargs)
        self.suggestions = [
            "This is likely a bug in the CLI",
            "Please report this issue at: https://github.com/neekware/DojoCoreCLI/issues",
            "Include the full error message and stack trace",
        ]


class NotImplementedError(InternalError):
    """Raised when a feature is not yet implemented."""

    def __init__(self, feature: Optional[str] = None, **kwargs: Any):
        """Initialize not implemented error."""
        message = (
            f"Feature not yet implemented: {feature}"
            if feature
            else "Feature not yet implemented"
        )
        super().__init__(message, **kwargs)
        self.suggestions = [
            "This feature is planned for a future release",
            "Check the roadmap for implementation timeline",
            "Consider contributing: https://github.com/neekware/DojoCoreCLI",
        ]


class UnexpectedError(InternalError):
    """Raised when an unexpected error occurs."""

    pass
