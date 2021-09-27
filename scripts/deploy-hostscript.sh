#!/bin/bash
# deploy-hostscript.sh

set -e

echo ">>> hostscript running as $(whoami)@$(hostname)"
echo ">>> deploying chaddi-tg to $(pwd)"
echo ""

cd /home/arkits/software

if [ -d "chaddi-tg" ]; then

    echo ">>> chaddi-tg was present"
    cd chaddi-tg
    echo ""

    echo ">>> git pulling latest from remote"
    git pull
    echo ""

    echo ">>> triggering kill-chaddi.sh"
    cd scripts
    ./kill-chaddi.sh

    echo ">>> starting new chaddi"
    ./run-prod.sh
    echo ""

    sleep 5
    echo ">>> checking processes"
    ps aux | grep "python chaddi.py"

else

    echo ">>> chaddi-tg was not present!"
    exit 4
fi
