# Simulation Run Environment

## Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)
- [Structure](#structure)

## About <a name = "about"></a>

Simulation run environment.

## Getting Started <a name = "getting_started"></a>

### Prerequisites

```
docker
docker-compose (dev only)
```

### Installing
To use the application, utilize the `server.sh` script. </br>
First, initialize the cluster:
```
./server.sh init
```

Alternatively, join the existing cluster using the `TOKEN` received from the `init` command:
```
./server.sh join TOKEN
```

Then, create the required networks (this step needs to be done only once inside the cluster):
```
./server.sh network
```

Finally, start the application:
```
./server.sh start
```

To see all the available options run the `help` command:
```
./server.sh help
```

## Usage <a name = "usage"></a>
The application must be used with a dedicated user interface and communication server.

## Structure <a name = "structure"></a>

The structure of the simulation run environment is presented below.
- [Data processor](#data-processor)
- [Data processor Mongo](#data-processor-mongo)
- [Data processor proxy](#data-processor-proxy)
- [DB](#db)
- [Entrypoint](#entrypoint)
- [Graph generator](#graph-generator)
- [Kafka](#kafka)
- [Kafka consumer](#kafka-consumer)
- [Kafka consumer Mongo](#kafka-consumer-mongo)
- [Kafka GUI](#kafka-gui)
- [Kafka streams](#kafka-streams)
- [Kafka topic creator](#kafka-topic-creator)
- [Mongo](#mongo)
- [Mongo GUI](#mongo-gui)
- [Redis](#redis)
- [Simulation load balancer](#simulation-load-balancer)
- [Spade instance](#spade-instance)
- [Translator](#translator)
- [Zookeeper](#zookeeper)

### Data processor <a name = "data-processor"></a>
The service processes the agent data stored in the graph database (neo4j).
The data is used for backup purposes (see `data-processor/src/routers/backup.py`).
Backups are accessed once a failure occurs or in the case of resuming the simulation after a stop.
Additionally, the service handles requests related to the statistics about the simulation (see `data-processor/src/routers/statistics.py`).

Environment variables:
* `DB_URL`
* `LOG_LEVEL_SERVICES`
* `PORT`
* `PROXY_REGISTRATION_ADDRESS`
* `PROXY_REGISTRATION_BACKEND_DATA_PROCESSOR_NAME`
* `PROXY_REGISTRATION_BACKEND_DATA_PROCESSOR_PORT`
* `PROXY_REGISTRATION_MAX_RETRIES`
* `PROXY_REGISTRATION_USER_NAME`
* `PROXY_REGISTRATION_USER_PASSWORD`
* `RELOAD`
* `WAIT_FOR_DB_ADDRESS`
* `WAIT_FOR_PROXY_ADDRESS`

### Data processor Mongo <a name = "data-processor-mongo"></a>
The service processes the agent data stored in the timeseries database (Mongo).
It handles the requests to access the timeseries data for further manual analysis (see `data-processor-mongo/src/routers/timeseries.py`).

Environment variables:
* `DB_URL`
* `PORT`
* `RELOAD`
* `WAIT_FOR_DB_ADDRESS`

Host port mapping (dev only):
* `8004`

### Data processor proxy <a name = "data-processor-proxy"></a>
The proxy provides access to multiple instances of the data processor service.
The registration procedure is automatic, and it happens once an instance of the data processor starts.

Environment variables:
* `API_PORT`
* `DATA_PROCESSOR_LISTEN_PORT`

Host port mapping (dev only):
* `5556` (proxy Web API)
* `8002` (data processor)

### DB <a name = "db"></a>
The graph database (neo4j) stores the most recent data advertised by agents running in the simulation.
Nodes represent agent instances, and edges represent messages and connections between the agents.

Environment variables:
* `NEO4J_AUTH`
* `NEO4JLABS_PLUGINS`

Host port mapping (dev only):
* `7474` (HTTP access)
* `7687` (Bolt access)

### Entrypoint <a name = "entrypoint"></a>
The service is the single entrypoint to the application.
It provides access to the following services: data processor, data processor Mongo, simulation load balancer, and graph database.

Environment variables:
* `API_LISTEN_PORT`
* `DATA_PROCESSOR_MONGO_BACKEND_PORT`
* `DATA_PROCESSOR_PROXY_BACKEND_PORT`
* `DB_LISTEN_PORT`
* `DB_BACKEND_PORT`
* `SIMULATION_LOAD_BALANCER_BACKEND_PORT`

Host port mapping (dev only):
* `8888` (simulation load balancer, data processor proxy, data processor Mongo)
* `8889` (neo4j)

### Graph generator <a name = "graph-generator"></a>
It handles requests with algorithms for graph structure generation.
It runs the code and generates the JSON representation of the network (see `graph-generator/src/routers.py`).

Environment variables:
* `COMMUNICATION_SERVER_DOMAIN`
* `PORT`
* `RELOAD`

Host port mapping (dev only):
* `8001`

### Kafka <a name = "kafka"></a>
The service is a message broker that stores the agent data from the running simulations.
Externally, two topics are available - one for the input data and the other for the output data.
The spade instances produce data that is attached to the input topic.
The Kafka streams service consumes the input topic and produces the output topic.
The Kafka consumer consumes the output topic and moves the data to the graph database.
The Kafka consumer Mongo consumes the input topic and moves the data to the timeseries database.

Environment variables:
* `ALLOW_PLAINTEXT_LISTENER`
* `KAFKA_BROKER_ID`
* `KAFKA_CFG_ADVERTISED_LISTENERS`
* `KAFKA_CFG_INTER_BROKER_LISTENER_NAME`
* `KAFKA_CFG_LISTENERS`
* `KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP`
* `KAFKA_CFG_OFFSET_METADATA_MAX_BYTES`
* `KAFKA_CFG_ZOOKEEPER_CONNECT`
* `WAIT_FOR_ZOOKEEPER_ADDRESS`

Host port mapping (dev only):
* `9093`

### Kafka consumer <a name = "kafka-consumer"></a>
Its purpose is to consume the data in batches from the Kafka output topic with agent updates and save it in the graph database.

Environment variables:
* `BATCH_TIMEOUT_MS`
* `DB_URL`
* `KAFKA_ADDRESS`
* `LOG_LEVEL_MAIN`
* `UPDATE_AGENT_OUTPUT_TOPIC_NAME`
* `WAIT_FOR_DB_ADDRESS`
* `WAIT_FOR_KAFKA_ADDRESS`
* `WAIT_FOR_KAFKA_TOPICS`

### Kafka consumer Mongo <a name = "kafka-consumer-mongo"></a>
Its purpose is to consume the data in batches from the Kafka input topic with agent updates and save it in the timeseries database.

Environment variables:
* `BATCH_TIMEOUT_MS`
* `DB_URL`
* `KAFKA_ADDRESS`
* `LOG_LEVEL_MAIN`
* `UPDATE_AGENT_INPUT_TOPIC_NAME`
* `WAIT_FOR_DB_ADDRESS`
* `WAIT_FOR_KAFKA_ADDRESS`
* `WAIT_FOR_KAFKA_TOPICS`

### Kafka GUI (dev only) <a name = "kafka-gui"></a>
The service provides a graphical user interface to access the data stored inside Kafka instances.

Environment variables:
* `KAFKA_BROKERCONNECT`

Host port mapping (dev only):
* `9090`

### Kafka streams <a name = "kafka-streams"></a>
The service is responsible for converting the data produced by spade instances to create a representation that can be easily inserted into the graph database.

Environment variables:
* `BOOTSTRAP_SERVER`
* `UPDATE_AGENT_INPUT_TOPIC_NAME`
* `UPDATE_AGENT_OUTPUT_TOPIC_NAME`
* `WAIT_FOR_KAFKA_ADDRESS`
* `WAIT_FOR_KAFKA_TOPICS`

### Kafka topic creator <a name = "kafka-topic-creator"></a>
The service uses Apache Kafka utility scripts to connect to the Kafka service and create the available topics.
After meeting its objective, it shutdowns.
Therefore, it runs only once.

Environment variables:
* `BOOTSTRAP_SERVER`
* `NUM_BROKERS`
* `UPDATE_AGENT_INPUT_TOPIC_NAME`
* `UPDATE_AGENT_INPUT_TOPIC_REPLICATION_FACTOR`
* `UPDATE_AGENT_INPUT_TOPIC_PARTITIONS`
* `UPDATE_AGENT_OUTPUT_TOPIC_NAME`
* `UPDATE_AGENT_OUTPUT_TOPIC_REPLICATION_FACTOR`
* `UPDATE_AGENT_OUTPUT_TOPIC_PARTITIONS`
* `WAIT_FOR_KAFKA_ADDRESS`
* `WAIT_FOR_ZOOKEEPER_ADDRESS`
* `ZOOKEEPER_SERVER`

### Mongo <a name = "mongo"></a>
The service is used as a timeseries database.
It stores agents' updates coming from spade instances.

Environment variables:
* `MONGODB_ROOT_USER`
* `MONGODB_ROOT_PASSWORD`
* `MONGODB_USERNAME`
* `MONGODB_PASSWORD`
* `MONGODB_DATABASE`

Host port mapping (dev only):
* `27017`

### Mongo GUI (dev only) <a name = "mongo-gui"></a>
The service provides a graphical user interface to access the data stored inside the timeseries database.

Environment variables:
* `ME_CONFIG_MONGODB_ADMINUSERNAME`
* `ME_CONFIG_MONGODB_ADMINPASSWORD`
* `ME_CONFIG_MONGODB_SERVER`
* `ME_CONFIG_OPTIONS_EDITORTHEME`

Host port mapping (dev only):
* `27018`

### Redis <a name = "redis"></a>
The service is used by the simulation load balancer to store the spade instances' states, simulation definitions, and additional metadata about the created simulations.

Environment variables:
* `REDIS_PASSWORD`

Host port mapping (dev only):
* `6379`

### Simulation load balancer <a name = "simulation-load-balancer"></a>
It is responsible for creating new simulations (see `simulation-load-balancer/src/routers.py`) by connecting to the translator, the graph generator, and the data processor (via proxy).
Next, it is in charge of orchestrating the spade instances. It monitors instances' advertised states to make decisions about the simulation.
As for its storage, it uses the Redis service.

Environment variables:
* `GRAPH_GENERATOR_URL`
* `DATA_PROCESSOR_URL`
* `LOG_LEVEL_HANDLERS`
* `PORT`
* `REDIS_ADDRESS`
* `REDIS_PORT`
* `REDIS_PASSWORD`
* `RELOAD`
* `TRANSLATOR_URL`
* `WAIT_FOR_REDIS_ADDRESS`

Host port mapping (dev only):
* `8003`

### Spade instance <a name = "spade-instance"></a>
The service runs the code received from the simulation load balancer.
It consists of Web API (see `spade-instance/src/routers.py`) and the simulation process (see `spade-instance/src/simulation/main.py`).
The latter one is created while starting the simulation.
The API is used to communicate and manage the instance (see `spade-instance/src/routers.py`).
It is connected to the communication server stack to enable the exchange of messages between the agents.
Periodically, the service sends an HTTP request to the simulation load balancer with its current state (see `spade-instance/src/repeated_tasks.py` and `spade-instance/src/state.py`).
The service sends the running agents' state updates to the Kafka service.

Environment variables:
* `ACTIVE_SIMULATION_STATUS_ANNOUCEMENT_URL`
* `ACTIVE_SIMULATION_STATUS_ANNOUCEMENT_PERIOD`
* `AGENT_BACKUP_URL`
* `AGENT_BACKUP_PERIOD`
* `AGENT_BACKUP_DELAY`
* `AGENT_REGISTRATION_MAX_CONCURRENCY`
* `AGENT_REGISTRATION_RETRY_AFTER`
* `COMMUNICATION_SERVER_PASSWORD`
* `KAFKA_ADDRESS`
* `KAFKA_UPDATE_AGENT_INPUT_TOPIC_NAME`
* `LOG_LEVEL_AGENT`
* `LOG_LEVEL_KAFKA`
* `LOG_LEVEL_UVICORN_ACCESS`
* `LOG_LEVEL_REPEATED_TASKS`
* `LOG_LEVEL_ROUTERS`
* `LOG_LEVEL_SIMULATION_CODE_GENERATION`
* `LOG_LEVEL_SIMULATION_INITIALIZATION`
* `LOG_LEVEL_SIMULATION_MAIN`
* `LOG_LEVEL_SIMULATION_STATUS`
* `LOG_LEVEL_SPADE_BEHAVIOUR`
* `LOG_LEVEL_STATE`
* `PORT`
* `RELOAD`
* `SIMULATION_LOAD_BALANCER_URL`
* `SIMULATION_LOAD_BALANCER_ANNOUNCEMENT_PERIOD`
* `SIMULATION_PROCESS_HEALTH_CHECK_PERIOD`
* `WAIT_FOR_KAFKA_ADDRESS`
* `WAIT_FOR_KAFKA_TOPICS`

### Translator <a name = "translator"></a>
The service's Web API enables the translation of Agents Assembly code using the `aasm` package (see `translator/src/routers.py`).

Environment variables:
* `PORT`
* `RELOAD`

Host port mapping (dev only):
* `8000`

### Zookeeper <a name = "zookeeper"></a>
It is a coordinator used to manage the Kafka service.
It maintains configuration information and provides synchronization and group services.

Environment variables:
* `ALLOW_ANONYMOUS_LOGIN`

Host port mapping (dev only):
* `2181`
* `2182` (admin server)
