#!/bin/bash
while ! nc -z db 7474; do sleep 1; done;
echo "db is up"
