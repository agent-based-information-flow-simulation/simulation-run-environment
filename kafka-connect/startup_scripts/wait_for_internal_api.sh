#!/bin/bash
echo "Waiting for Kafka Connect API to start listening on localhost"

function ping_api() {
    echo `curl -s -o /dev/null -w %{http_code} localhost:${CONNECT_REST_PORT}/connectors`
}

while true; do
    RESPONSE_CODE=`ping_api`
    echo "Response code from Kafka Connect API: ${RESPONSE_CODE}"
    if [ "${RESPONSE_CODE}" = "200" ]; then break; fi
    echo "Retrying..."
    sleep 1; 
done
