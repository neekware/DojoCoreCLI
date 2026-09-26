"""Shell completion management commands and completion definitions for dev commands."""

import subprocess
import sys
from pathlib import Path

import click

# ============================================================================
# Completion Management Commands
# ============================================================================


@click.group()
def completion() -> None:
    """Shell completion management"""
    pass


@completion.command(name="test")
def test_completion() -> None:
    """Test shell completion functionality"""
    click.echo("Running completion tests...")
    result = subprocess.run(
        ["python", "tests/commands/test_cmd_completion.py"],
        capture_output=True,
        text=True,
    )

    click.echo(result.stdout)
    if result.stderr:
        click.echo(result.stderr, err=True)

    if result.returncode != 0:
        click.echo("❌ Completion tests failed!", err=True)
        sys.exit(1)
    else:
        click.echo("✅ Completion tests passed!")
        sys.exit(0)


@completion.command()
def sync() -> None:
    """Sync shell completion with current CLI commands"""
    project_root = Path(__file__).parent.parent.parent.parent
    completion_path = project_root / "commands" / "autogen" / "completion.sh"

    # Files to check for changes
    command_files = [
        project_root / "commands" / "main.py",
        *list((project_root / "commands" / "subs").rglob("*.py")),
    ]

    # Check if regeneration is needed
    if completion_path.exists():
        completion_mtime = completion_path.stat().st_mtime
        needs_update = any(
            cmd_file.stat().st_mtime > completion_mtime
            for cmd_file in command_files
            if cmd_file.exists()
        )

        if not needs_update:
            click.echo("✓ Shell completion is already up to date")
            return
    else:
        click.echo("⚠️  Shell completion script not found")

    click.echo("🔄 Regenerating shell completion...")

    try:
        # Import here to avoid circular imports
        sys.path.insert(0, str(project_root))
        from commands.main import cli
        from commands.utils.completion import (
            generate_completion_script,
            get_command_info,
        )

        # Generate completion script
        cli_info = get_command_info(cli)
        completion_script = generate_completion_script(cli_info)

        # Add completion loaded marker
        completion_script = completion_script.replace(
            "# Auto-generated completion script for Dojo Core CLI",
            "# Auto-generated completion script for Dojo Core CLI\nexport _dojo_cli_completions_loaded=1",
        )

        # Write to file
        completion_path.write_text(completion_script)

        click.echo(f"✅ Generated {completion_path.relative_to(project_root)}")
        click.echo(
            "💡 Restart your shell or run 'source .venv/bin/activate' to load new completions"
        )

    except Exception as e:
        click.echo(f"❌ Failed to generate completion: {e}", err=True)
        sys.exit(1)


# ============================================================================
# Completion Definitions for Dev Commands
# ============================================================================


def get_dev_completions(ctx: object, args: list[str], incomplete: str) -> list[str]:
    """Get completions for dev commands.

    Args:
        ctx: Click context
        args: Already provided arguments
        incomplete: Current incomplete word

    Returns:
        List of completion suggestions
    """
    # Get the subcommand if specified
    if not args or args[0] == "dev":
        # Suggest dev subcommands
        commands = [
            "all",
            "format",
            "lint",
            "typecheck",
            "test",
            "precommit",
            "completion",
        ]
        return [cmd for cmd in commands if cmd.startswith(incomplete)]

    subcommand = args[0] if args else None

    # Delegate to specific completers
    if subcommand == "format":
        return complete_format(ctx, args[1:], incomplete)
    elif subcommand == "lint":
        return complete_lint(ctx, args[1:], incomplete)
    elif subcommand == "typecheck":
        return complete_typecheck(ctx, args[1:], incomplete)
    elif subcommand == "test":
        return complete_test(ctx, args[1:], incomplete)
    elif subcommand == "precommit":
        return complete_precommit(ctx, args[1:], incomplete)
    elif subcommand == "completion":
        return complete_completion_cmd(ctx, args[1:], incomplete)

    return []


def complete_all(ctx: object, args: list[str], incomplete: str) -> list[str]:
    """Completions for dev all command."""
    if incomplete.startswith("-"):
        options = ["--verbose", "--quiet", "--stop-on-error"]
        return [opt for opt in options if opt.startswith(incomplete)]
    return []


def complete_format(ctx: object, args: list[str], incomplete: str) -> list[str]:
    """Completions for dev format command."""
    if incomplete.startswith("-"):
        options = ["--check", "--diff", "--verbose"]
        return [opt for opt in options if opt.startswith(incomplete)]

    # Suggest Python files
    if not incomplete.startswith("-"):
        py_files = list(Path.cwd().glob("**/*.py"))
        suggestions = [str(f.relative_to(Path.cwd())) for f in py_files]
        return [s for s in suggestions if s.startswith(incomplete)][:10]  # Limit to 10

    return []


def complete_lint(ctx: object, args: list[str], incomplete: str) -> list[str]:
    """Completions for dev lint command."""
    if incomplete.startswith("-"):
        options = ["--fix", "--show-fixes", "--verbose"]
        return [opt for opt in options if opt.startswith(incomplete)]

    # Suggest Python files
    if not incomplete.startswith("-"):
        py_files = list(Path.cwd().glob("**/*.py"))
        suggestions = [str(f.relative_to(Path.cwd())) for f in py_files]
        return [s for s in suggestions if s.startswith(incomplete)][:10]

    return []


def complete_typecheck(ctx: object, args: list[str], incomplete: str) -> list[str]:
    """Completions for dev typecheck command."""
    if incomplete.startswith("-"):
        options = ["--strict", "--ignore-missing-imports", "--verbose"]
        return [opt for opt in options if opt.startswith(incomplete)]

    # Suggest directories
    if not incomplete.startswith("-"):
        dirs = [
            d for d in Path.cwd().iterdir() if d.is_dir() and not d.name.startswith(".")
        ]
        suggestions = [d.name for d in dirs]
        return [s for s in suggestions if s.startswith(incomplete)]

    return []


def complete_test(ctx: object, args: list[str], incomplete: str) -> list[str]:
    """Completions for dev test command."""
    if incomplete.startswith("-"):
        options = ["--coverage", "--verbose", "--failfast", "--parallel"]
        return [opt for opt in options if opt.startswith(incomplete)]

    # Suggest test files
    if not incomplete.startswith("-"):
        test_files = list(Path.cwd().glob("**/test_*.py"))
        suggestions = [str(f.relative_to(Path.cwd())) for f in test_files]
        return [s for s in suggestions if s.startswith(incomplete)][:10]

    return []


def complete_precommit(ctx: object, args: list[str], incomplete: str) -> list[str]:
    """Completions for dev precommit command."""
    if incomplete.startswith("-"):
        options = ["--fix", "--ci", "--verbose"]
        return [opt for opt in options if opt.startswith(incomplete)]
    return []


def complete_completion_cmd(ctx: object, args: list[str], incomplete: str) -> list[str]:
    """Completions for dev completion command."""
    # If no subcommand yet
    if not args:
        subcommands = ["test", "sync"]
        return [cmd for cmd in subcommands if cmd.startswith(incomplete)]

    return []


# Export completion registry for modular completion system
COMPLETIONS = {
    "dev": get_dev_completions,
    "all": complete_all,
    "format": complete_format,
    "lint": complete_lint,
    "typecheck": complete_typecheck,
    "test": complete_test,
    "precommit": complete_precommit,
    "completion": complete_completion_cmd,
}
