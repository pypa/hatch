#!/bin/ash
# http://redsymbol.net/articles/unofficial-bash-strict-mode/
IFS=$'\n\t'
set -euo pipefail

echo "==:> Initializing server"
devpi-init --no-root-pypi

echo "==:> Starting server"
devpi-server --host 0.0.0.0 --port 3141 &

echo "==:> Waiting on server"
for i in $(seq 1 30); do
    if devpi use http://localhost:3141 2>/dev/null; then
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "Timed out waiting for devpi-server"
        exit 1
    fi
    sleep 1
done


echo "==:> Setting up index"
devpi use http://localhost:3141
devpi user -c $DEVPI_USERNAME password=$DEVPI_PASSWORD
devpi login $DEVPI_USERNAME --password=$DEVPI_PASSWORD
devpi index -c $DEVPI_INDEX_NAME volatile=True mirror_whitelist="*"
devpi use $DEVPI_USERNAME/$DEVPI_INDEX_NAME
devpi logoff

echo "==:> Serving index $DEVPI_USERNAME/$DEVPI_INDEX_NAME"
sleep infinity
