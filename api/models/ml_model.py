from pydantic import Field, validator, root_validator
from typing import List, Optional

from .base import SnakeModel


MODELS_DEVICES = {
    "Jetson": ["ssd_mobilenet_v2_coco", "ssd_mobilenet_v2_pedestrian_softbio", "openpifpaf_tensorrt"],
    "EdgeTPU": ["mobilenet_ssd_v2", "pedestrian_ssd_mobilenet_v2", "pedestrian_ssdlite_mobilenet_v2", "posenet"],
    "Dummy": ["openvino", "openpifpaf_tensorrt", "mobilenet_ssd_v2", "openpifpaf", "yolov3", "ssd_mobilenet_v2_coco",
              "ssd_mobilenet_v2_pedestrian_softbio", "posenet", "pedestrian_ssd_mobilenet_v2",
              "pedestrian_ssdlite_mobilenet_v2"],  # All available models.
    "x86": ["mobilenet_ssd_v2", "openvino", "openpifpaf", "openpifpaf_tensorrt", "yolov3"],
    "x86-gpu": ["mobilenet_ssd_v2", "openvino", "openpifpaf", "openpifpaf_tensorrt", "yolov3"]
}


class MLModelDTO(SnakeModel):
    device: str = Field(example="Jetson")
    name: str = Field(example="openvino")
    image_size: str = Field(example="300,300,3")
    model_path: str = Field("")
    class_id: int = Field(1)
    min_score: float = Field(0.25, example=0.30)
    tensorrt_precision: Optional[int] = Field(None, example=32)

    @validator("device")
    def validate_device(cls, device):
        if device not in ["x86", "x86-gpu", "Jetson", "EdgeTPU", "Dummy"]:
            raise ValueError('Not valid Device. Try one of the following: "x86", "x86-gpu", "Jetson", "EdgeTPU",'
                             '"Dummy".')
        return device

    @validator("tensorrt_precision")
    def validate_tensorrt_precision(cls, tensorrt_precision):
        if tensorrt_precision is not None and tensorrt_precision not in [16, 32]:
            raise ValueError('Not valid tensorrt_precision. Accepted values: 16, 32')

        return tensorrt_precision

    @validator("image_size")
    def validate_image_size(cls, image_size):
        integers = image_size.split(",")

        if len(integers) != 3:
            raise ValueError('ImageSize must be a string with 3 numbers separated with commas. Ex: "30,30,40".')

        try:
            [int(x) for x in integers]
        except ValueError:
            raise ValueError('ImageSize must be a string with 3 numbers separated with commas. Ex: "30,30,40".')

        return image_size

    # Root validators are called after each field validators success.

    @root_validator(skip_on_failure=True)
    def check_models_and_device(cls, values):
        if values.get("device") == "Jetson":
            if values.get("name") not in MODELS_DEVICES["Jetson"]:
                raise ValueError(f'The device {values.get("device")} only supports the following models:'
                                 f' {MODELS_DEVICES["Jetson"]}. ')

        elif values.get("device") == "EdgeTPU":
            if values.get("name") not in MODELS_DEVICES["EdgeTPU"]:
                raise ValueError(f'The device {values.get("device")} only supports the following models:'
                                 f' {MODELS_DEVICES["EdgeTPU"]}. ')

        elif values.get("device") == "Dummy":
            # No restrictions on this model.
            # All available models.
            if values.get("name") not in MODELS_DEVICES["Dummy"]:
                raise ValueError(f'The device {values.get("device")} only supports the following models:'
                                 f' {MODELS_DEVICES["Dummy"]}. ')

        elif values.get("device") == "x86":
            if values.get("name") not in MODELS_DEVICES["x86"]:
                raise ValueError(f'The device {values.get("device")} only supports the following models:'
                                 f' {MODELS_DEVICES["x86"]}. ')

        elif values.get("device") == "x86-gpu":
            if values.get("name") not in MODELS_DEVICES["x86-gpu"]:
                raise ValueError(f'The device {values.get("device")} only supports the following models:'
                                 f' {MODELS_DEVICES["x86-gpu"]}. ')

        return values

    @root_validator(skip_on_failure=True)
    def check_variables_for_models(cls, values):

        if values.get("name") in ["ssd_mobilenet_v2_coco", "ssd_mobilenet_v2_pedestrian_softbio", "mobilenet_ssd_v2",
                                  "pedestrian_ssd_mobilenet_v2", "pedestrian_ssdlite_mobilenet_v2", "mobilenet_ssd_v2",
                                  "openvino"]:
            pass

        elif values.get("name") == "openpifpaf_tensorrt":
            if values.get("tensorrt_precision") is None:
                raise ValueError('The model "openpifpaf_tensorrt" requires the parameter "tensorrt_precision", and'
                                 'said parameter can be either 16 or 32.')

            integers = values.get("image_size").split(",")
            if int(integers[0]) % 16 != 1 or int(integers[0]) % 16 != 1:
                raise ValueError('First two values of ImageSize must be multiples of 16 plus 1 for openpifpaf_tensorrt.'
                                 ' Ex: "641,369,3".')

        elif values.get("name") == "posenet":
            integers = values.get("image_size").split(",")

            if integers != ["1281", "721", "3"] and integers != ["641", "481", "3"] and integers != ["481", "353", "3"]:
                raise ValueError('ImageSize must be either one of the following options: "1281,721,3", "641,481,3" or'
                                 ' "481,353,3".')

        elif values.get("name") == "openpifpaf":
            if values.get("image_size").split(",") != ["1281", "721", "3"]:
                raise ValueError('ImageSize must be 1281,721,3 for the model "openpifpaf".')

        elif values.get("name") == "yolov3":
            integers = values.get("image_size").split(",")

            reminder_one = int(integers[0]) % 32
            reminder_two = int(integers[1]) % 32

            if reminder_one or reminder_two != 0:
                raise ValueError('For yolov3 model the ImageSize MUST be w = h = 32x e.g: x= 13=> ImageSize = 416,'
                                 '416,3. ')

        return values
