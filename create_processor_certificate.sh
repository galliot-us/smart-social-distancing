#!/bin/bash
if [[ $# -eq 0 ]]; then
    echo "IP argument is required"
    exit 0;
fi
IP=$1
IP_NAME=${IP//./_}
mkdir -p ./certs
openssl genrsa -out ./certs/$IP_NAME.key 2048
openssl req -new -key ./certs/$IP_NAME.key -out ./certs/$IP_NAME.csr
# Create a config file for the extensions
echo -e 'authorityKeyIdentifier=keyid,issuer\nbasicConstraints=CA:FALSE' >> ./certs/$IP_NAME.ext
echo -e 'keyUsage=digitalSignature,nonRepudiation,keyEncipherment,dataEncipherment' >> ./certs/$IP_NAME.ext
echo -e 'subjectAltName=IP:'$IP >> ./certs/$IP_NAME.ext
openssl x509 -req -in ./certs/$IP_NAME.csr -CA ./certs/ca/processorCA.pem -CAkey ./certs/ca/processorCA.key -CAcreateserial -out ./certs/$IP_NAME.crt -days 825 -sha256 -extfile ./certs/$IP_NAME.ext
