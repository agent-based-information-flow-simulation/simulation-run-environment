#!/bin/bash
/api/startup_scripts/wait_for_redis.sh && \
/venv/bin/python3.10 -m src.main
