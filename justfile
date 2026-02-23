# like so we"ll get PS on win -vs- bash for all others
set windows-shell := ["powershell", "-Command"]
set shell := ["bash", "-cu"]

[group('dev')]
lint:
    echo "linting..."
    uv run ruff check .
