#!/bin/bash
mkdir -p ./certs/ca
openssl genrsa -des3 -out ./certs/ca/processorCA.key 2048
openssl req -x509 -new -nodes -key ./certs/ca/processorCA.key -sha256 -days 825 -out ./certs/ca/processorCA.pem

