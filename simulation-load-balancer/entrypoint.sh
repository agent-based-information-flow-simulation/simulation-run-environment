#!/bin/bash
while ! nc -z redis 6379; do sleep 1; done;
echo "Redis is up"

/venv/bin/python3.10 -m src.main
