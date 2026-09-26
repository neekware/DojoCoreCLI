"""Central configuration for Dojo Core CLI"""

from commands import __version__

# Project metadata
PROJECT_NAME = "MyProject"  # Change this to your project name
PROJECT_DESCRIPTION = (
    "A Python CLI application"  # Change this to your project description
)
CLI_NAME = "Dojo Core CLI"
CLI_COMMAND = "cli"

__all__ = [
    "PROJECT_NAME",
    "PROJECT_DESCRIPTION",
    "CLI_NAME",
    "CLI_COMMAND",
    "__version__",
]
