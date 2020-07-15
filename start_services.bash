#!/bin/bash
CONFIG="$1"
python3 run_processor_core.py --config $CONFIG & 
python3 run_processor_api.py --config $CONFIG 
