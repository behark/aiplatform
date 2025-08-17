#!/usr/bin/env bash
# Small helper to run lint and tests locally
set -euo pipefail

python3 -m pip install --upgrade pip
if [ -f requirements.txt ]; then
  python3 -m pip install -r requirements.txt
fi
python3 -m pip install black isort ruff

# Run linters
black --check . || true
isort --check-only . || true
ruff check . || true

# Run tests
if [ -d tests ]; then
  python3 -m pytest -q
else
  echo "No tests detected, skipping pytest"
fi
