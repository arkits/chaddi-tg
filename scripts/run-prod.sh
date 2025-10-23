#!/bin/bash
# run-prod.sh

# Stop if there is an error
set -e

cd ..

source .venv/bin/activate

export PYTHONPATH=$PYTHONPATH:$(pwd)

# echo ">>> pip installing"
# pip install -r requirements.txt
# echo ""

cd src

python chaddi.py >../logs/chaddi.log 2>&1 &
