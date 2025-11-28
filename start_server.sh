#!/bin/bash
# Load .env file and export variables
set -a
source .env
set +a

# Start gunicorn with PORT from .env (or default to 5000)
exec python3 -m gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:${PORT:-5000} app:app

