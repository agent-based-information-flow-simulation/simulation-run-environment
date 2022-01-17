#!/bin/bash
/app/startup_scripts/wait_for_kafka.sh
java -jar /app/target/scala-2.12/kafka-streams-assembly-0.1.0-SNAPSHOT.jar
