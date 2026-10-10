#!/bin/bash
# kill-chaddi.sh
#
# Stops the running chaddi-tg. In prod chaddi.service (Restart=always) brings it
# straight back up, so this doubles as a restart.

PORT=5100
# Match only the bot itself ("uv run python chaddi.py" and its python child),
# not any shell whose command line happens to mention chaddi.py
PATTERN='(uv run python|bin/python3?) chaddi\.py$'

PIDS=$(pgrep -f "$PATTERN")

if [[ -n "$PIDS" ]]; then
    echo ">>> stopping chaddi-tg - PIDs $(echo $PIDS)"
    kill $PIDS 2>/dev/null

    # Give PTB a chance to shut down cleanly before forcing it
    for i in $(seq 1 15); do
        pgrep -f "$PATTERN" >/dev/null || break
        sleep 1
    done

    PIDS=$(pgrep -f "$PATTERN")
    if [[ -n "$PIDS" ]]; then
        echo ">>> chaddi-tg did not exit, killing - PIDs $(echo $PIDS)"
        kill -9 $PIDS 2>/dev/null
    fi
fi

PID_PORT=$(lsof -t -i:$PORT -sTCP:LISTEN)
if [[ -n "$PID_PORT" ]]; then
    echo ">>> killing leftover process on port $PORT - PID $PID_PORT"
    kill -9 $PID_PORT
fi

echo ">>> chaddi-tg stopped"
