#!/bin/bash
/app/startup_scripts/wait_for_zookeeper.sh && \
/app/startup_scripts/wait_for_kafka.sh && \
/app/startup_scripts/create_topics.sh
