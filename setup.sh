#!/bin/bash
# Dojo Core CLI Bootstrap Script
# Sets up Python virtual environment and installs the cli

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
AUTO_YES=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -y|--yes)
            AUTO_YES=true
            shift
            ;;
        *)
            echo "Usage: $0 [-y|--yes]"
            echo "  -y, --yes    Auto-confirm all prompts"
            exit 1
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

ask() {
    if [[ "$AUTO_YES" == true ]]; then
        return 0
    fi

    local prompt="$1"
    local default="${2:-y}"

    echo -e "${BLUE}?${NC} $prompt (${default}/n): "
    read -r response
    response=${response:-$default}

    [[ "$response" =~ ^[Yy] ]]
}

# Check Python version
check_python() {
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD=python3
    elif command -v python >/dev/null 2>&1; then
        PYTHON_CMD=python
    else
        error "Python not found. Please install Python 3.9+"
    fi

    # Check version
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MAJOR" -eq 3 -a "$PYTHON_MINOR" -lt 9 ]; then
        error "Python 3.9+ required, found $PYTHON_VERSION"
    fi

    log "Found Python $PYTHON_VERSION"
}

# Create virtual environment
create_venv() {
    if [[ -d "$VENV_DIR" ]]; then
        if ask "Virtual environment already exists. Recreate?"; then
            log "Moving existing virtual environment to temp..."

            # Move to temp with unique name and remove in background
            local temp_dir="/tmp/corecli-venv-$$-$(date +%s)"
            mv "$VENV_DIR" "$temp_dir"

            # Remove in background
            (rm -rf "$temp_dir" 2>/dev/null) &

            log "Old virtual environment moved to temp, removal running in background"
        else
            log "Using existing virtual environment"
            return 0
        fi
    fi

    log "Creating virtual environment in .venv"
    sleep 1.0 && $PYTHON_CMD -m venv "$VENV_DIR"

    # Verify venv was created
    if [[ ! -f "$VENV_DIR/bin/activate" ]]; then
        error "Virtual environment creation failed"
    fi

    log "Virtual environment created"
}

# Install dependencies
install_deps() {
    log "Activating virtual environment and installing dependencies..."

    source "$VENV_DIR/bin/activate"
    # Upgrade pip quietly
    pip install --quiet --upgrade pip setuptools wheel

    # Configure pip to use temp directory for build artifacts
    export PIP_BUILD=/tmp/pip-build-$$
    export PIP_EGG_INFO_DIR="$VENV_DIR"

    # Install dependencies from tools/requirements.txt (NOT as a package)
    log "Installing dependencies..."

    # Extract main package names (not sub-dependencies)
    MAIN_PACKAGES=$(grep -E '^[^#]' "$SCRIPT_DIR/tools/requirements.txt" | cut -d'>' -f1 | cut -d'=' -f1 | xargs)
    echo "  Installing: $MAIN_PACKAGES"

    # Install with minimal output
    pip install --quiet -r "$SCRIPT_DIR/tools/requirements.txt"

    log "Dependencies installed successfully"

    # Install pre-commit hooks (only if in a git repo)
    if [[ -d ".git" ]]; then
        log "Installing pre-commit hooks..."
        pre-commit install >/dev/null 2>&1 || warn "Could not install pre-commit hooks (not a git repo?)"
        log "Pre-commit hooks installed"
    fi
}

# Install cli
install_cli() {
    log "Installing cli..."

    # Copy the wrapper script to venv only
    cp "$SCRIPT_DIR/commands/bin/cli-venv" "$VENV_DIR/bin/cli"
    chmod +x "$VENV_DIR/bin/cli"

    log "cli installed to venv"

    # Generate completion script (optional, may fail in CI)
    log "Generating shell completion..."
    
    # Ensure autogen directory exists
    mkdir -p "$SCRIPT_DIR/commands/autogen"

    # Try to generate completion, but don't fail if it doesn't work
    if "$VENV_DIR/bin/python" -c "
from pathlib import Path
import sys
sys.path.insert(0, '$SCRIPT_DIR')
try:
    from commands.utils.completion import generate_completion_script, get_command_info
    from commands.main import cli
    
    completion_path = Path('$SCRIPT_DIR/commands/autogen/completion.sh')
    completion_path.parent.mkdir(parents=True, exist_ok=True)
    cli_info = get_command_info(cli)
    completion_script = generate_completion_script(cli_info)
    
    # Add completion loaded marker
    completion_script = completion_script.replace(
        '# Auto-generated completion script for Dojo Core CLI',
        '# Auto-generated completion script for Dojo Core CLI\\nexport _dojo_cli_completions_loaded=1'
    )
    
    completion_path.write_text(completion_script)
    print(f'✓ Generated {completion_path}')
except Exception as e:
    print(f'⚠ Could not generate completion: {e}')
    sys.exit(1)
" 2>/dev/null; then
        log "Shell completion generated"
    else
        warn "Could not generate shell completion (this is normal in CI)"
    fi

    # Add completion sourcing to activate script
    if [[ -f "$SCRIPT_DIR/commands/completion.sh" ]]; then
        # Add to the end of activate script with proper safeguards
        if ! grep -q "source.*commands/completion.sh" "$VENV_DIR/bin/activate"; then
            echo "" >> "$VENV_DIR/bin/activate"
            echo "# Auto-load CLI completion (only in interactive shells)" >> "$VENV_DIR/bin/activate"
            echo "if [[ -f \"$SCRIPT_DIR/commands/completion.sh\" ]] && [[ \$- == *i* ]]; then" >> "$VENV_DIR/bin/activate"
            echo "    source \"$SCRIPT_DIR/commands/completion.sh\" 2>/dev/null || true" >> "$VENV_DIR/bin/activate"
            echo "fi" >> "$VENV_DIR/bin/activate"
        fi
        log "Shell completion configured"
    fi
}


# Main execution
main() {
    echo -e "${BLUE}🚀 Dojo Core CLI Bootstrap${NC}"
    echo "Setting up Python environment for Dojo Core CLI..."
    echo

    # Check if already in a virtual environment
    if [ -n "$VIRTUAL_ENV" ]; then
        # Show a friendlier path if it's our project's venv
        VENV_DISPLAY="$VIRTUAL_ENV"
        if [[ "$VIRTUAL_ENV" == "$SCRIPT_DIR/.venv" ]]; then
            VENV_DISPLAY=".venv (this project)"
        elif [[ "$VIRTUAL_ENV" == *"/.venv" ]]; then
            # Show just the parent directory name and .venv
            PARENT_DIR=$(basename "$(dirname "$VIRTUAL_ENV")")
            VENV_DISPLAY="$PARENT_DIR/.venv"
        fi
        error "A virtual environment is currently active: $VENV_DISPLAY\n\nPlease deactivate it first by running:\n  deactivate\n\nThen run ./setup.sh again."
    fi

    check_python
    create_venv
    install_deps
    install_cli

    echo
    log "Bootstrap complete!"
    echo
    echo -e "${GREEN}✅ Setup complete!${NC}"
    echo
    echo -e "${BLUE}To use the CLI:${NC}"
    echo "  source .venv/bin/activate"
    echo "  cli --help"
}

main "$@"
