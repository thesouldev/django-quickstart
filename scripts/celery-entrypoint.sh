#!/bin/sh

set -a
[ -f /app/.env ] && . /app/.env
set +a

export PYTHONPATH="/app/src:$PYTHONPATH"

cd /app/src

exec "$@"