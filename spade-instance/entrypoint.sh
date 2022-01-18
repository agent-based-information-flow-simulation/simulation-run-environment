#!/bin/bash
/api/startup_scripts/wait_for_kafka.sh && \
/api/startup_scripts/wait_for_kafka_topics.sh && \
/venv/bin/python3.9 -m src.main
