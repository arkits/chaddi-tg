set -e

export PYTHONPATH=$PYTHONPATH:$(pwd)

# Create logs directory if it doesn't exist
mkdir -p logs

cd src

# Pipe output to both stdout and log file
# 2>&1 redirects stderr to stdout, tee writes to both file and terminal
uv run python chaddi.py 2>&1 | tee ../logs/chaddi.log
