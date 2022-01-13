# Simulation Run Environment

## Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)

## About <a name = "about"></a>

Simulation run environment.

## Getting Started <a name = "getting_started"></a>

### Prerequisites

```
docker
docker-compose
```

### Installing
Use the `server.sh` utility script.
```
./server.sh help
```

## Usage <a name = "usage"></a>

After starting the `.dev.yml` compose file, the server in accessible on localhost.
* port `80` - simulation load balancer
* port `6379` - redis
* port `7474` - neo4j http access
* port `7687` - neo4j bolt access
* port `8000` - translator
* port `8001` - graph generator
* port `8002` - data processor proxy
* port `9000` - spade instance
