#!/bin/bash
# restart-prod.sh
#
# Restarts chaddi-tg by stopping it and letting chaddi.service start it again.

set -e

cd "$(dirname "$0")"

./kill-chaddi.sh
./wait-for-chaddi.sh
