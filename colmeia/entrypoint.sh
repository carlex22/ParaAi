#!/usr/bin/env bash
set -e

python -u worker.py &

# server (porta esperada pelo Spaces: 7860)
exec uvicorn app:app --host 0.0.0.0 --port 7860
