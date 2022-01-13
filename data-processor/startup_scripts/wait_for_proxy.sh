#!/bin/bash
while ! nc -z data-processor-proxy 5555; do sleep 1; done;
echo "data-processor-proxy is up"
