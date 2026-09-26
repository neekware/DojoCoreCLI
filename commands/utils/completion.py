#!/usr/bin/env python3
"""Generate shell completion script from CLI structure with modular completion support"""

import importlib
from pathlib import Path
from typing import Any, Callable, Optional

import click


def get_command_info(cmd: click.Command) -> dict[str, Any]:
    """Extract command info including options and subcommands"""
    info: dict[str, Any] = {
        "name": cmd.name,
        "help": cmd.help or "",
        "options": [],
        "subcommands": {},
    }

    # Get options
    for param in cmd.params:
        if isinstance(param, click.Option):
            opt_info = {
                "names": param.opts,
                "type": (
                    param.type.name if hasattr(param.type, "name") else str(param.type)
                ),
                "choices": [],
            }

            # Get choices if it's a Choice type
            if isinstance(param.type, click.Choice):
                opt_info["choices"] = list(param.type.choices)

            info["options"].append(opt_info)

    # Get subcommands if it's a group
    if isinstance(cmd, click.Group):
        for name, subcmd in cmd.commands.items():
            info["subcommands"][name] = get_command_info(subcmd)

    return info


def generate_completion_case(cmd_info: dict[str, Any], depth: int = 0) -> str:
    """Generate a completion case for a command and its subcommands recursively"""
    indent = "    " * (depth + 3)
    case_content = ""

    # Handle options
    if cmd_info["options"]:
        case_content += f'{indent}if [[ "${{prev}}" == --* ]]; then\n'
        case_content += f'{indent}    case "${{prev}}" in\n'

        for opt in cmd_info["options"]:
            if opt["choices"]:
                for opt_name in opt["names"]:
                    if opt_name.startswith("--"):
                        choices = " ".join(opt["choices"])
                        case_content += f"{indent}        {opt_name})\n"
                        case_content += f'{indent}            COMPREPLY=($(compgen -W "{choices}" -- "${{cur}}"))\n'
                        case_content += f"{indent}            return 0\n"
                        case_content += f"{indent}            ;;\n"

        case_content += f"{indent}    esac\n"
        case_content += f"{indent}fi\n\n"

    # Handle subcommands
    if cmd_info["subcommands"]:
        subcommands = " ".join(cmd_info["subcommands"].keys())

        # Generate option list for this level
        options = []
        for opt in cmd_info["options"]:
            options.extend(opt["names"])
        options_str = " ".join(options) if options else ""

        case_content += f"{indent}# Check for subcommand at this level\n"
        case_content += f"{indent}local subcmd=''\n"
        case_content += f"{indent}local subcommands='{subcommands}'\n"
        case_content += f"{indent}local idx=$((cmd_idx + {depth}))\n"
        case_content += f"{indent}for ((i=idx+1; i < ${{cword}}; i++)); do\n"
        case_content += f'{indent}    if [[ "${{words[i]}}" != -* ]] && [[ " ${{subcommands}} " == *" ${{words[i]}} "* ]]; then\n'
        case_content += f'{indent}        subcmd="${{words[i]}}"\n'
        case_content += f"{indent}        break\n"
        case_content += f"{indent}    fi\n"
        case_content += f"{indent}done\n\n"

        case_content += f'{indent}if [[ -n "${{subcmd}}" ]]; then\n'
        case_content += f'{indent}    case "${{subcmd}}" in\n'

        # Recursively handle each subcommand
        for subcmd_name, subcmd_info in cmd_info["subcommands"].items():
            case_content += f"{indent}        {subcmd_name})\n"
            subcmd_case = generate_completion_case(subcmd_info, depth + 1)
            # Add the subcmd case content with proper indentation
            for line in subcmd_case.splitlines():
                if line:
                    case_content += f"{indent}            {line}\n"
            case_content += f"{indent}            ;;\n"

        case_content += f"{indent}    esac\n"
        case_content += f"{indent}else\n"
        case_content += (
            f"{indent}    # No subcommand yet, offer subcommands and options\n"
        )
        case_content += f'{indent}    if [[ "${{cur}}" == -* ]]; then\n'
        if options_str:
            # Add logic to filter out already used options
            case_content += f"{indent}        # Filter out already used options\n"
            case_content += f'{indent}        local available_opts=" {options_str} "\n'
            case_content += f'{indent}        for word in "${{words[@]}}"; do\n'
            case_content += f'{indent}            if [[ "$word" == -* ]] && [[ "$word" != "${{cur}}" ]]; then\n'
            case_content += f'{indent}                available_opts="${{available_opts// $word / }}"\n'
            case_content += f"{indent}            fi\n"
            case_content += f"{indent}        done\n"
            case_content += (
                f"{indent}        # Trim spaces and offer remaining options\n"
            )
            case_content += f'{indent}        available_opts="${{available_opts## }}"\n'
            case_content += f'{indent}        available_opts="${{available_opts%% }}"\n'
            case_content += f'{indent}        COMPREPLY=($(compgen -W "${{available_opts}}" -- "${{cur}}"))\n'
        else:
            case_content += f"{indent}        COMPREPLY=()\n"
        case_content += f"{indent}    else\n"
        case_content += f'{indent}        COMPREPLY=($(compgen -W "${{subcommands}}" -- "${{cur}}"))\n'
        case_content += f"{indent}    fi\n"
        case_content += f"{indent}fi\n"
    else:
        # No subcommands, just complete options
        options = []
        for opt in cmd_info["options"]:
            options.extend(opt["names"])
        if options:
            options_str = " ".join(options)
            case_content += f'{indent}if [[ "${{cur}}" == -* ]]; then\n'
            case_content += f"{indent}    # User typed -, show matching options\n"
            # Add logic to filter out already used options
            case_content += f"{indent}    # Filter out already used options\n"
            case_content += f'{indent}    local available_opts=" {options_str} "\n'
            case_content += f'{indent}    for word in "${{words[@]}}"; do\n'
            case_content += f'{indent}        if [[ "$word" == --* ]] && [[ "$word" != "${{cur}}" ]]; then\n'
            case_content += (
                f'{indent}            available_opts="${{available_opts// $word / }}"\n'
            )
            case_content += f"{indent}        fi\n"
            case_content += f"{indent}    done\n"
            case_content += f"{indent}    # Trim spaces and offer remaining options\n"
            case_content += f'{indent}    available_opts="${{available_opts## }}"\n'
            case_content += f'{indent}    available_opts="${{available_opts%% }}"\n'
            case_content += f'{indent}    COMPREPLY=($(compgen -W "${{available_opts}}" -- "${{cur}}"))\n'
            case_content += f'{indent}elif [[ -z "${{cur}}" ]]; then\n'
            case_content += f"{indent}    # Empty current word, show filtered options\n"
            # Add logic to filter out already used options
            case_content += f"{indent}    # Filter out already used options\n"
            case_content += f'{indent}    local available_opts=" {options_str} "\n'
            case_content += f'{indent}    for word in "${{words[@]}}"; do\n'
            case_content += f'{indent}        if [[ "$word" == --* ]] && [[ "$word" != "${{cur}}" ]]; then\n'
            case_content += (
                f'{indent}            available_opts="${{available_opts// $word / }}"\n'
            )
            case_content += f"{indent}        fi\n"
            case_content += f"{indent}    done\n"
            case_content += f"{indent}    # Trim spaces and offer remaining options\n"
            case_content += f'{indent}    available_opts="${{available_opts## }}"\n'
            case_content += f'{indent}    available_opts="${{available_opts%% }}"\n'
            case_content += (
                f'{indent}    COMPREPLY=($(compgen -W "${{available_opts}}" -- ""))\n'
            )
            case_content += f"{indent}fi\n"

    return case_content.rstrip()


def generate_completion_script(cli_info: dict[str, Any]) -> str:
    """Generate bash/zsh completion script from CLI info"""

    # First, collect all commands and their structures
    all_commands = list(cli_info["subcommands"].keys())

    script = f"""#!/bin/bash
# Auto-generated completion script for Dojo Core CLI
export _dojo_cli_completions_loaded=1

_dojo_cli_completions() {{
    local cur prev words cword
    if [[ -n "$ZSH_VERSION" ]]; then
        cur="${{COMP_WORDS[COMP_CWORD]}}"
        prev="${{COMP_WORDS[COMP_CWORD-1]}}"
        words=("${{COMP_WORDS[@]}}")
        cword=$COMP_CWORD
    else
        if type _get_comp_words_by_ref &>/dev/null; then
            _get_comp_words_by_ref -n : cur prev words cword
        else
            cur="${{COMP_WORDS[COMP_CWORD]}}"
            prev="${{COMP_WORDS[COMP_CWORD-1]}}"
            words=("${{COMP_WORDS[@]}}")
            cword=$COMP_CWORD
        fi
    fi

    # Main commands
    local commands="{" ".join(all_commands)}"

    if [[ ${{cword}} -eq 1 ]]; then
        COMPREPLY=($(compgen -W "${{commands}}" -- "${{cur}}"))
        return 0
    fi

    # Find the main command
    local cmd=""
    local cmd_idx=1
    for ((i=1; i < ${{cword}}; i++)); do
        if [[ "${{words[i]}}" != -* ]]; then
            cmd="${{words[i]}}"
            cmd_idx=$i
            break
        fi
    done

    # Complete based on command
    case "${{cmd}}" in
"""

    # Generate cases for each command
    for cmd_name, cmd_info in cli_info["subcommands"].items():
        script += f"        {cmd_name})\n"
        # Use the recursive function to generate the case content
        case_content = generate_completion_case(cmd_info)
        script += case_content
        script += "\n            ;;\n"

    script += """        *)
            if [[ "${{cur}}" == -* ]]; then
                COMPREPLY=($(compgen -W "--help" -- "${{cur}}"))
            fi
            ;;
    esac
}}

# Only enable completion for interactive shells
if [[ $- == *i* ]]; then
    # For bash
    if [[ -n "$BASH_VERSION" ]]; then
        complete -F _dojo_cli_completions cli
    fi

    # For zsh
    if [[ -n "$ZSH_VERSION" ]]; then
        autoload -U +X bashcompinit && bashcompinit
        complete -F _dojo_cli_completions cli
    fi
fi
"""

    return script


# Modular completion support
class ModularCompletionRegistry:
    """Registry for modular completion functions from subcommand modules."""

    def __init__(self) -> None:
        """Initialize the completion registry."""
        self.completions: dict[str, Callable] = {}
        self._load_completion_modules()

    def _load_completion_modules(self) -> None:
        """Load completion definitions from all subcommand modules."""
        # Get the subs directory
        subs_dir = Path(__file__).parent.parent / "subs"

        # Iterate through each subcommand directory
        for subdir in subs_dir.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("_"):
                # Check for completion.py
                if (subdir / "completion.py").exists():
                    try:
                        # Import the completion module
                        module_name = f"commands.subs.{subdir.name}.completion"
                        module = importlib.import_module(module_name)

                        # Get the COMPLETIONS registry if it exists
                        if hasattr(module, "COMPLETIONS"):
                            completions = module.COMPLETIONS
                            for cmd_name, completer in completions.items():
                                # Register with full path for nested commands
                                self.completions[f"{subdir.name}.{cmd_name}"] = (
                                    completer
                                )
                    except ImportError:
                        # Silently skip if module can't be imported
                        pass

    def get_completions(
        self, command_path: str, ctx: object, args: list[str], incomplete: str
    ) -> list[str]:
        """Get completions for a given command path.

        Args:
            command_path: Dot-separated command path (e.g., "dev.format")
            ctx: Click context
            args: Already provided arguments
            incomplete: Current incomplete word

        Returns:
            List of completion suggestions
        """
        # Try to find a completer for this command path
        if command_path in self.completions:
            completer = self.completions[command_path]
            result = completer(ctx, args, incomplete)
            return result if isinstance(result, list) else []

        # Try parent command
        parts = command_path.split(".")
        if len(parts) > 1:
            parent_path = ".".join(parts[:-1])
            if parent_path in self.completions:
                completer = self.completions[parent_path]
                result = completer(ctx, args, incomplete)
                return result if isinstance(result, list) else []

        return []

    def get_available_commands(self) -> list[str]:
        """Get list of all registered command paths.

        Returns:
            List of command paths with completions
        """
        return sorted(self.completions.keys())


# Global registry instance
_registry: Optional[ModularCompletionRegistry] = None


def get_completion_registry() -> ModularCompletionRegistry:
    """Get or create the global completion registry.

    Returns:
        The completion registry instance
    """
    global _registry
    if _registry is None:
        _registry = ModularCompletionRegistry()
    return _registry


def get_modular_completions(ctx: object, args: list[str], incomplete: str) -> list[str]:
    """Main entry point for getting modular completions.

    Args:
        ctx: Click context
        args: Already provided arguments
        incomplete: Current incomplete word

    Returns:
        List of completion suggestions
    """
    registry = get_completion_registry()

    # Build command path from args
    command_path = ".".join(args) if args else ""

    # Get completions from registry
    completions = registry.get_completions(command_path, ctx, args, incomplete)

    return completions


# This module is meant to be imported, not run directly
# Use it from commands.main.py in the enable_completion command
