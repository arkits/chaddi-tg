#!/bin/bash
# deploy-hostscript.sh

set -e

echo ">>> hostscript running as $(whoami)@$(hostname)"
echo ">>> deploying chaddi-tg to $(pwd)"

if [ -d "chaddi-tg" ]; then
    echo ">>> chaddi-tg was present"
    cd chaddi-tg
    git pull
    cd scripts
    echo ">>> triggering kill-chaddi.sh"
    # ./kill-chaddi.sh
    echo ">>> starting new chaddi"
    ./run-prod.sh
else
    echo ">>> chaddi-tg was not present!"
    exit 4
fi
