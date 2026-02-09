#!/bin/sh

# Change to the application directory where main.py is located
cd /app/src

# Running Uvicorn
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info