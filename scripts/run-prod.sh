#!/bin/bash
# run-prod.sh

# Stop if there is an error
set -e

cd ..

export PYTHONPATH=$PYTHONPATH:$(pwd)

# Dependencies are now managed by uv via pyproject.toml
# Install/sync dependencies with: uv sync

cd src

uv run python chaddi.py >../logs/chaddi.log 2>&1 &
