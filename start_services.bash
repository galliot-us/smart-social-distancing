#!/bin/bash
CONFIG="$1"
#bash /repo/sample_startup.bash $CONFIG  &
bash /repo/sample_startup.bash $CONFIG  &
python3 create_reports.py --config $CONFIG &
>>>>>>> 089b802dbe4cfc7d8ceab73eb23690ce7ec6f487
python3 run_processor_core.py --config $CONFIG & 
python3 run_processor_api.py --config $CONFIG
