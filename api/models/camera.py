import numpy as np
import cv2 as cv

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Tuple

from .base import EntityConfigDTO, NotificationConfig, SnakeModel


class CameraDTO(EntityConfigDTO, NotificationConfig):
    videoPath: str = Field(example='/repo/data/softbio_vid.mp4')
    tags: Optional[str] = Field("", example='kitchen,living_room')
    image: Optional[str] = Field("", example='Base64 image')
    distMethod: Optional[str] = Field("", example='CenterPointsDistance')
    liveFeedEnabled: bool = Field(True, example=True)
    hasBeenCalibrated: bool = Field(False, example=False)
    hasDefinedRoi: bool = Field(False, example=False)
    hasInOutBorder: bool = Field(False, example=False)


class CreateCameraDTO(CameraDTO):

    @validator('videoPath')
    def video_must_be_valid(cls, video_uri):
        error = False
        input_cap = cv.VideoCapture(video_uri)

        if input_cap.isOpened():
            _, cv_image = input_cap.read()
            if np.shape(cv_image) == ():
                error = True
        else:
            error = True

        input_cap.release()
        if error:
            raise ValueError('Failed to load video. The video URI is not valid')
        else:
            return video_uri


class CamerasListDTO(SnakeModel):
    cameras: List[CameraDTO]


class ImageModel(BaseModel):
    image: str

    class Config:
        schema_extra = {
            "example": {
                "image": "data:image/jpg;base64,iVBORw0KG..."
            }
        }


class VideoLiveFeedModel(BaseModel):
    enabled: bool


class ContourRoI(BaseModel):
    contour_roi: List[Tuple[int, int]]

    class Config:
        schema_extra = {
            'example': {
                'contour_roi': [[88, 58], [90, 284], [279, 284], [281, 58]]
            }
        }


class InOutBoundary(BaseModel):
    name: Optional[str] = Field("", example="Left Door")
    in_out_boundary: Tuple[Tuple[int, int], Tuple[int, int]]


class InOutBoundaries(BaseModel):
    in_out_boundaries: List[InOutBoundary]

    class Config:
        schema_extra = {
            "example": {
                "in_out_boundaries": [
                    {
                        "name": "Left Door",
                        "in_out_boundary": [[5, 5], [5, 240]]
                    },
                    {
                        "name": "Right Door",
                        "in_out_boundary": [[280, 5], [280, 240]]
                    },
                ]
            }
        }
