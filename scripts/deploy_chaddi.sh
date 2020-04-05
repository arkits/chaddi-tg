#!/bin/bash
# deploy_chaddi.sh

# Stop if there is an error
set -e

# Go to chaddi home
cd /opt/software/chaddi-tg

# Pull latest from Git
git pull

# Enable Virtualenv
source .env/bin/activate

# Update libs
pip install -r requirements.txt

cd scripts

# Kill existing bot
./kill.sh

# New run
./run_prod.sh

# Sanity check
ps aux | grep python