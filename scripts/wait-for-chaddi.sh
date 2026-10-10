#!/bin/bash
# wait-for-chaddi.sh
#
# Waits for chaddi.service to bring chaddi-tg back up after it was stopped.

PORT=5100
# RestartSec=10, then uv sync + imports take a while on first start
TIMEOUT=120

echo ">>> waiting up to ${TIMEOUT}s for chaddi.service to bind to port $PORT"

for i in $(seq 1 $TIMEOUT); do
    PID_PORT=$(lsof -t -i:$PORT -sTCP:LISTEN)
    if [[ -n "$PID_PORT" ]]; then
        echo ">>> chaddi-tg is up - PID $PID_PORT ($(systemctl is-active chaddi.service))"
        exit 0
    fi
    sleep 1
done

echo "ERROR: chaddi-tg did not bind to port $PORT within ${TIMEOUT}s"
systemctl status chaddi.service --no-pager | head -20
journalctl -u chaddi.service -n 30 --no-pager
exit 4
