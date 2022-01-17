#!/bin/bash
/api/startup_scripts/wait_for_kafka.sh && \
/venv/bin/python3.9 -m src.main
