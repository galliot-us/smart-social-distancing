#!/bin/bash
config="$1"

imageSize=$(sed -nr "/^\[Detector\]/ { :l /^ImageSize[ ]*=/ { s/.*=[ ]*//; p; q;}; n; b l;}" $config)
IFS=',' read -a marray <<< "$imageSize"
width=${marray[0]}
height=${marray[1]}
mkdir -p /repo/data/onnx
onnxName="/repo/data/onnx/openpifpaf_resnet50_${width}_${height}.onnx"
if [ ! -f $onnxName ]; then
	echo ############## exporting ONNX from OpenPifPaf ##################
	python3 -m openpifpaf.export_onnx --outfile $onnxName  --checkpoint resnet50  --input-width $width --input-height $height
fi

mkdir -p /repo/data/tensorrt

precision=$(sed -nr "/^\[Detector\]/ { :l /^TensorrtPrecision[ ]*=/ { s/.*=[ ]*//; p; q;}; n; b l;}" $config)
tensorrtName="/repo/data/tensorrt/openpifpaf_resnet50_${width}_${height}_d${precision}.trt"

if [ ! -f $tensorrtName ]; then
	echo ############## Generating TensorRT Engine ######################
	onnx2trt $onnxName -o $tensorrtName -d $precision -b 1
fi	


