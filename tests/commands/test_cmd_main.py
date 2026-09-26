"""Basic tests for Dojo Core CLI"""

import subprocess
import sys
from pathlib import Path

from click.testing import CliRunner

from commands.main import cli


def test_cli_help() -> None:
    """Test that CLI help works"""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Dojo Core CLI" in result.output


def test_cli_version() -> None:
    """Test that CLI version command works"""
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "CLI version:" in result.output


def test_python_module_invocation() -> None:
    """Test that CLI can be invoked as python module"""
    result = subprocess.run(
        [sys.executable, "-m", "commands", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,  # Go up to project root
    )
    assert result.returncode == 0
    assert "Dojo Core CLI" in result.stdout
