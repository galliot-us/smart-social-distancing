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

if [[ ! $run_on_jetson ]] && [[ ! -f $onnx_name_openpifpaf ]]; then
    echo "############## exporting ONNX from OpenPifPaf ##################"
    python3 -m openpifpaf.export_onnx --outfile $onnx_name_openpifpaf  --checkpoint resnet50  --input-width $width --input-height $height
   
elif [[ $run_on_jetson ]] && [[ ! -f $onnx_name_openpifpaf  ]]; then
    wget https://media.githubusercontent.com/media/neuralet/neuralet-models/c874b2bcee0521d770d3480ed5fef25643160abd/ONNX/openpifpaf_12a4/openpifpaf_resnet50_321_193.onnx -O $onnx_name_openpifpaf
fi

if [ ! -f $onnx_name_face_mask ]; then
    wget https://media.githubusercontent.com/media/neuralet/neuralet-models/c874b2bcee0521d770d3480ed5fef25643160abd/ONNX/OFMClassifier/OFMClassifier.onnx -O $onnx_name_face_mask
fi

mkdir -p /repo/data/tensorrt

precision=$(sed -nr "/^\[Detector\]/ { :l /^TensorrtPrecision[ ]*=/ { s/.*=[ ]*//; p; q;}; n; b l;}" $config)
tensorrt_name_openpifpaf="/repo/data/tensorrt/openpifpaf_resnet50_${width}_${height}_d${precision}.trt"

if [ ! -f $tensorrt_name_openpifpaf ]; then
    echo "############## Generating TensorRT Engine for openpifpaf ######################"
    onnx2trt $onnx_name_openpifpaf -o $tensorrt_name_openpifpaf -d $precision -b 1
fi

tensorrt_name_face_mask="/repo/data/tensorrt/ofm_face_mask_d${precision}.trt"

if [ ! -f $tensorrt_name_face_mask ]; then
    echo "############## Generating TensorRT Engine for face_mask classifier ##############"
    onnx2trt $onnx_name_face_mask -o $tensorrt_name_face_mask -d $precision -b 1
fi

