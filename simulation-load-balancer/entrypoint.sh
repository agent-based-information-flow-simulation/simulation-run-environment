#!/bin/bash
while ! nc -z db 27017; do sleep 1; done;
echo "Database is up"

/venv/bin/python3.10 -m src.main
