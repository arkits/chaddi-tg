set -e

export PYTHONPATH=$PYTHONPATH:$(pwd)

cd src

uv run python chaddi.py
