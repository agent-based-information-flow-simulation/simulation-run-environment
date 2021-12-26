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

```
docker-compose -f COMPOSE_FILE up
```

For the local development use the `.dev` compose file. To run unit tests use the `.test` compose file.

## Usage <a name = "usage"></a>

After starting the `.dev` compose file, the server in accessible on localhost.
* port `80` - entrypoint
* port `8000` - translator
* port `8001` - graph generator
* port `8002` - simulation load balancer
* port `27017` - mongodb
* port `27018` - mongodb express
