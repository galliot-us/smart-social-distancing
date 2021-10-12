"""build_engine.py

This script converts a SSD model (pb) to UFF and subsequently builds
the TensorRT engine.

Input : spces of a ssd frozen inference graph in config.ini file
Output: TensorRT Engine file

Reference:
   https://github.com/jkjung-avt/tensorrt_demos/blob/master/ssd/build_engine.py
"""


import os
import ctypes
import argparse
import wget

import uff
import tensorrt as trt
import graphsurgeon as gs
import numpy as np
import add_plugin_and_preprocess_ssd_mobilenet as plugin

def export_trt(pb_file, output_dir, num_classes=90, neuralet_adaptive_model=1):
    """
    Exports the Tensorflow pb models to TensorRT engines.
    Args:
        pb_file: The path of input pb file
        output_dir: A directory to store the output files
        num_classes: Detector's number of classes
    """
    lib_flatten_concat_file = "exporters/libflattenconcat.so.6"
    # initialize
    if trt.__version__[0] < '7':
        ctypes.CDLL(lib_flatten_concat_file)
    TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
    trt.init_libnvinfer_plugins(TRT_LOGGER, '')
    
    # compile the model into TensorRT engine
    model = "ssd_mobilenet_v2_coco"

    if not os.path.isfile(pb_file):
        raise FileNotFoundError('model does not exist under: {}'.format(pb_file))

    if not os.path.isdir(output_dir):
        print("the provided output directory : {0} is not exist".format(output_dir))
        print("creating output directory : {0}".format(output_dir))
        os.makedirs(output_dir, exist_ok=True)


    dynamic_graph = plugin.add_plugin_and_preprocess(
        gs.DynamicGraph(pb_file),
        model,
        num_classes,
        neuralet_adaptive_model)
    model_file_name = ".".join((pb_file.split("/")[-1]).split(".")[:-1])
    uff_path = os.path.join(output_dir, model_file_name + ".uff")
    _ = uff.from_tensorflow(
        dynamic_graph.as_graph_def(),
        output_nodes=['NMS'],
        output_filename=uff_path,
        text=True,
        debug_mode=False)
    input_dims = (3, 300, 300)
    with trt.Builder(TRT_LOGGER) as builder, builder.create_network() as network, trt.UffParser() as parser:
        builder.max_workspace_size = 1 << 28
        builder.max_batch_size = 1
        builder.fp16_mode = True

        parser.register_input('Input', input_dims)
        parser.register_output('MarkOutput_0')
        parser.parse(uff_path, network)
        engine = builder.build_cuda_engine(network)
        
        buf = engine.serialize()
        engine_path = os.path.join(output_dir, model_file_name + ".bin")
        with open(engine_path, 'wb') as f:
            f.write(buf)
        print("your model has been converted to trt engine successfully under : {}".format(engine_path))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="This script exports a pb tensorflow model to a TRT engine")
    parser.add_argument("--pb_file", type=str, required=True, help="the path of input pb file")
    parser.add_argument("--out_dir", type=str, required=True, help="a directory to store the output files")
    parser.add_argument("--num_classes", type=int, default=90, help="detector's number of classes")
    parser.add_argument("--neuralet_adaptive_model", type=int, default=1, help="1 if the model is trained by Neuralet adaptive learning,0 if not")
    args = parser.parse_args()
    pb_file = args.pb_file
    output_dir = args.out_dir
    num_classes = args.num_classes
    neuralet_adaptive_model = args.neuralet_adaptive_model
    export_trt(pb_file=pb_file, output_dir=output_dir, num_classes=num_classes, neuralet_adaptive_model=neuralet_adaptive_model)

