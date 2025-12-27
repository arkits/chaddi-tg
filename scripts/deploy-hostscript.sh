#!/bin/bash
# deploy-hostscript.sh

set -e

echo ">>> hostscript running as $(whoami)@$(hostname)"
echo ">>> deploying chaddi-tg to $(pwd)"
echo ""

cd /opt/software/

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

    echo ">>> sleeping for 5 seconds"
    sleep 5
    echo ">>> done sleeping"

    echo ">>> starting new chaddi-tg"
    ./run-prod.sh

    PID=$(ps -eaf | grep "chaddi.py" | grep -v grep | awk '{print $2}')
    echo ">>> PID of chaddi-tg: $PID"

    PORT=5100
    PID_PORT=$(lsof -t -i:$PORT)
    echo ">>> PID of server on port $PORT: $PID_PORT"

    echo ">>> done starting new chaddi-tg"

else

    echo ">>> chaddi-tg was not present!"
    exit 4
fi
