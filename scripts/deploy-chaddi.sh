#!/bin/bash
# deploy-chaddi.sh

set -e

source deploy-constants.sh

echo ">>> Running hostscript - $SSH_USER@$SSH_HOST"
echo ">>> DEPLOY_ARGS=$DEPLOY_ARGS"
echo " "
ssh -q $SSH_USER@$SSH_HOST "$DEPLOY_ARGS" 'bash -s' <deploy-hostscript.sh
if [ $? -ne 0 ]; then
    echo "ERROR: running install-hostscript as $SSH_USER@$SSH_HOST failed"
    exit 4
fi
