#!/usr/bin/env python3
"""Test all CLI commands to ensure they work correctly.

This script tests all CLI commands (except expensive model operations).
It can be run with actual tests or in dry-run mode.
"""

import subprocess
import sys
from typing import Optional


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def run_command(cmd: str, dry_run: bool = False) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    if dry_run:
        print(f"{Colors.BLUE}[DRY-RUN] Would execute:{Colors.ENDC} {cmd}")
        return True, "Dry run - command not executed"

    try:
        # Ensure venv is activated
        activate_cmd = "source .venv/bin/activate && "
        full_cmd = activate_cmd + cmd

        result = subprocess.run(
            full_cmd, shell=True, capture_output=True, text=True, timeout=30
        )

        output = result.stdout + result.stderr
        success = result.returncode == 0

        if not success and "No such option: --dry-run" in output:
            # Try command without --dry-run if it's not supported
            cmd_without_dry = cmd.replace(" --dry-run", "").replace(" --dry", "")
            if cmd_without_dry != cmd:
                print(
                    f"{Colors.YELLOW}  Command doesn't support --dry-run, running without it{Colors.ENDC}"
                )
                return run_command(cmd_without_dry, dry_run=False)

        return success, output

    except subprocess.TimeoutExpired:
        return False, "Command timed out after 30 seconds"
    except Exception as e:
        return False, f"Error running command: {str(e)}"


def check_command(
    name: str, cmd: str, dry_run: bool = False, skip_reason: Optional[str] = None
) -> bool:
    """Test a single command and report results."""
    print(f"\n{Colors.BOLD}Testing: {name}{Colors.ENDC}")
    print(f"Command: {cmd}")

    if skip_reason:
        print(f"{Colors.YELLOW}SKIPPED:{Colors.ENDC} {skip_reason}")
        return True

    success, output = run_command(cmd, dry_run)

    if success:
        print(f"{Colors.GREEN}✓ PASSED{Colors.ENDC}")
        if "--help" not in cmd and not dry_run:
            # Show first few lines of output for non-help commands
            lines = output.strip().split("\n")[:3]
            for line in lines:
                print(f"  {line}")
            if len(output.strip().split("\n")) > 3:
                print("  ...")
    else:
        print(f"{Colors.RED}✗ FAILED{Colors.ENDC}")
        print(f"Output: {output[:500]}...")

    return success


def main() -> None:
    """Run all command tests."""
    dry_run = "--dry-run" in sys.argv or "--dry" in sys.argv

    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Testing Dojo Core CLI Commands{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"Mode: {'DRY RUN' if dry_run else 'ACTUAL EXECUTION'}")

    # Define all commands to test
    # Format: (test_name, command, skip_reason)
    commands = [
        # Basic commands
        ("Version", "cli version", None),
        ("Help", "cli --help", None),
        # Build commands
        ("Build Help", "cli build --help", None),
        ("Build All Help", "cli build all --help", None),
        ("Build Clean Help", "cli build clean --help", None),
        # Dev commands
        ("Dev Help", "cli dev --help", None),
        ("Dev Format Check", "cli dev format --check", None),
        ("Dev Lint", "cli dev lint", None),
        ("Dev Typecheck", "cli dev typecheck", None),
        ("Dev Test", "cli dev test", None),
        ("Dev All", "cli dev all", None),
        # Package commands
        ("Package Help", "cli package --help", None),
        ("Package Build Help", "cli package build --help", None),
        ("Package Dist Help", "cli package dist --help", None),
        # Project commands
        ("Proj Help", "cli proj --help", None),
        ("Proj Info", "cli proj info", None),
        ("Proj Size", "cli proj size", None),
        ("Proj Stats", "cli proj stats", None),
        # Release commands
        ("Release Help", "cli release --help", None),
        ("Release Create Help", "cli release create --help", None),
        ("Release Publish Help", "cli release publish --help", None),
    ]

    # Track results
    passed = 0
    failed = 0
    skipped = 0
    failed_commands = []

    # Run all tests
    for test_name, cmd, skip_reason in commands:
        if check_command(test_name, cmd, dry_run=False, skip_reason=skip_reason):
            if skip_reason:
                skipped += 1
            else:
                passed += 1
        else:
            failed += 1
            failed_commands.append((test_name, cmd))

    # Summary
    print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Test Summary{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.ENDC}")
    print(f"{Colors.RED}Failed: {failed}{Colors.ENDC}")
    print(f"{Colors.YELLOW}Skipped: {skipped}{Colors.ENDC}")

    if failed_commands:
        print(f"\n{Colors.RED}Failed Commands:{Colors.ENDC}")
        for name, cmd in failed_commands:
            print(f"  - {name}: {cmd}")

    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
