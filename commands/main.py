#!/usr/bin/env python3
"""Dojo Core CLI - Main entry point"""

import sys

import click

from commands import __version__
from commands.config import CLI_NAME
from commands.subs.build import build
from commands.subs.dev import dev
from commands.subs.package import package
from commands.subs.proj import proj
from commands.subs.release import release


@click.group(epilog="Maintained by Dojo ⛩️  https://heydojo.ai")
@click.version_option(version=__version__, prog_name="cli")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    """Dojo Core CLI - A modular command-line interface

    Examples:
      cli proj info               # Show project information
      cli proj size               # Show repository size
      cli proj stats              # Show detailed statistics

      cli dev format              # Format code with black
      cli dev lint                # Lint code with ruff
      cli dev all                 # Run all checks
    """
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug


# Add a version command that shows version info
@cli.command()
def version() -> None:
    """Show version information"""
    click.echo(f"{CLI_NAME} version: {__version__}")
    click.echo("Maintained by Dojo ⛩️  https://heydojo.ai")


# Add command groups - sorted alphabetically for consistency
cli.add_command(build)
cli.add_command(dev)
cli.add_command(package)
cli.add_command(proj)
cli.add_command(release)


def main() -> None:
    """Main entry point"""
    try:
        cli(prog_name="cli")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
