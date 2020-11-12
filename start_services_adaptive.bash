#!/bin/bash

CONFIG="$1"
# check if model name is correct
model=$(sed -nr "/^\[Detector\]/ { :l /^Name[ ]*=/ { s/.*=[ ]*//; p; q;}; n; b l;}" $CONFIG)

if [ $model != "mobilenet_ssd_v2" ]; then
    echo "the selected model must be 'mobilenet_ssd_v2' in adaptive learning setup but it is $model"
    kill -SIGUSR1 `ps --pid $$ -oppid=`
    exit 1
fi

bash /repo/sample_startup.bash $CONFIG  &
bash /repo/update_model.bash $CONFIG &
#trap "echo exitting because the model name is not compatible with adaptive learning.>&2;kill $(jobs -p)" SIGUSR1
python3 create_reports.py --config $CONFIG &
python3 run_processor_core.py --config $CONFIG &
python3 run_processor_api.py --config $CONFIG
