#!/bin/bash
# run_prod.sh

# Stop if there is an error
set -e

# Go to chaddi home
cd /opt/software/chaddi-tg

source .env/bin/activate

cd src

python chaddi_bot.py