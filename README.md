# Simulation Run Environment

## Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)
- [Structure](#structure)
- [Contributing](#contributing)

## About <a name = "about"></a>

Environment for running scalable agent-based simulations.
The Simulation Run Environment is a part of the [Agents Assembly](https://agents-assembly.com) ecosystem.
Other applications are:
- [Local Interface](https://github.com/agent-based-information-flow-simulation/local-interface) - GUI for simulation definition, management, and analysis.
- [Communication Server](https://github.com/agent-based-information-flow-simulation/communication-server) - cluster of servers used for XMPP communication.
- [Agents Assembly Translator](https://github.com/agent-based-information-flow-simulation/agents-assembly-translator) - translator for Agents Assembly code.
- [Local Development Environment](https://github.com/agent-based-information-flow-simulation/local-development-environment) - simple environment for running agent-based simulations.

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
- [SPADE instance](#spade-instance)
- [Translator](#translator)
- [Zookeeper](#zookeeper)

### Data processor <a name = "data-processor"></a>
The service processes the agent data stored in the graph database (neo4j).
The data is used for backup purposes (see `data-processor/src/routers/backup.py`).
Backups are accessed once a failure occurs or in the case of resuming the simulation after a stop.
Additionally, the service handles requests related to the statistics about the simulation (see `data-processor/src/routers/statistics.py`).

[Docker Hub](https://hub.docker.com/r/aasm/sre-data-processor)

Environment variables:
* `DB_URL` - neo4j connection string (Bolt access, i.e., neo4j://db:7687)
* `PORT` - listen port (i.e., 8000)
* `PROXY_REGISTRATION_ADDRESS` - data processor proxy Web API address (i.e., data-processor-proxy:5555)
* `PROXY_REGISTRATION_BACKEND_DATA_PROCESSOR_NAME` - data processor proxy backend name for data processor instances (i.e., data_processor)
* `PROXY_REGISTRATION_BACKEND_DATA_PROCESSOR_PORT` - data processor proxy backend port for data processor instances (i.e., 8000); it must match `PORT` value
* `PROXY_REGISTRATION_MAX_RETRIES` - data processor proxy maximum number of registration retries (i.e., 100)
* `PROXY_REGISTRATION_USER_NAME` - data processor proxy user name (i.e., admin)
* `PROXY_REGISTRATION_USER_PASSWORD` - data processor proxy user password (i.e., admin)
* `RELOAD` - reload application after detecting a change in source files (i.e., False); if set to True, it requires the following volume attached: data-processor/src:/api/src
* `WAIT_FOR_DB_ADDRESS` - neo4j address (HTTP access, i.e., db:7474)
* `WAIT_FOR_PROXY_ADDRESS` - data processor proxy Web API address (i.e., data-processor-proxy:5555)

### Data processor Mongo <a name = "data-processor-mongo"></a>
The service processes the agent data stored in the timeseries database (Mongo).
It handles the requests to access the timeseries data for further manual analysis (see `data-processor-mongo/src/routers/timeseries.py`).

[Docker Hub](https://hub.docker.com/r/aasm/sre-data-processor-mongo)

Environment variables:
* `DB_URL` - MongoDB connection string (i.e., mongodb://user:pass@mongo:27017/simulations)
* `PORT` - listen port (i.e., 8000)
* `RELOAD` - reload application after detecting a change in source files (i.e., False); if set to True, it requires the following volume attached: data-processor-mongo/src:/api/src
* `WAIT_FOR_DB_ADDRESS` - MongoDB address (i.e., mongo:27017)

Host port mapping (dev only):
* `8004`

### Data processor proxy <a name = "data-processor-proxy"></a>
The proxy provides access to multiple instances of the data processor service.
The registration procedure is automatic, and it happens once an instance of the data processor starts.

[Docker Hub](https://hub.docker.com/r/aasm/sre-data-processor-proxy)

Environment variables:
* `API_PORT` - [Data Plane API](https://www.haproxy.com/documentation/hapee/latest/api/data-plane-api/) listen port (i.e., 5555)
* `DATA_PROCESSOR_LISTEN_PORT` - data processor backend listen port (i.e., 8000)

Host port mapping (dev only):
* `5556` (proxy Web API)
* `8002` (data processor)

### DB <a name = "db"></a>
The graph database (neo4j) stores the most recent data advertised by agents running in the simulation.
Nodes represent agent instances, and edges represent messages and connections between the agents.

Environment variables:
* `NEO4J_AUTH` - [neo4j docs](https://neo4j.com/docs/operations-manual/current/docker/introduction/#docker-auth) (i.e., none)
* `NEO4JLABS_PLUGINS` - [neo4j docs](https://neo4j.com/docs/operations-manual/current/docker/operations/#docker-neo4jlabs-plugins) (i.e., ["apoc"])

Host port mapping (dev only):
* `7474` (HTTP access)
* `7687` (Bolt access)

### Entrypoint <a name = "entrypoint"></a>
The service is the single entrypoint to the application.
It provides access to the following services: data processor, data processor Mongo, simulation load balancer, and graph database.

[Docker Hub](https://hub.docker.com/r/aasm/sre-entrypoint)

Environment variables:
* `API_LISTEN_PORT` - port the user interface uses to access the SRE API (i.e., 80)
* `DATA_PROCESSOR_MONGO_BACKEND_PORT` - data processor Mongo backend port (i.e., 8000); it must match data processor Mongo `PORT` value
* `DATA_PROCESSOR_PROXY_BACKEND_PORT` - data processor proxy backend port (i.e., 8000); it must match data processor proxy `DATA_PROCESSOR_LISTEN_PORT` value
* `DB_LISTEN_PORT` - port the user interface uses to access the graph database (i.e., 7687)
* `DB_BACKEND_PORT` - graph database backend port (i.e., 7687); it must match graph database port used for Bolt access
* `SIMULATION_LOAD_BALANCER_BACKEND_PORT` - simulation load balancer backend port (i.e., 8000); it must match simulation load balancer `PORT` value

Host port mapping (dev only):
* `8888` (simulation load balancer, data processor proxy, data processor Mongo)
* `8889` (neo4j)

### Graph generator <a name = "graph-generator"></a>
It handles requests with algorithms for graph structure generation.
It runs the code and generates the JSON representation of the network (see `graph-generator/src/routers.py`).

[Docker Hub](https://hub.docker.com/r/aasm/sre-graph-generator)

Environment variables:
* `COMMUNICATION_SERVER_DOMAIN` - domain used by the XMPP server (i.e., cs_entrypoint)
* `PORT` - listen port (i.e., 8000)
* `RELOAD` - reload application after detecting a change in source files (i.e., False); if set to True, it requires the following volume attached: graph-generator/src:/api/src

Host port mapping (dev only):
* `8001`

### Kafka <a name = "kafka"></a>
The service is a message broker that stores the agent data from the running simulations.
Externally, two topics are available - one for the input data and the other for the output data.
The spade instances produce data that is attached to the input topic.
The Kafka streams service consumes the input topic and produces the output topic.
The Kafka consumer consumes the output topic and moves the data to the graph database.
The Kafka consumer Mongo consumes the input topic and moves the data to the timeseries database.

[Docker Hub](https://hub.docker.com/r/aasm/sre-kafka)

Environment variables:
* `ALLOW_PLAINTEXT_LISTENER` - [Bitnami docs](https://github.com/bitnami/bitnami-docker-kafka#configuration) (i.e., yes)
* `KAFKA_BROKER_ID` - [Bitnami docs](https://github.com/bitnami/bitnami-docker-kafka#configuration) (i.e., 1)
* `KAFKA_CFG_ADVERTISED_LISTENERS` - [Bitnami docs](https://github.com/bitnami/bitnami-docker-kafka#configuration) (i.e., CLIENT://kafka:9092)
* `KAFKA_CFG_INTER_BROKER_LISTENER_NAME` - [Bitnami docs](https://github.com/bitnami/bitnami-docker-kafka#configuration) (i.e., CLIENT)
* `KAFKA_CFG_LISTENERS` - [Bitnami docs](https://github.com/bitnami/bitnami-docker-kafka#configuration) (i.e., CLIENT://:9092)
* `KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP` - [Bitnami docs](https://github.com/bitnami/bitnami-docker-kafka#configuration) (i.e., CLIENT:PLAINTEXT)
* `KAFKA_CFG_OFFSET_METADATA_MAX_BYTES` - [Bitnami docs](https://github.com/bitnami/bitnami-docker-kafka#configuration) (i.e., 10485760)
* `KAFKA_CFG_ZOOKEEPER_CONNECT` - [Bitnami docs](https://github.com/bitnami/bitnami-docker-kafka#configuration) (i.e., zookeeper:2181)
* `WAIT_FOR_ZOOKEEPER_ADDRESS` - zookeeper address (i.e., zookeeper:2181)

Host port mapping (dev only):
* `9093`

### Kafka consumer <a name = "kafka-consumer"></a>
Its purpose is to consume the data in batches from the Kafka output topic with agent updates and save it in the graph database.

[Docker Hub](https://hub.docker.com/r/aasm/sre-kafka-consumer)

Environment variables:
* `BATCH_TIMEOUT_MS` - milliseconds spent waiting for a batch to be produced (i.e., 5000)
* `DB_URL` - neo4j connection string (i.e., neo4j://db:7687)
* `KAFKA_ADDRESS` - Kafka address (i.e., kafka:9092)
* `LOG_LEVEL_MAIN` - log level for `kafka-consumer/src/main.py` (i.e., INFO)
* `UPDATE_AGENT_OUTPUT_TOPIC_NAME` - name of the topic with transformed agent data (i.e., update_agent_output); it must match Kafka topic creator `UPDATE_AGENT_OUTPUT_TOPIC_NAME` value
* `WAIT_FOR_DB_ADDRESS` - neo4j address (HTTP access, i.e., db:7474)
* `WAIT_FOR_KAFKA_ADDRESS` - Kafka address (i.e., kafka:9092)
* `WAIT_FOR_KAFKA_TOPICS` - list of Kafka topic to wait for (i.e., update_agent_output)

### Kafka consumer Mongo <a name = "kafka-consumer-mongo"></a>
Its purpose is to consume the data in batches from the Kafka input topic with agent updates and save it in the timeseries database.

[Docker Hub](https://hub.docker.com/r/aasm/sre-kafka-consumer-mongo)

Environment variables:
* `BATCH_TIMEOUT_MS` - milliseconds spent waiting for a batch to be produced (i.e., 5000)
* `DB_URL` - MongoDB connection string (i.e., mongodb://user:pass@mongo:27017/simulations)
* `KAFKA_ADDRESS` - Kafka address (i.e., kafka:9092)
* `LOG_LEVEL_MAIN` - log level for `kafka-consumer-mongo/src/main.py` (i.e., INFO)
* `UPDATE_AGENT_INPUT_TOPIC_NAME` - name of the topic with agent data from spade instances (i.e., update_agent_input); it must match Kafka topic creator `UPDATE_AGENT_INPUT_TOPIC_NAME` value
* `WAIT_FOR_DB_ADDRESS` - MongoDB address (i.e., mongo:27017)
* `WAIT_FOR_KAFKA_ADDRESS` - Kafka address (i.e., kafka:9092)
* `WAIT_FOR_KAFKA_TOPICS` - list of Kafka topic to wait for (i.e., update_agent_input)

### Kafka GUI (dev only) <a name = "kafka-gui"></a>
The service provides a graphical user interface to access the data stored inside Kafka instances.

Environment variables:
* `KAFKA_BROKERCONNECT` - Kafka address (i.e., kafka:9092)

Host port mapping (dev only):
* `9090`

### Kafka streams <a name = "kafka-streams"></a>
The service is responsible for converting the data produced by spade instances to create a representation that can be easily inserted into the graph database.

[Docker Hub](https://hub.docker.com/r/aasm/sre-kafka-streams)

Environment variables:
* `BOOTSTRAP_SERVER` - Kafka address (i.e., kafka:9092)
* `UPDATE_AGENT_INPUT_TOPIC_NAME` - name of the topic with agent data from spade instances (i.e., update_agent_input); it must match Kafka topic creator `UPDATE_AGENT_INPUT_TOPIC_NAME` value
* `UPDATE_AGENT_OUTPUT_TOPIC_NAME` - name of the topic with transformed agent data (i.e., update_agent_output); it must match Kafka topic creator `UPDATE_AGENT_OUTPUT_TOPIC_NAME` value
* `WAIT_FOR_KAFKA_ADDRESS` - Kafka address (i.e., kafka:9092)
* `WAIT_FOR_KAFKA_TOPICS` - list of Kafka topic to wait for (i.e., update_agent_input,update_agent_output)

### Kafka topic creator <a name = "kafka-topic-creator"></a>
The service uses Apache Kafka utility scripts to connect to the Kafka service and create the available topics.
After meeting its objective, it shutdowns.
Therefore, it runs only once.

[Docker Hub](https://hub.docker.com/r/aasm/sre-kafka-topic-creator)

Environment variables:
* `BOOTSTRAP_SERVER` - Kafka address (i.e., kafka:9092)
* `NUM_BROKERS` - number of Kafka brokers (i.e., 1)
* `UPDATE_AGENT_INPUT_TOPIC_NAME` - name of the topic with agent data from spade instances (i.e., update_agent_input)
* `UPDATE_AGENT_INPUT_TOPIC_REPLICATION_FACTOR` - number of replicas for the topic with agent data from spade instances (i.e., 1)
* `UPDATE_AGENT_INPUT_TOPIC_PARTITIONS` - number of partitions for the topic with agent data from spade instances (i.e., 1); the number must be bigger than the number of consumers
* `UPDATE_AGENT_OUTPUT_TOPIC_NAME` - name of the topic with transformed agent data (i.e., update_agent_output)
* `UPDATE_AGENT_OUTPUT_TOPIC_REPLICATION_FACTOR` - number of replicas for the topic with transformed agent data (i.e., 1)
* `UPDATE_AGENT_OUTPUT_TOPIC_PARTITIONS` - number of partitions for the topic with transformed agent data (i.e., 1); the number must be bigger than the number of consumers (in a single group)
* `WAIT_FOR_KAFKA_ADDRESS` - Kafka address (i.e., kafka:9092)
* `WAIT_FOR_ZOOKEEPER_ADDRESS` - Zookeeper address (i.e., zookeeper:2181)
* `ZOOKEEPER_SERVER` - Zookeeper address (i.e., zookeeper:2181)

### Mongo <a name = "mongo"></a>
The service is used as a timeseries database.
It stores agents' updates coming from spade instances.

Environment variables:
* `MONGODB_ROOT_USER` - root user (i.e., root)
* `MONGODB_ROOT_PASSWORD` - root password (i.e., root)
* `MONGODB_USERNAME` - database user (i.e., user)
* `MONGODB_PASSWORD` - database password (i.e., pass)
* `MONGODB_DATABASE` - database name (i.e., simulations)

Host port mapping (dev only):
* `27017`

### Mongo GUI (dev only) <a name = "mongo-gui"></a>
The service provides a graphical user interface to access the data stored inside the timeseries database.

Environment variables:
* `ME_CONFIG_MONGODB_ADMINUSERNAME` - MongoDB root user (i.e., root)
* `ME_CONFIG_MONGODB_ADMINPASSWORD` - MongoDB root password (i.e., root)
* `ME_CONFIG_MONGODB_SERVER` - MongoDB address (i.e., mongo)
* `ME_CONFIG_OPTIONS_EDITORTHEME` - theme name (i.e., 3024-night)

Host port mapping (dev only):
* `27018`

### Redis <a name = "redis"></a>
The simulation load balancer uses the service to store the spade instances' states, simulation definitions, and additional metadata about the created simulations.

Environment variables:
* `REDIS_PASSWORD` - password (i.e., pass)

Host port mapping (dev only):
* `6379`

### Simulation load balancer <a name = "simulation-load-balancer"></a>
It is responsible for creating new simulations (see `simulation-load-balancer/src/routers.py`) by connecting to the translator, the graph generator, and the data processor (via proxy).
Next, it is in charge of orchestrating the spade instances. It monitors instances' advertised states to make decisions about the simulation.
As for its storage, it uses the Redis service.

[Docker Hub](https://hub.docker.com/r/aasm/sre-simulation-load-balancer)

Environment variables:
* `GRAPH_GENERATOR_URL` - graph generator url (i.e., http://graph-generator:8000)
* `DATA_PROCESSOR_URL` - data processor url (i.e., http://data-processor:8000)
* `LOG_LEVEL_HANDLERS` - log level for `simulation-load-balancer/src/handlers.py` (i.e., INFO)
* `PORT` - listen port (i.e., 8000)
* `REDIS_ADDRESS` - Redis address (i.e., redis)
* `REDIS_PORT` - Redis port (i.e., 6379)
* `REDIS_PASSWORD` - Redis password (i.e., password)
* `RELOAD` - reload application after detecting a change in source files (i.e., False); if set to True, it requires the following volume attached: simulation-load-balancer/src:/api/src
* `TRANSLATOR_URL` - translator url (i.e., http://translator:8000)
* `WAIT_FOR_REDIS_ADDRESS` - Redis address (i.e., redis:6379)

Host port mapping (dev only):
* `8003`

### SPADE instance <a name = "spade-instance"></a>
The service runs the code received from the simulation load balancer.
It consists of Web API (see `spade-instance/src/routers.py`) and the simulation process (see `spade-instance/src/simulation/main.py`).
The latter one is created while starting the simulation.
The API is used to communicate and manage the instance.
It is connected to the communication server stack to enable the exchange of messages between the agents.
Periodically, the service sends an HTTP request to the simulation load balancer with its current state (see `spade-instance/src/repeated_tasks.py` and `spade-instance/src/state.py`).
The service sends the running agents' state updates to the Kafka service.

[Docker Hub](https://hub.docker.com/r/aasm/sre-spade-instance)

Environment variables:
* `ACTIVE_SIMULATION_STATUS_ANNOUCEMENT_URL` - url where the active simulation process sends its status (i.e., http://127.0.0.1:8000/internal/instance/status)
* `ACTIVE_SIMULATION_STATUS_ANNOUCEMENT_PERIOD` - active simulation process status announcement period (i.e., 10)
* `AGENT_BACKUP_URL` - url where the agent backups are sent (i.e., http://127.0.0.1:8000/internal/simulation/agent_data)
* `AGENT_BACKUP_PERIOD` - agent backup period (i.e., 10)
* `AGENT_BACKUP_DELAY` - agent first backup delay after starting (i.e., 5)
* `AGENT_REGISTRATION_MAX_CONCURRENCY` - maximum number of concurrent agent registration requests to the communication server (i.e., 10)
* `AGENT_REGISTRATION_RETRY_AFTER` - delay before retrying an agent registration request (i.e., 5)
* `COMMUNICATION_SERVER_PASSWORD` - communication server password (i.e., password)
* `KAFKA_ADDRESS` - Kafka address (i.e., kafka:9092)
* `KAFKA_UPDATE_AGENT_INPUT_TOPIC_NAME` - Kafka topic name for agent input data (i.e., update_agent_input); it must match Kafka topic creator `UPDATE_AGENT_INPUT_TOPIC_NAME` value
* `LOG_LEVEL_AGENT` - log level for agents running in the simulation process; see spade-instance/src/simulation/code_generation.py (i.e., INFO)
* `LOG_LEVEL_KAFKA` - log level for spade-instance/src/kafka.py (i.e., INFO)
* `LOG_LEVEL_UVICORN_ACCESS` - log level for uvicorn server
* `LOG_LEVEL_REPEATED_TASKS` - log level for spade-instance/src/repeated_tasks.py (i.e., INFO)
* `LOG_LEVEL_ROUTERS` - log level for spade-instance/src/routers.py (i.e., INFO)
* `LOG_LEVEL_SIMULATION_CODE_GENERATION` - log level for spade-instance/src/simulation/code_generation.py (i.e., INFO)
* `LOG_LEVEL_SIMULATION_INITIALIZATION` - log level for spade-instance/src/simulation/initialization.py (i.e., INFO)
* `LOG_LEVEL_SIMULATION_MAIN` - log level for spade-instance/src/simulation/main.py (i.e., INFO)
* `LOG_LEVEL_SIMULATION_STATUS` - log level for spade-instance/src/simulation/status.py (i.e., INFO)
* `LOG_LEVEL_SPADE_BEHAVIOUR` - log level for SPADE behaviours (i.e., INFO)
* `LOG_LEVEL_STATE` - log level for spade-instance/src/state.py (i.e., INFO)
* `PORT` - listen port (i.e., 8000)
* `RELOAD` - reload application after detecting a change in source files (i.e., False); if set to True, it requires the following volume attached: spade-instance/src:/api/src
* `SIMULATION_LOAD_BALANCER_URL` - simulation load balancer url (i.e., http://simulation-load-balancer:8000)
* `SIMULATION_LOAD_BALANCER_ANNOUNCEMENT_PERIOD` - simulation load balancer announcement about the instance period (i.e., 10)
* `SIMULATION_PROCESS_HEALTH_CHECK_PERIOD` - running simulation health check period (i.e., 5)
* `WAIT_FOR_KAFKA_ADDRESS` - Kafka address (i.e., kafka:9092)
* `WAIT_FOR_KAFKA_TOPICS` - list of Kafka topic to wait for (i.e., update_agent_input)

### Translator <a name = "translator"></a>
The service's Web API enables the translation of Agents Assembly code using the `aasm` package (see `translator/src/routers.py`).

[Docker Hub](https://hub.docker.com/r/aasm/sre-translator)

Environment variables:
* `PORT` - listen port (i.e., 8000)
* `RELOAD` - reload application after detecting a change in source files (i.e., False); if set to True, it requires the following volume attached: translator/src:/api/src

Host port mapping (dev only):
* `8000`

### Zookeeper <a name = "zookeeper"></a>
It is a coordinator used to manage the Kafka service.
It maintains configuration information and provides synchronization and group services.

Environment variables:
* `ALLOW_ANONYMOUS_LOGIN` - [Bitnami docs](https://github.com/bitnami/bitnami-docker-zookeeper#configuration) (i.e., yes)

Host port mapping (dev only):
* `2181`
* `2182` (admin server)

## Contributing <a name = "contributing"></a>
Please follow the [contributing guide](CONTRIBUTING.md) if you wish to contribute to the project.
