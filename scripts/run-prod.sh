#!/bin/bash
# run-prod.sh

# Stop if there is an error
set -e

cd ..

source .venv/bin/activate

export PYTHONPATH=$PYTHONPATH:$(pwd)

echo ">>> pip installing"
pip install -r requirements.txt
echo ""

cd src

TIMESTAMP=$(date +"%s")
FILENAME="chaddi_$TIMESTAMP.log"
echo ">>> logging to file ./logs/$FILENAME"
echo ""

python chaddi.py >../logs/chaddi_$TIMESTAMP.log 2>&1 &
