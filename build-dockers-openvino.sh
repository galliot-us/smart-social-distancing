#!/bin/bash
docker build -f x86-openvino.Dockerfile -t "neuralet/smart-social-distancing:latest-x86_64_openvino" 
docker build -f api.Dockerfile -t "neuralet/smart-social-distancing:latest-api" .
docker build -f frontend.Dockerfile -t "neuralet/smart-social-distancing:latest-frontend" .
docker build -f run-frontend.Dockerfile -t "neuralet/smart-social-distancing:latest-run-frontend" .
