#!/bin/bash
# run_prod.sh

# Stop if there is an error
set -e

cd ..

source .venv/bin/activate

cd src

python chaddi.py >../logs/chaddi_$TIMESTAMP.log 2>&1 &
