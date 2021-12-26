#!/bin/bash
INSTANCES=$1
PER_INSTANCE=$2
mkdir -p logs
for ((i=1;i<=INSTANCES;i++)); do
    python -u main.py -n $PER_INSTANCE -d $i > ./logs/out_"${i}" 2>&1 &
done
