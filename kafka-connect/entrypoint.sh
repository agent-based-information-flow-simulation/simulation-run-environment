#!/bin/bash
/app/startup_scripts/wait_for_kafka.sh
/etc/confluent/docker/run &
/app/startup_scripts/wait_for_internal_api.sh
/app/startup_scripts/create_connectors.sh
sleep infinity
