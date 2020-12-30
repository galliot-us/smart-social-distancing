#!/bin/bash
config="$1"
run_on_jetson="$2"

imageSize=$(sed -nr "/^\[Detector\]/ { :l /^ImageSize[ ]*=/ { s/.*=[ ]*//; p; q;}; n; b l;}" $config)
IFS=',' read -a marray <<< "$imageSize"
width=${marray[0]}
height=${marray[1]}

mkdir -p /repo/data/onnx
onnx_name_openpifpaf="/repo/data/onnx/openpifpaf_resnet50_${width}_${height}.onnx"
onnx_name_face_mask="/repo/data/onnx/ofm_face_mask.onnx"

onnx_openpifpaf_download_url="https://media.githubusercontent.com/media/neuralet/neuralet-models/master/ONNX/openpifpaf_12a4/openpifpaf_resnet50_${width}_${height}.onnx"

if [[ ! $run_on_jetson ]] && [[ ! -f $onnx_name_openpifpaf ]]; then
    echo "############## exporting ONNX from OpenPifPaf ##################"
    python3 -m openpifpaf.export_onnx --outfile $onnx_name_openpifpaf  --checkpoint resnet50  --input-width $width --input-height $height
   
elif [[ $run_on_jetson ]] && [[ ! -f $onnx_name_openpifpaf  ]]; then
    wget $onnx_openpifpaf_download_url -O $onnx_name_openpifpaf
fi

if [ ! -f $onnx_name_face_mask ]; then
    wget https://media.githubusercontent.com/media/neuralet/neuralet-models/master/ONNX/OFMClassifier/OFMClassifier.onnx -O $onnx_name_face_mask
fi

mkdir -p /repo/data/tensorrt

precision_detector=$(sed -nr "/^\[Detector\]/ { :l /^TensorrtPrecision[ ]*=/ { s/.*=[ ]*//; p; q;}; n; b l;}" $config)
tensorrt_name_openpifpaf="/repo/data/tensorrt/openpifpaf_resnet50_${width}_${height}_d${precision_detector}.trt"

if [ ! -f $tensorrt_name_openpifpaf ]; then
    echo "############## Generating TensorRT Engine for openpifpaf ######################"
    onnx2trt $onnx_name_openpifpaf -o $tensorrt_name_openpifpaf -d $precision_detector -b 1
fi

precision_classifier=$(sed -nr "/^\[Classifier\]/ { :l /^TensorrtPrecision[ ]*=/ { s/.*=[ ]*//; p; q;}; n; b l;}" $config)
tensorrt_name_face_mask="/repo/data/tensorrt/ofm_face_mask_d${precision_classifier}.trt"
ls $onnx_name_face_mask
if [ ! -f $tensorrt_name_face_mask ]; then
    echo "############## Generating TensorRT Engine for face_mask classifier ##############"
    onnx2trt $onnx_name_face_mask -o $tensorrt_name_face_mask -d $precision_classifier -b 1
fi

