#!/bin/bash
if [[ $# -eq 0 ]]; then
    echo "Config file argument is required"
    exit 0;
fi
config="$1"
if sslEnabled=$(cat $config | grep -i "SSLEnabled = " | grep -i "true\|yes\|1"); then
    docs_url=https://0.0.0.0:8000/docs
else
    docs_url=http://0.0.0.0:8000/docs
fi
curl -k --fail $docs_url || exit 1
