from pydantic import Field, validator, root_validator
from typing import List, Optional

from .base import SnakeModel

# importar settings
settings = None


def get_model_dto(model_parameters):
    if model_parameters.model_name == "openvino":
        model = ModelOpenvinoDTO(model_parameters)
    else:
        pass


class MLModelDTO(SnakeModel):
    device: str = Field()
    name: str = Field()  # instead of model_name
    image_size: str = Field()
    model_path: str = Field("")
    class_id: int = Field(1)
    min_score: float = Field(0.25)
    tensorrt_precision: Optional[int] = Field(None)  # 16, 32 only. IN: config-x86-gpu-tensorrt.ini and config-jetson-tx2.ini

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
            raise ValueError('Not valid ML model. Try one of the following: "openvino", "openpifpaf_tensorrt", "mobilenet_ssd_v2", "openpifpaf", "yolov3",'
                             '"ssd_mobilenet_v2_coco", "ssd_mobilenet_v2_pedestrian_softbio", "posenet",'
                             '"pedestrian_ssd_mobilenet_v2", "pedestrian_ssdlite_mobilenet_v2".')

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

    """
    Necesito los modelos devices que aceptan que modelos.
    Las variables de los modelos.
    Lista de todos los modelos.
    
    HACERLA YO BIEN CASERA Y VER QUE ONDA.
    """
    # Root validators are called after field validators.
    @root_validator(skip_on_failure=True)
    def check_variables_for_models(cls, values):
        if values.get("name") == "openvino":
            pass
        elif values.get("name") == "openpifpaf_tensorrt":
            pass

    @root_validator(skip_on_failure=True)
    def check_models_and_device(cls, values):
        if values.get("name") == "openvino":
            if values.get("device") not in ["Jetson", "EdgeTPU", "Dummy", "x86"]:
                raise ValueError(f'The model {values.get("name")} is only supported in the following devices:'
                                 f'"Jetson", "EdgeTPU", "Dummy", "x86".')
        elif values.get("name") == "openvino":
            pass


    """
    @validator('name')
    def validate_variables(cls, name, values, **kwargs):
        if name == "openvino":
            openvino_variables = ("image_size", "model_path", "class_id", "min_score")
            if set(variables.keys()) != set(openvino_variables):
                raise ValueError('Variables do not correspond to the model.'
                                 'You have to specify: "image_size", "model_path", "class_id", "min_score"')
        elif model_name == "openpifpaf_tensorrt":
            pass
        # TODO: Check if this is the right way.

        return model_name
    """
