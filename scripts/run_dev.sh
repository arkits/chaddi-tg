#!/bin/bash
# run_prod.sh

cd ..

source .env/bin/activate

cd src

python chaddi_bot.py