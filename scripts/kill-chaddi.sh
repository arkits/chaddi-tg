#!/bin/bash
# kill-chaddi.sh

PID=$(ps -eaf | grep "chaddi.py" | grep -v grep | awk '{print $2}')

if [[ "" != "$PID" ]]; then
    echo ">>> killing PID - $PID"
    kill -9 $PID
fi

echo ">>> checking processes"
ps aux | grep "chaddi.py"
echo ""

# kill server running on port 5100
PORT=5100
PID_PORT=$(lsof -t -i:$PORT)
if [[ "" != "$PID_PORT" ]]; then
    echo ">>> killing process on port $PORT - PID $PID_PORT"
    kill -9 $PID_PORT
fi
echo ">>> checking processes on port $PORT"
lsof -i:$PORT
echo ""