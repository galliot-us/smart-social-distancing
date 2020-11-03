#!/bin/bash
if [[ $# -eq 0 ]]; then
    echo "IP argument is required"
    exit 0;
fi
IP=$1
IP_NAME=${IP//./_}
mkdir -p ./certificates/processor
openssl genrsa -out ./certificates/processor/$IP_NAME.key 2048
openssl req -new -key ./certificates/processor/$IP_NAME.key -out ./certificates/processor/$IP_NAME.csr
# Create a config file for the extensions
echo -e 'authorityKeyIdentifier=keyid,issuer\nbasicConstraints=CA:FALSE' >> ./certificates/processor/$IP_NAME.ext
echo -e 'keyUsage=digitalSignature,nonRepudiation,keyEncipherment,dataEncipherment' >> ./certificates/processor/$IP_NAME.ext
echo -e 'subjectAltName=IP:'$IP >> ./certificates/processor/$IP_NAME.ext
openssl x509 -req -in ./certificates/processor/$IP_NAME.csr -CA ./certificates/ca/processorCA.pem -CAkey ./certificates/ca/processorCA.key -CAcreateserial -out ./certificates/processor/$IP_NAME.crt -days 825 -sha256 -extfile ./certificates/processor/$IP_NAME.ext
