#!/bin/bash
/app/startup_scripts/wait_for_db.sh && \
/app/startup_scripts/wait_for_kafka.sh && \
/app/startup_scripts/wait_for_kafka_topics.sh && \
/venv/bin/python3.9 -m src.main
