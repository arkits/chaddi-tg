set -e

psql -c "DROP DATABASE chaddi_tg;"
psql -c "CREATE DATABASE chaddi_tg;"
