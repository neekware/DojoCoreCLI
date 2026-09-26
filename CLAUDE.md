# CLAUDE.md - Project-Specific Instructions for Dojo Core CLI

## Quick Start

```bash
# Initial setup
./setup.sh

# Activate environment (required before using CLI)
source .venv/bin/activate

# Use the CLI
cli --help
```

## CLI Commands Reference

### Development Tools (`cli dev`)
- `cli dev format` - Format code with Black
- `cli dev lint` - Lint with Ruff
- `cli dev typecheck` - Type check with MyPy
- `cli dev test` - Run tests with pytest
- `cli dev all` - Run all checks
- `cli dev precommit` - Run pre-commit hooks

### Project Management (`cli proj`)
- `cli proj info` - Show git status and project info
- `cli proj size` - Show repository size
- `cli proj stats` - Show detailed statistics

### Build Commands (`cli build`)
- `cli build all` - Build all targets (placeholder)
- `cli build clean` - Clean build artifacts (placeholder)
- `cli build component` - Build specific component (placeholder)

### Package Commands (`cli package`)
- `cli package build` - Build packages (placeholder)
- `cli package dist` - Distribute packages (placeholder)
- `cli package list` - List packages (placeholder)

### Release Commands (`cli release`)
- `cli release create` - Create releases (placeholder)
- `cli release publish` - Publish releases (placeholder)
- `cli release list` - List releases (placeholder)

## Development Rules

### Python Type Annotations (Required)
```python
# Good - with type annotations
from typing import Dict, List, Optional
from pathlib import Path

def process_data(input_file: Path, max_size: int = 100) -> Dict[str, Any]:
    results: List[str] = []
    ...

# Bad - missing type annotations
def process_data(input_file, max_size=100):  # Don't do this!
    ...
```

### Code Quality Standards
- All code must pass `black` formatting
- All code must pass `ruff` linting
- All code must pass `mypy` type checking
- Pre-commit hooks enforce these standards automatically

### Architecture Principles

1. **Modular Design**: Each command group in `commands/subs/`
2. **Separation of Concerns**: One responsibility per module
3. **Clean Interfaces**: Commands handle CLI, logic separate
4. **Type Safety**: Full type annotations everywhere

## Git Safety Rules

**ALWAYS ask before:**
- Creating commits
- Pushing to remote
- Any destructive operations
- Modifying history

**NEVER run without permission:**
- `git reset --hard`
- `git push --force`
- `git clean -xdf`
- `rm -rf`

## Project Customization

To customize this template for your project:

1. Edit `commands/config.py`:
   ```python
   PROJECT_NAME = "YourProject"  # Your project name
   PROJECT_DESCRIPTION = "Your description"
   ```

2. Update `commands/__init__.py` for version:
   ```python
   __version__ = "1.0.0"  # Your version
   ```

3. Modify placeholder commands in `commands/subs/` as needed

## Visual Accessibility Guidelines

When creating diagrams or visualizations:

### Color Schemes
- **Success**: `#2E7D32` (dark green) or `#C8E6C9` (light green with black text)
- **Warning**: `#F57C00` (dark orange) or `#FFE0B2` (light orange with black text)
- **Error**: `#C62828` (dark red) or `#FFCDD2` (light red with black text)
- **Info**: `#1565C0` (dark blue) or `#BBDEFB` (light blue with black text)

### Requirements
- Minimum contrast ratio 4.5:1 (WCAG AA)
- Avoid red/green combinations
- Include text labels with colors
- Use patterns as secondary indicators

## Testing

```bash
# Run all tests
cli dev test

# Run specific test file
pytest commands/tests/test_main.py

# Run with coverage
pytest --cov=commands
```

## Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. To run manually:

```bash
cli dev precommit        # Check staged files
cli dev precommit --fix  # Auto-fix issues
cli dev precommit --ci   # Check all files
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure virtual environment is activated
2. **Command not found**: Run `./setup.sh` and activate venv
3. **Type errors**: Run `cli dev typecheck` to identify issues
4. **Format issues**: Run `cli dev format` to auto-fix

### Debug Mode

Run any command with `--debug` for verbose output:
```bash
cli --debug [command]
```