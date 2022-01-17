#!/bin/bash
echo "Creating Kafka Connect neo4j sink connector"
curl -i -X POST localhost:8083/connectors -H "Content-Type: application/json" -d @/app/connectors/neo4jSinkConnector.json
