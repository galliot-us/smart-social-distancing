#!/bin/bash
CONFIG="$1"
python3 processor_core.py --config $CONFIG & 
python3 processor_api.py --config $CONFIG 
