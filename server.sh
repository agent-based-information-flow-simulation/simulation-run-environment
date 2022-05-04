#!/bin/bash

function usage() {
    echo "Usage: $0 {init|join|network|start|scale|stop|clean|stats|services|publish|unit-test|reload}"
    echo "       init: initialize the swarm cluster"
    echo "       join TOKEN IP:PORT: join the swarm cluster"
    echo "       network (REQUIRES SWARM CLUSTER): create shared networks for the swarm mode"
    echo "       start [-d: dev mode [-p: publish]] (REQUIRES SWARM CLUSTER): start the server"
    echo "       scale <SERVICE: data-processor, kafka-consumer, kafka-consumer-mongo, kafka-streams, spade-instance> <N: number of instances> (REQUIRES SWARM CLUSTER): scale the server to N SERVICE instances"
    echo "       stop: stop the server"
    echo "       clean: stop the server and remove all docker data"
    echo "       stats: print stats from all services"
    echo "       services: print all services"
    echo "       publish [-d: dev mode (REQUIRES SWARM CLUSTER)]: publish the images to a registry"
    echo "       unit-test SERVICE: run the unit-test suite for the given service"
    echo "       reload SERVICE (REQUIRES DEV MODE): rebuild and update the service"
    echo "       mongo-dump CONTAINER HOST_DESTINATION: dump the mongo database"
    echo "       mongo-restore CONTAINER HOST_SOURCE: restore the mongo database"
    echo ""
    echo "IMPORTANT: number of kafka-consumer/kafka-conumser-mongo/kafka-streams instances should be bigger or equal to the number of the topic partitions they read from"
    echo "           see UPDATE_AGENT_OUTPUT_TOPIC_PARTITIONS for kafka-consumer, UPDATE_AGENT_INPUT_TOPIC_PARTITIONS for kafka-consumer-mongo/kafka-streams"
    exit 1
}

function init() {
    if docker swarm init; then
        echo "swarm cluster initialized"
    else
        echo "failed to initialize swarm cluster"
    fi
}

function join() {
    if [ -z "$1" ]; then
        echo "missing token"
        usage
    fi
    if [ -z "$2" ]; then
        echo "missing address"
        usage
    fi
    if docker swarm join --token "$1" "$2"; then
        echo "swarm cluster joined"
    else
        echo "failed to join swarm cluster"
    fi
}

function network() {
    if docker network create --driver overlay --attachable sre-cs; then
        echo "[simulation run environment <-> communication server] created"
    else
        echo "[simulation run environment <-> communication server] failed to create"
    fi

    if docker network create --driver overlay --attachable li-sre; then
        echo "[local interface <-> simulation run environment] created"
    else
        echo "[local interface <-> simulation run environment] failed to create"
    fi
}

function start() {
    DEV=0
    PUBLISH=0
    while getopts dp opt; do
        case $opt in
            d) DEV=1 ;;
            p) PUBLISH=1 ;;
            *) usage ;;
        esac
    done

    if [ "$DEV" -eq "1" ]; then
        COMPOSE_FILE=docker-compose.dev.swarm.yml
        if [ "$PUBLISH" -eq "1" ]; then publish -d; fi
    else
        COMPOSE_FILE=docker-compose.swarm.yml
    fi

    if docker stack deploy -c ./"$COMPOSE_FILE" sre; then
        echo "OK"
    else
        echo ""
        echo "failed to start the server"
        echo ""
        echo "if you see the following error:"
        echo "failed to create service X: Error response from daemon: network Y not found"
        echo "then restart docker daemon (i.e. sudo systemctl restart docker) and run ./server.sh clean"
        echo ""
        echo "if you see the following error:"
        echo "network X is declared as external, but could not be found"
        echo "run the script with the network option to create the required networks"
    fi
}

function scale() {
    if [ -z "$1" ]; then
        echo "missing service name"
        usage
    elif [ -z "$2" ]; then
        echo "missing number of instances"
        usage
    fi
    docker service scale sre_"${1}"="${2}"
}

function stop() {
    docker stack rm sre
}

function clean() {
    stop
    docker swarm leave --force
    docker system prune --all --volumes
}

function stats() {
    docker stats
}

function services() {
    docker service ls
    echo ""
    echo "if you notice that some of the services are not up"
    echo "then stop the server, publish the images, create the shared networks, and start the server again"
    echo ""
    echo "sre_kafka-topic-creator is expected to run only once"
}

function publish() {
    local OPTIND
    DEV=0
    while getopts d opt; do
        case $opt in
            d) DEV=1 ;;
            *) usage ;;
        esac
    done

    if [ "$DEV" -eq "1" ]; then
        echo "creating local registry"
        if ! docker service ps -q registry > /dev/null 2>&1; then
            if ! docker service create --name registry --publish published=5000,target=5000 registry:2; then
                echo "failed to create registry"
                usage
            fi
        else
            echo "registry already exists"
        fi
        docker-compose -f docker-compose.dev.swarm.yml build --parallel
        docker-compose -f docker-compose.dev.swarm.yml push
    else
        docker-compose -f docker-compose.swarm.yml build --parallel
        docker-compose -f docker-compose.swarm.yml push
    fi
}

function unit-test() {
    if [ -z "${1}" ]; then
        echo "missing service name"
        usage
    fi
    docker-compose -f docker-compose.test.yml up "$1" --build
}

function reload() {
    if [ -z "${1}" ]; then
        echo "missing service name"
        usage
    fi
    docker-compose -f docker-compose.dev.swarm.yml build "${1}" && \
    docker-compose -f docker-compose.dev.swarm.yml push && \
    docker service update sre_"${1}" --force
}

function mongo-dump() {
    if [ -z "$1" ]; then
        echo "missing container name"
        usage
    elif [ -z "$2" ]; then
        echo "missing host destination"
        usage
    fi
    docker exec -it "${1}" mongodump --username root --password root --authenticationDatabase admin --db simulations --out /opt/bitnami/mongodb/dump && \
    docker cp "${1}":/opt/bitnami/mongodb/dump "${2}" && \
    docker exec -it "${1}" rm -rf /opt/bitnami/mongodb/dump
}

function mongo-restore() {
    if [ -z "$1" ]; then
        echo "missing container name"
        usage
    elif [ -z "$2" ]; then
        echo "missing host source"
        usage
    fi
    docker exec -it "${1}" mkdir -p /opt/bitnami/mongodb/dump && \
    docker cp "${2}" "${1}":/opt/bitnami/mongodb/dump && \
    docker exec -it "${1}" mongorestore --username root --password root --authenticationDatabase admin --db simulations --drop /opt/bitnami/mongodb/dump
}

case "${1}" in
    init) init ;;

    join) join "${2}" "${3}" ;;

    network) network ;;

    start) start "${@:2}" ;;

    scale) scale "${2}" "${3}" ;;

    stop) stop ;;

    clean) clean ;;

    stats) stats ;;

    services) services ;;

    publish) publish "${@:2}" ;;

    unit-test) unit-test "${2}" ;;

    reload) reload "${2}" ;;

    mongo-dump) mongo-dump "${2}" "${3}" ;;

    mongo-restore) mongo-restore "${2}" "${3}" ;;

    *) usage ;;
esac
