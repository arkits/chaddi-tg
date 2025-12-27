#!/bin/bash
# Stop if there is an error
set -e

./kill-chaddi.sh
sleep 5
./run-prod.sh
