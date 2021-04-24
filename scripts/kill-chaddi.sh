#!/bin/bash
# kill-chaddi.sh

PID=$(ps -eaf | grep "python chaddi.py" | grep -v grep | awk '{print $2}')

if [[ "" != "$PID" ]]; then
    echo ">>> killing PID - $PID"
    kill -9 $PID
fi

echo ">>> checking processes"
ps aux | grep "python chaddi.py"
echo ""
