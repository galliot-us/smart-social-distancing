#!/bin/bash
# This script generates a TensorRT engine from pretrained FastPose model.
# Must be run inside the Jetson Container
#
# Usage:
# bash generate_pose_tensorrt.bash [ONNX FILE URL] [Stored on FLOAT16(fp16)/ FLOAT32(fp32)] [BATCH_SIZE]
# Example: bash generate_pose_tensorrt.bash https://media.githubusercontent.com/media/neuralet/models/master/ONNX/fastpose/fastpose_resnet50_256_192_tf.onnx fp16 8
# NOTE: For Jetson TX2 batch size 8 is recommended. For other devices you can test multiple batch sizes to find the optimum one.

# download link to onnx model
onnx_url=$1

# float16=fp16 or float32=fp32 
precision=$2

#TensorRT batch_size, 8 is tested on Jetson TX2
batch_size=$3
tensorrt_model_name="fast_pose_"$precision"_b"$batch_size".trt"
workspace=0
if (( $batch_size > 1 )); then
	workspace=4096
else
	workspace=2048
fi
mkdir -p data/jetson
wget $1 -O "data/jetson/model_static.onnx"

/usr/src/tensorrt/bin/trtexec --onnx=data/jetson/model_static.onnx --saveEngine=data/jetson/$tensorrt_model_name --$precision --batch=$batch_size --workspace=$workspace

rm data/jetson/model_static.onnx
