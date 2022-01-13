#!/bin/bash
/api/startup_scripts/wait_for_db.sh
/api/startup_scripts/wait_for_proxy.sh
/venv/bin/python3.9 -u /api/startup_scripts/register_in_proxy.py `cat /etc/hostname` && \
/venv/bin/python3.9 -m src.main
