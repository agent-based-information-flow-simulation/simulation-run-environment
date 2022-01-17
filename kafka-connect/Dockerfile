FROM confluentinc/cp-kafka-connect:7.0.1

RUN confluent-hub install --no-prompt neo4j/kafka-connect-neo4j:2.0.1

COPY ./connectors /app/connectors

COPY ./startup_scripts /app/startup_scripts

COPY ./entrypoint.sh /app/entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]
