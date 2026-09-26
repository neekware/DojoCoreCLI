#!/bin/bash
# Git-tracked completion wrapper for Dojo Core CLI
#
# This stable wrapper handles shell completion hookup logic and sources
# the auto-generated completion functions. It provides:
# - Universal shell support (bash + zsh)
# - Path resolution fallbacks
# - Development reload functionality
# - Interactive shell detection
#
# The wrapper sources: commands/autogen/completion.sh (auto-generated, git-ignored)

# Function to force reload completion (useful for development)
reload_cli_completion() {
    # Setup completion based on shell type
    if [[ -n "$ZSH_VERSION" ]]; then
        # zsh: enable bash compatibility
        autoload -U +X bashcompinit && bashcompinit
    elif [[ -n "$BASH_VERSION" ]]; then
        # bash: completion should work natively
        true
    fi

    # Clear existing completion
    complete -r cli 2>/dev/null
    unset -f _cli_completion 2>/dev/null
    unset -f _corecli_completions 2>/dev/null

    # Get the directory where this script is located
    local SCRIPT_DIR
    if [[ -n "${BASH_SOURCE[0]}" ]]; then
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    else
        # Fallback: assume we're in project root
        SCRIPT_DIR="$(pwd)/commands"
    fi

    # Source the auto-generated completion script
    local AUTOGEN_COMPLETION="$SCRIPT_DIR/autogen/completion.sh"

    if [[ -f "$AUTOGEN_COMPLETION" ]]; then
        source "$AUTOGEN_COMPLETION" 2>/dev/null || true
        export _CORECLI_COMPLETION_LOADED="$(date)"
        echo "✅ CLI completion reloaded ($([[ -n "$ZSH_VERSION" ]] && echo "zsh" || echo "bash"))"
    else
        echo "❌ Completion script not found: $AUTOGEN_COMPLETION"
        echo "   Run 'cli dev completion sync' to generate it"
    fi
}

# Only enable completion for interactive shells
if [[ $- == *i* ]]; then
    # Get the directory where this script is located
    if [[ -n "${BASH_SOURCE[0]}" ]]; then
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    else
        # Fallback: assume we're in project root
        SCRIPT_DIR="$(pwd)/commands"
    fi

    # Source the auto-generated completion script
    AUTOGEN_COMPLETION="$SCRIPT_DIR/autogen/completion.sh"

    if [[ -f "$AUTOGEN_COMPLETION" ]]; then
        # Setup completion based on shell type
        if [[ -n "$ZSH_VERSION" ]]; then
            # zsh: enable bash compatibility
            autoload -U +X bashcompinit && bashcompinit
        elif [[ -n "$BASH_VERSION" ]]; then
            # bash: completion should work natively
            true
        fi

        # Clear any existing completion first
        complete -r cli 2>/dev/null
        unset -f _cli_completion 2>/dev/null
        unset -f _corecli_completions 2>/dev/null

        source "$AUTOGEN_COMPLETION" 2>/dev/null || true
        export _CORECLI_COMPLETION_LOADED="$(date)"
    fi
fi
