#!/usr/bin/env python3
"""Test completion functionality"""

import sys
from pathlib import Path

# Add parent dir to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from commands.main import cli  # noqa: E402
from commands.utils.completion import (  # noqa: E402
    generate_completion_script,
    get_command_info,
)


def test_completion_generation() -> None:
    """Test that completion script can be generated"""
    # Get CLI info
    cli_info = get_command_info(cli)
    assert cli_info is not None
    assert "name" in cli_info
    assert "subcommands" in cli_info

    # Generate completion script
    script = generate_completion_script(cli_info)
    assert script is not None
    assert len(script) > 0
    assert "#!/bin/bash" in script
    assert "_dojo_cli_completions" in script


def test_command_structure() -> None:
    """Test that command structure is properly extracted"""
    cli_info = get_command_info(cli)

    # Check main commands exist
    expected_commands = {"build", "dev", "package", "proj", "release"}
    actual_commands = set(cli_info["subcommands"].keys())

    assert expected_commands.issubset(
        actual_commands
    ), f"Missing commands: {expected_commands - actual_commands}"

    # Check dev subcommands
    dev_info = cli_info["subcommands"]["dev"]
    dev_subcommands = set(dev_info["subcommands"].keys())
    expected_dev = {"format", "lint", "typecheck", "test", "all", "precommit"}

    assert expected_dev.issubset(
        dev_subcommands
    ), f"Missing dev commands: {expected_dev - dev_subcommands}"


# For running as a standalone script
def run_tests() -> bool:
    """Run tests when called as a script"""
    success = True
    try:
        test_completion_generation()
        print("✅ Completion generation test passed")
    except Exception as e:
        print(f"❌ Completion generation test failed: {e}")
        success = False

    try:
        test_command_structure()
        print("✅ Command structure test passed")
    except Exception as e:
        print(f"❌ Command structure test failed: {e}")
        success = False

    return success


if __name__ == "__main__":
    if run_tests():
        print("\n✅ All completion tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some completion tests failed")
        sys.exit(1)
