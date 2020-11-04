#!/bin/bash
CONFIG="$1"
bash /repo/sample_startup.bash $CONFIG  &
bash /repo/update_model.bash $CONFIG &
python3 create_reports.py --config $CONFIG &
python3 run_processor_core.py --config $CONFIG &
python3 run_processor_api.py --config $CONFIG
