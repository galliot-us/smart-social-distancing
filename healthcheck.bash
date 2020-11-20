#!/bin/bash
if fatalError=$(supervisorctl -c supervisord.conf status all | grep -i "FATAL\|UNKNOWN"); then
    exit 1;
else
    exit 0;
fi
