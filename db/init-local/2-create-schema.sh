#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "$(readlink -f "${BASH_SOURCE[0]}")" )" && pwd)"

sqlplus -s YCCLOCAL/changeit@XE @"$SCRIPT_DIR/sql/schema-local.sql"
