#!/bin/bash
set -eu

echo "Preparing conf/config.json ..."
echo "$CONFIG_JSON" > "conf/config.json"

echo "Preparing conf/logging.conf ..."
echo "$LOGGING_CONF" > "conf/logging.conf"

python -m ycc_hull.main
