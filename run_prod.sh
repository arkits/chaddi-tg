#!/bin/bash
# run_prod.sh

cd src
echo "Running bot_chaddi!"
nohup python3 bot_chaddi.py > ../chaddi.log 2>&1 & 