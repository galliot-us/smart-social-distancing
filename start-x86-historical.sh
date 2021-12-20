#!/bin/bash
docker run -it -p 8300:8000 -v "$PWD":/repo -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-x86_64 /repo/run_historical_metrics.sh
