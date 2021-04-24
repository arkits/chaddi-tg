#!/bin/bash
# run-prod.sh

# Stop if there is an error
set -e

cd ..

source .venv/bin/activate

export PYTHONPATH=$PYTHONPATH:$(pwd)

cd src

TIMESTAMP=$(date +"%s")

python chaddi.py >../logs/chaddi_$TIMESTAMP.log 2>&1 &
