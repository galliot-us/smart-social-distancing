#!/bin/bash
CONFIG="$1"
python3 start_engine.py --config $CONFIG & 
python3 start_api.py --config $CONFIG 
