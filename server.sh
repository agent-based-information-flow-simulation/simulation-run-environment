#!/bin/bash

function usage() {
    echo "Usage: $0 {init|join|network|start|scale|stop|clean|stats|services|publish|unit-test}"
    echo "       init: initialize the swarm cluster"
    echo "       join TOKEN IP:PORT: join the swarm cluster"
    echo "       network (REQUIRES SWARM CLUSTER): create shared networks for the swarm mode"
    echo "       start [-n <N=1>: N spade instances] [-d: dev mode [-p: publish]] [-x: dev without swarm cluster [-s SERVICE: service to start]] (REQUIRES SWARM CLUSTER): start the server"
    echo "       scale N: scale the server to N spade instances"
    echo "       stop: stop the server"
    echo "       clean: stop the server and remove all docker data"
    echo "       stats: print stats from all services"
    echo "       services: print all services"
    echo "       publish [-d: dev mode (REQUIRES SWARM CLUSTER)]: publish the images to a registry"
    echo "       unit-test SERVICE: run the unit-test suite for the given service"
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
}

function start() {
    DEV=0
    N=1
    PUBLISH=0
    SERVICE=
    WITHOUT_SWARM=0
    while getopts dn:ps:x opt; do
        case $opt in
            d) DEV=1 ;;
            n) N=$OPTARG ;;
            p) PUBLISH=1 ;;
            s) SERVICE=$OPTARG ;;
            x) WITHOUT_SWARM=1 ;;
            *) usage ;;
        esac
    done

    if [ "$WITHOUT_SWARM" -eq "1" ]; then
        if [ ! -z "$SERVICE" ]; then
            docker-compose -f docker-compose.dev.yml up "$SERVICE" --build
        else
            docker-compose -f docker-compose.dev.yml up --build
        fi
        exit 0
    fi

    if [ "$DEV" -eq "1" ]; then
        COMPOSE_FILE=docker-compose.dev.swarm.yml
        if [ "$PUBLISH" -eq "1" ]; then publish -d; fi
    else
        COMPOSE_FILE=docker-compose.swarm.yml
    fi

    if docker stack deploy -c ./"$COMPOSE_FILE" sre; then
        if [ "$N" -gt "1" ]; then scale "$N"; fi
        echo "Server can be accessed on port 80"
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
    if [ -z "${1}" ]; then
        echo "missing number of instances"
        usage
    fi
    docker service scale sre_spade-instance="${1}"
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
        echo "creating local registry..." 
        docker service create --name registry --publish published=5000,target=5000 registry:2
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

case "${1}" in
    init) init ;;

    join) join "${2}" "${3}" ;;

    network) network ;;

    start) start "${@:2}" ;;

    scale) scale "${2}" ;;

    stop) stop ;;

    clean) clean ;;

    stats) stats ;;

    services) services ;;

    publish) publish "${@:2}" ;;

    unit-test) unit-test "${2}" ;;

    *) usage ;;
esac
