#!/bin/bash
if ! curl --fail -o /dev/null -m 5 0.0.0.0:8000/docs; then
    # The api service is not working or is giving timeout.
    # Restart it
    eval "supervisorctl -c supervisord.conf restart api"
fi;
if fatalError=$(supervisorctl -c supervisord.conf status all | grep -i "FATAL\|UNKNOWN"); then
    exit 1;
else
    exit 0;
fi
