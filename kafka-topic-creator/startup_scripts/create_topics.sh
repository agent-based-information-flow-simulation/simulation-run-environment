#!/bin/bash
# env variables:
# - BOOTSTRAP_SERVER
# - NUM_BROKERS
# - UPDATE_AGENT_INPUT_TOPIC_NAME
# - UPDATE_AGENT_INPUT_TOPIC_REPLICATION_FACTOR
# - UPDATE_AGENT_INPUT_TOPIC_PARTITIONS
# - UPDATE_AGENT_OUTPUT_TOPIC_NAME
# - UPDATE_AGENT_OUTPUT_TOPIC_REPLICATION_FACTOR
# - UPDATE_AGENT_OUTPUT_TOPIC_PARTITIONS
# - ZOOKEEPER_SERVER

function are_all_brokers_available() {
    NUM_FOUND_BROKERS=$(("$(zookeeper-shell.sh "${ZOOKEEPER_SERVER}" ls /brokers/ids 2>/dev/null | grep -o , | wc -l)" + 1))
    [[ "${NUM_FOUND_BROKERS}" -ge "${NUM_BROKERS}" ]]
    return
}

while ! are_all_brokers_available; do
    echo "Not all brokers not available yet"
    sleep 1
done

echo "Creating topics"

kafka-topics.sh \
    --create \
    --topic "${UPDATE_AGENT_INPUT_TOPIC_NAME}"  \
    --replication-factor "${UPDATE_AGENT_INPUT_TOPIC_REPLICATION_FACTOR}" \
    --partitions "${UPDATE_AGENT_INPUT_TOPIC_PARTITIONS}" \
    --bootstrap-server "${BOOTSTRAP_SERVER}" \
    --if-not-exists \
    --config "cleanup.policy=compact" && \
\
kafka-topics.sh \
    --create \
    --topic "${UPDATE_AGENT_OUTPUT_TOPIC_NAME}"  \
    --replication-factor "${UPDATE_AGENT_OUTPUT_TOPIC_REPLICATION_FACTOR}" \
    --partitions "${UPDATE_AGENT_OUTPUT_TOPIC_PARTITIONS}" \
    --bootstrap-server "${BOOTSTRAP_SERVER}" \
    --if-not-exists \
    --config "cleanup.policy=compact" && \
\
echo "Topics created"
