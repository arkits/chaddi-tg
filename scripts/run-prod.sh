#!/bin/bash
# run-prod.sh
#
# chaddi-tg runs under systemd in prod (see scripts/chaddi.service). Starting a
# second copy by hand steals port 5100 and getUpdates from the service, which
# then crash-loops - so this only starts the service.

set -e

if systemctl cat chaddi.service >/dev/null 2>&1; then
    echo ">>> chaddi-tg is managed by chaddi.service - not starting it by hand"
    echo ">>> use ./restart-prod.sh to restart it"
    exit 1
fi

echo "ERROR: chaddi.service is not installed - see scripts/chaddi.service"
exit 4
