#!/bin/bash
# env variables:
# - WAIT_FOR_KAFKA_ADDRESS
# - WAIT_FOR_KAFKA_TOPICS

echo "Waiting for kafka topics"

IFS=',' read -ra TOPICS_SPLIT <<< "${WAIT_FOR_KAFKA_TOPICS}"
for TOPIC in "${TOPICS_SPLIT[@]}"; do
    echo "Waiting for topic: ${TOPIC}"
    while [ "$(kafkacat -b ${WAIT_FOR_KAFKA_ADDRESS} -L -m 60 | grep topic | grep -ow ${TOPIC})" != "${TOPIC}" ] ; do
        echo "Retrying topic ${TOPIC}"
        sleep 1
    done
done

echo "Kafka topics [${TOPICS_SPLIT[@]}] are up"
