#!/bin/bash
/api/startup_scripts/wait_for_db.sh && \
/api/startup_scripts/wait_for_kafka.sh && \
/venv/bin/python3.9 -m src.main
