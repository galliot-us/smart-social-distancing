from pydantic import Field, validator, root_validator
from typing import List, Optional

from .base import SnakeModel


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
        if tensorrt_precision is not None:
            if tensorrt_precision not in [16, 32]:
                raise ValueError('Not valid tensorrt_precision. Accepted values: 16, 32')

        return tensorrt_precision

    @validator("name")
    def validate_name(cls, name):
        if name not in ["openvino", "openpifpaf_tensorrt", "mobilenet_ssd_v2", "openpifpaf", "yolov3",
                              "ssd_mobilenet_v2_coco", "ssd_mobilenet_v2_pedestrian_softbio", "posenet",
                              "pedestrian_ssd_mobilenet_v2", "pedestrian_ssdlite_mobilenet_v2"]:
            raise ValueError('Not valid ML model. Try one of the following: "openvino", "openpifpaf_tensorrt",'
                             '"mobilenet_ssd_v2", "openpifpaf", "yolov3",'
                             '"ssd_mobilenet_v2_coco", "ssd_mobilenet_v2_pedestrian_softbio", "posenet",'
                             '"pedestrian_ssd_mobilenet_v2", "pedestrian_ssdlite_mobilenet_v2".')
        return name

    @validator("image_size")
    def validate_image_size(cls, image_size):
        integers = image_size.split(",")

        if len(integers) != 3:
            raise ValueError('ImageSize must be a string with 3 numbers separated with commas. Ex: "30,30,40".')

        for x in integers:
            try:
                int(x)
            except ValueError:
                raise ValueError('ImageSize must be a string with 3 numbers separated with commas. Ex: "30,30,40".')

        return image_size

    # Root validators are called after each field validators success.

    @root_validator(skip_on_failure=True)
    def check_models_and_device(cls, values):
        if values.get("device") == "Jetson":
            if values.get("name") not in ["ssd_mobilenet_v2_coco", "ssd_mobilenet_v2_pedestrian_softbio",
                                          "openpifpaf_tensorrt"]:
                raise ValueError(f'The device {values.get("device")} only supports the following models:'
                                 f'"ssd_mobilenet_v2_coco", "ssd_mobilenet_v2_pedestrian_softbio",'
                                 f'"openpifpaf_tensorrt". ')
        elif values.get("device") == "EdgeTPU":
            if values.get("name") not in ["mobilenet_ssd_v2", "pedestrian_ssd_mobilenet_v2",
                                          "pedestrian_ssdlite_mobilenet_v2", "posenet"]:
                raise ValueError(f'The device {values.get("device")} only supports the following models:'
                                 f'"mobilenet_ssd_v2", "pedestrian_ssd_mobilenet_v2","pedestrian_ssdlite_mobilenet_v2",'
                                 f'"posenet". ')
        elif values.get("device") == "Dummy":
            # No restrictions on this model.
            pass
        elif values.get("device") in ["x86", "x86-gpu"]:
            if values.get("name") not in ["mobilenet_ssd_v2", "openvino", "openpifpaf", "openpifpaf_tensorrt",
                                          "yolov3"]:
                raise ValueError(f'The device {values.get("device")} only supports the following models:'
                                 f'"mobilenet_ssd_v2", "openvino","openpifpaf","openpifpaf_tensorrt"'
                                 f'"yolov3". ')

        return values

    @root_validator(skip_on_failure=True)
    def check_variables_for_models(cls, values):

        if values.get("name") == "ssd_mobilenet_v2_coco" or values.get("name") == "ssd_mobilenet_v2_pedestrian_softbio":
            pass

        elif values.get("name") == "openpifpaf_tensorrt":
            # image size x,x,y puede ser?
            if values.get("tensorrt_precision") is None:
                raise ValueError('The model "openpifpaf_tensorrt" requires the parameter "tensorrt_precision", and'
                                 'said parameter can be either 16 or 32.')

        elif values.get("name") == "mobilenet_ssd_v2":
            pass

        elif values.get("name") == "pedestrian_ssd_mobilenet_v2":
            pass

        elif values.get("name") == "pedestrian_ssdlite_mobilenet_v2":
            pass

        elif values.get("name") == "posenet":
            integers = values.get("image_size").split(",")

            if integers != ["1281", "721", "3"] and integers != ["641", "481", "3"] and integers != ["481", "353", "3"]:
                raise ValueError('ImageSize must be either one of the following options: "1281,721,3", "641,481,3" or'
                                 ' "481,353,3".')

        elif values.get("name") == "mobilenet_ssd_v2":
            pass

        elif values.get("name") == "openvino":
            pass

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
