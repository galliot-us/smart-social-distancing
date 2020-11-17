#!/bin/bash
config="$1"

MODEL_DIR="/repo/adaptive-learning/data/student_model/frozen_graph/"
sleep 20

# start watching files
inotifywait -e modify -m $MODEL_DIR | grep '\s\+detect.tflite$' --line-buffered |
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


    response=$(curl 0.0.0.0:8000/start-process-video)
    if [ "$response" != true ] ; then
        echo "restarting failed, trying again in 5 seconds!"
    elif [ "$response" = true ] ; then
     	echo "ok video is going to be processed with updated model ..."
    fi

    done

