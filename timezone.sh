#!/bin/bash

# Look for file inside a zoneinfo dir to which the symlink points (Such as US/Pacific or America/Montevideo)
echo `ls -la /etc/ | grep -o '/zoneinfo/.*' | awk '{gsub("/zoneinfo/",""); print }'`
