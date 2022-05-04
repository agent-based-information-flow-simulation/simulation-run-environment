#!/bin/bash
/api/startup_scripts/wait_for_db.sh && \
/venv/bin/python3.9 -m src.main
