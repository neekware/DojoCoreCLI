"""Project statistics command"""

import os
from pathlib import Path

import click

from commands.utils.paths import get_paths


@click.command()
def stats() -> None:
    """Show detailed statistics"""
    project_root = get_paths().root

    try:
        # Count files by extension
        file_counts: dict[str, int] = {}
        total_files = 0
        total_lines = 0

        # Walk through all files
        for root, dirs, files in os.walk(project_root):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d
                not in [
                    "node_modules",
                    "__pycache__",
                    "target",
                    "dist",
                    "cache",
                    "release",
                    ".venv",
                ]
            ]

            for file in files:
                if file.startswith("."):
                    continue

                total_files += 1
                ext = Path(file).suffix or "no extension"
                file_counts[ext] = file_counts.get(ext, 0) + 1

                # Try to count lines for text files
                if ext in [
                    ".py",
                    ".js",
                    ".ts",
                    ".rs",
                    ".go",
                    ".c",
                    ".cpp",
                    ".h",
                    ".java",
                    ".rb",
                    ".sh",
                    ".md",
                    ".txt",
                    ".toml",
                    ".yaml",
                    ".yml",
                    ".json",
                ]:
                    try:
                        file_path = os.path.join(root, file)
                        with open(file_path, encoding="utf-8", errors="ignore") as f:
                            lines = len(f.readlines())
                            total_lines += lines
                    except Exception:
                        pass

        # Get directory count
        dir_count = sum(
            1
            for _, dirs, _ in os.walk(project_root)
            for d in dirs
            if d.startswith(".")
            or d
            not in [
                "node_modules",
                "__pycache__",
                "target",
                "dist",
                "cache",
                "release",
                ".venv",
            ]
        )

        # Average lines per file
        avg_lines = total_lines // total_files

        # Show results
        click.echo(f"Total files: {total_files}")
        click.echo(f"Total directories: {dir_count}")
        click.echo(f"Total lines of code: {total_lines:,}")
        click.echo(f"Average lines per file: {avg_lines}")
        click.echo("\nTop 10 file types:")

        # Sort and show top 10 file types
        sorted_types = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        for ext, count in sorted_types:
            click.echo(f"  {ext}: {count}")

    except Exception as e:
        click.echo(f"Error gathering statistics: {e}", err=True)
