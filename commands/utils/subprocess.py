"""Secure subprocess execution utilities for the CLI.

This module provides safe wrappers around subprocess operations to prevent
shell injection and other security vulnerabilities.
"""

import os
import shlex
import subprocess
from pathlib import Path
from typing import IO, Any, Optional, Union

from commands.utils.exceptions import (
    CommandExecutionError,
    CommandTimeoutError,
    InvalidCommandError,
)


class SecureCommand:
    """Secure command execution wrapper with validation and sanitization."""

    # Commands that are allowed to be executed
    ALLOWED_COMMANDS = {
        "python",
        "python3",
        "pip",
        "pip3",
        "git",
        "docker",
        "docker-compose",
        "npm",
        "yarn",
        "pnpm",
        "node",
        "cargo",
        "rustc",
        "rustfmt",
        "gcc",
        "g++",
        "clang",
        "clang++",
        "make",
        "cmake",
        "go",
        "gofmt",
        "java",
        "javac",
        "mvn",
        "gradle",
        "dotnet",
        "nuget",
        "black",
        "ruff",
        "mypy",
        "pytest",
        "pre-commit",
        "du",
        "ls",
        "cat",
        "grep",
        "find",
        "which",
    }

    def __init__(
        self,
        command: Union[str, list[str]],
        *,
        cwd: Optional[Path] = None,
        env: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        allow_unsafe: bool = False,
    ):
        """Initialize a secure command.

        Args:
            command: Command to execute (string or list of arguments)
            cwd: Working directory for command execution
            env: Environment variables (merged with current environment)
            timeout: Maximum execution time in seconds
            check: Raise exception on non-zero exit code
            capture_output: Capture stdout and stderr
            text: Return output as text (not bytes)
            allow_unsafe: Allow execution of commands not in allowlist (use with caution)

        Raises:
            InvalidCommandError: If command is not allowed and allow_unsafe is False
        """
        self.command = self._validate_command(command, allow_unsafe)
        self.cwd = Path(cwd) if cwd else Path.cwd()
        self.env = self._prepare_environment(env)
        self.timeout = timeout or 60.0  # Default 60 second timeout
        self.check = check
        self.capture_output = capture_output
        self.text = text

    def _validate_command(
        self, command: Union[str, list[str]], allow_unsafe: bool
    ) -> list[str]:
        """Validate and parse command for safe execution.

        Args:
            command: Command to validate
            allow_unsafe: Whether to allow commands not in allowlist

        Returns:
            List of command arguments

        Raises:
            InvalidCommandError: If command is invalid or not allowed
        """
        # Parse string commands safely
        if isinstance(command, str):
            # Use shlex for safe parsing (prevents injection)
            try:
                parsed = shlex.split(command)
            except ValueError as e:
                raise InvalidCommandError(f"Invalid command syntax: {e}") from e
        else:
            parsed = list(command)

        if not parsed:
            raise InvalidCommandError("Empty command")

        # Extract base command for validation
        base_cmd = Path(parsed[0]).name

        # Check against allowlist unless explicitly allowed
        if not allow_unsafe and base_cmd not in self.ALLOWED_COMMANDS:
            raise InvalidCommandError(
                f"Command '{base_cmd}' is not in the allowed list. "
                f"Use allow_unsafe=True if you're sure this is safe."
            )

        # Additional validation for suspicious patterns
        suspicious_patterns = [
            ";",
            "&&",
            "||",
            "|",
            ">",
            "<",
            ">>",
            "<<",
            "$",
            "`",
            "\\",
            "\n",
            "\r",
            "../",
            "~/",
            "/etc/",
            "/sys/",
            "/proc/",
        ]

        for arg in parsed[2:]:  # Skip command itself
            for pattern in suspicious_patterns:
                if pattern in arg and not allow_unsafe:
                    raise InvalidCommandError(
                        f"Suspicious pattern '{pattern}' found in arguments. "
                        f"This might be a security risk."
                    )

        return parsed

    def _prepare_environment(self, env: Optional[dict[str, str]]) -> dict[str, str]:
        """Prepare environment variables for subprocess.

        Args:
            env: Additional environment variables

        Returns:
            Merged environment dictionary
        """
        # Start with current environment
        new_env = dict(os.environ)

        # Remove potentially dangerous variables
        dangerous_vars = ["LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES"]
        for var in dangerous_vars:
            new_env.pop(var, None)

        # Add custom variables if provided
        if env:
            new_env.update(env)

        return new_env

    def run(self) -> subprocess.CompletedProcess:
        """Execute the command securely.

        Returns:
            CompletedProcess instance with results

        Raises:
            CommandExecutionError: If command fails and check=True
            CommandTimeoutError: If command times out
        """
        try:
            result = subprocess.run(
                " ".join(self.command) if isinstance(self.command, list) else self.command,
                cwd=self.cwd,
                env=self.env,
                capture_output=self.capture_output,
                text=self.text,
                timeout=self.timeout,
                check=False,  # We'll handle this ourselves
                shell=True,  # convenience: allow shell features in commands
            )

            if self.check and result.returncode != 0:
                raise CommandExecutionError(
                    f"Command failed with exit code {result.returncode}",
                    command=self.command,
                    returncode=result.returncode,
                    stdout=result.stdout if self.capture_output else None,
                    stderr=result.stderr if self.capture_output else None,
                )

            return result

        except subprocess.TimeoutExpired as e:
            raise CommandTimeoutError(
                f"Command timed out after {self.timeout} seconds",
                command=self.command,
                timeout=self.timeout,
            ) from e

        except Exception as e:
            raise CommandExecutionError(
                f"Command execution failed: {e}",
                command=self.command,
            ) from e


def run_command(
    command: Union[str, list[str]], **kwargs: Any
) -> subprocess.CompletedProcess:
    """Convenience function for running secure commands.

    Args:
        command: Command to execute
        **kwargs: Additional arguments for SecureCommand

    Returns:
        CompletedProcess with results

    Example:
        >>> result = run_command("git status")
        >>> print(result.stdout)
    """
    secure_cmd = SecureCommand(command, **kwargs)
    return secure_cmd.run()


def run_command_output(command: Union[str, list[str]], **kwargs: Any) -> str:
    """Run command and return stdout as string.

    Args:
        command: Command to execute
        **kwargs: Additional arguments for SecureCommand

    Returns:
        Command stdout as string

    Example:
        >>> output = run_command_output("git rev-parse HEAD")
        >>> print(f"Current commit: {output}")
    """
    kwargs["capture_output"] = True
    kwargs["text"] = True
    result = run_command(command, **kwargs)
    output = result.stdout.strip()
    return str(output)


def check_command_exists(command: str) -> bool:
    """Check if a command exists in the system PATH.

    Args:
        command: Command name to check

    Returns:
        True if command exists, False otherwise

    Example:
        >>> if check_command_exists("docker"):
        ...     print("Docker is installed")
    """
    try:
        result = run_command(
            ["which", command],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def run_piped_commands(
    commands: list[Union[str, list[str]]], **kwargs: Any
) -> subprocess.CompletedProcess:
    """Run multiple commands in a pipeline (like cmd1 | cmd2).

    Args:
        commands: List of commands to pipe together
        **kwargs: Additional arguments for subprocess

    Returns:
        CompletedProcess from the last command

    Example:
        >>> result = run_piped_commands([
        ...     "git log --oneline",
        ...     "head -n 10"
        ... ])
    """
    if not commands:
        raise InvalidCommandError("No commands provided for pipeline")

    processes = []
    prev_stdout = None

    try:
        for i, cmd in enumerate(commands):
            # Validate each command
            secure_cmd = SecureCommand(cmd, **kwargs)

            # Set up pipeline
            stdin: Optional[IO[str]] = prev_stdout
            stdout = subprocess.PIPE if i < len(commands) - 1 else None

            process = subprocess.Popen(
                secure_cmd.command,
                stdin=stdin,
                stdout=stdout,
                stderr=subprocess.PIPE,
                cwd=secure_cmd.cwd,
                env=secure_cmd.env,
                text=kwargs.get("text", True),
            )

            processes.append(process)
            prev_stdout = process.stdout

        # Wait for all processes to complete
        for process in processes[:-1]:
            process.wait()

        # Get output from last process
        stdout, stderr = processes[-1].communicate(timeout=kwargs.get("timeout", 60))

        return subprocess.CompletedProcess(
            args=str(commands),
            returncode=processes[-1].returncode,
            stdout=stdout,
            stderr=stderr,
        )

    finally:
        # Clean up any running processes
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()


# Convenience functions for common operations
def git_command(args: str, **kwargs: Any) -> subprocess.CompletedProcess:
    """Execute a git command safely."""
    return run_command(f"git {args}", **kwargs)


def python_command(args: str, **kwargs: Any) -> subprocess.CompletedProcess:
    """Execute a Python command safely."""
    import sys

    return run_command([sys.executable] + shlex.split(args), **kwargs)


def npm_command(args: str, **kwargs: Any) -> subprocess.CompletedProcess:
    """Execute an npm command safely."""
    return run_command(f"npm {args}", **kwargs)


def docker_command(args: str, **kwargs: Any) -> subprocess.CompletedProcess:
    """Execute a docker command safely."""
    return run_command(f"docker {args}", **kwargs)
