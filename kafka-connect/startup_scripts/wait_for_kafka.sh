#!/bin/bash
# env variables:
# - WAIT_FOR_KAFKA_ADDRESS

echo "Waiting for Kafka"
IFS=':' read -ra ADDRESS_SPLIT <<< "${WAIT_FOR_KAFKA_ADDRESS}"
if [ "${#ADDRESS_SPLIT[@]}" -ne "2" ]; then
    echo "Expected argument format: HOST:PORT"
    echo "Unexpected argument: ${ADDRESS}"
    echo "Split (on ':' delimiter) into:"
    for PART in "${ADDRESS_SPLIT[@]}"; do
        echo "${PART}"
    done
    exit 1
fi
HOST="${ADDRESS_SPLIT[0]}"
PORT="${ADDRESS_SPLIT[1]}"

while ! nc -z "${HOST}" "${PORT}"; do sleep 1; done;
echo "Kafka is up"
