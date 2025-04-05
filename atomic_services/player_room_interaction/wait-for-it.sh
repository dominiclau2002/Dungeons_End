#!/usr/bin/env bash
# wait-for-it.sh

set -e

host="$1"
shift
cmd="$@"

until nc -z ${host%:*} ${host##*:}; do
  echo "Waiting for $host to be ready..."
  sleep 2
done

echo "$host is up - executing command"
exec $cmd
