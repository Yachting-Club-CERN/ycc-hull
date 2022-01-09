#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "$(readlink -f "${BASH_SOURCE[0]}")" )" && pwd)"

# In this way it produces a container start failure upon SQL error
sqlplus -s YCCLOCAL/changeit@XE @"$SCRIPT_DIR/sql/schema-local.sql"
