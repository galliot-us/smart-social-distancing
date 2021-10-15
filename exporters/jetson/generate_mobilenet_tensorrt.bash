#!/bin/bash
# This script generates a TensorRT engine from pretrained Tensorflow SSD Mobilenet v2 COCO model.

echo $relative_path
if [ $# -eq 2 ]
then
	pb_file=$1
	adaptive_model=1
	num_classes=$2

else 
	if [ ! -f "repo$relative_path/data/jetson/ssd_mobilenet_v2_coco_2018_03_29.tar.gz"  ]; then
		echo "downloading ssd_mobilenet_v2_coco_2018_03_29 ..."
		wget http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz -P repo$relative_path/data/jetson/
	fi
	tar -xvf repo$relative_path/data/jetson/ssd_mobilenet_v2_coco_2018_03_29.tar.gz --no-same-owner -C repo$relative_path/data/jetson/
	pb_file="repo$relative_path/data/jetson/ssd_mobilenet_v2_coco_2018_03_29/frozen_inference_graph.pb"
	adaptive_model=0
	num_classes=1

fi


echo "************  Generating TensorRT from: $pb_file  **************"
python3 repo$relative_path/exporters/jetson/trt_exporter.py --pb_file $pb_file --out_dir repo$relative_path/data/jetson --neuralet_adaptive_model $adaptive_model --num_classes $num_classes