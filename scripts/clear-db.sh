#!/bin/bash
# clear-db.sh

# Stop if there is an error
set -e

psql -c "DELETE FROM bakchod;" -d chaddi_tg
psql -c "DELETE FROM group;" -d chaddi_tg
psql -c "DELETE FROM groupmember;" -d chaddi_tg
psql -c "DELETE FROM message;" -d chaddi_tg
psql -c "DELETE FROM quote;" -d chaddi_tg
psql -c "DELETE FROM roll;" -d chaddi_tg
