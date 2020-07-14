#!/bin/bash
API_PORT=$1
DASHBOARD_PORT=$2
QUEUE_PORT=$3

echo "running openvino docker ..."
docker run --rm -p $QUEUE_PORT:$QUEUE_PORT -v "$PWD/data":/repo/data neuralet/smart-social-distancing:latest-x86_64_openvino &
echo "running api docker... "
docker run --rm -p $QUEUE_PORT:$QUEUE_PORT -p $API_PORT:$API_PORT -v "$PWD":/repo neuralet/smart-social-distancing:latest-api &
echo "run dashboard ..."
docker run --rm -p $DASHBOARD_PORT:$DASHBOARD_PORT -v "$PWD/data":/repo/data neuralet/smart-social-distancing:latest-run-frontend
