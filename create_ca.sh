#!/bin/bash
mkdir -p ./certificates/ca
openssl genrsa -des3 -out ./certificates/ca/processorCA.key 2048
openssl req -x509 -new -nodes -key ./certificates/ca/processorCA.key -sha256 -days 825 -out ./certificates/ca/processorCA.pem

