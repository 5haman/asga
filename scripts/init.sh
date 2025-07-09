#!/bin/sh
set -e

# wait for langfuse to start
until curl -sf http://langfuse-web:3000 >/dev/null; do
  echo "waiting for langfuse..."
  sleep 2
done

exec uvicorn src.agent:app --host 0.0.0.0 --port 8000
