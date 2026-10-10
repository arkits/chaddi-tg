#!/bin/bash
# deploy-hostscript.sh

set -e

# uv lives in ~/.local/bin, which a non-interactive ssh session doesn't have on PATH
export PATH="$HOME/.local/bin:$PATH"

echo ">>> hostscript running as $(whoami)@$(hostname)"
echo ">>> deploying chaddi-tg to $(pwd)"
echo ""

cd /opt/software/

if [ -d "chaddi-tg" ]; then

    echo ">>> chaddi-tg was present"
    cd chaddi-tg
    echo ""

    echo ">>> fetching latest from remote"
    git fetch origin
    git reset --hard origin/master
    git clean -fd -- frontend
    echo ""

    echo ">>> building frontend"
    cd frontend
    if command -v bun >/dev/null 2>&1; then
        bun install --frozen-lockfile
        bun run build
    elif command -v npm >/dev/null 2>&1; then
        npm install
        npm run build
    else
        echo "ERROR: bun or npm is required to build the frontend"
        exit 4
    fi
    cd ..
    echo ""

    echo ">>> syncing python dependencies"
    uv sync
    echo ""

    # chaddi.service (Restart=always) owns the process - stop it and let systemd
    # start the new code, rather than starting a second copy that fights it
    # for port 5100 and getUpdates
    cd scripts
    ./kill-chaddi.sh
    ./wait-for-chaddi.sh

    echo ">>> done deploying chaddi-tg"

else

    echo ">>> chaddi-tg was not present!"
    exit 4
fi
