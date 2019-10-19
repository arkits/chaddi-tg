#!/bin/bash
# deploy_chaddi.sh

# cd to chaddi home
cd ~/chaddi-tg

# Stop if there is an error
set -e

# Pull latest from Git
git pull

# Enable Virtualenv
source src/.env/bin/activate

# Update libs
pip install -r requirements.txt
apt get-update

# Run the tests
pytest

# Kill existing bot
./kill_prod.sh

# New run
./run_prod.sh

# Sanity check
ps aux | grep python
