#!/bin/bash
config="$1"

# check if model name is correct
line=$(cat $config | grep Name)
model="$(cut -d'=' -f2 <<<"$line")"
if [ $model != "mobilenet_ssd_v2" ]; then
    echo "the selected model must be 'mobilenet_ssd_v2' in adaptive learning setup but it is $model"
    exit 1
fi

MODEL_DIR="/repo/adaptive-learning/data/student_model/frozen_graph/"

# start watching files
inotifywait -e modify,create --exclude "[^detect.tflite]$" -m $MODEL_DIR |
  while read dir action file; do
    echo "Start Updating Model ..."
    sleep 5
    edgetpu_compiler $MODEL_DIR/detect.tflite -o /repo/data/edgetpu/
    mv /repo/data/edgetpu/detect_edgetpu.tflite /repo/data/edgetpu/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite
    # restarting core
    stop_response=$(curl 0.0.0.0:8000/stop-process-video)
    if [ "$stop_response" = true ] ; then
      echo "core stopped sucessfuly"
      sleep 5
    elif [ "$stop_response" != true ] ; then
      echo "failed to stopping core , ..."
    fi


    response=$(curl 0.0.0.0:8000/process-video-cfg)
    if [ "$response" != true ] ; then
        echo "restarting failed, trying again in 5 seconds!"
    elif [ "$response" = true ] ; then
     	echo "ok video is going to be processed with updated model ..."
    fi

    done

