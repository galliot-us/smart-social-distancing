import cv2 as cv
import numpy as np
import os

from pathlib import Path
from pydantic import conlist, BaseModel
from scipy.spatial import distance
from .config import get_source_config_directory

class ConfigHomographyMatrix(BaseModel):
    pts_destination: conlist(conlist(float, min_items=2, max_items=2), min_items=4, max_items=4)

    class Config:
        schema_extra = {
            'example': {
                'pts_destination': [[130., 310.], [45., 420.], [275., 420.], [252., 310.]]
            }
        }


def compute_and_save_inv_homography_matrix(points: ConfigHomographyMatrix, destination: str):
    Path(os.path.dirname(destination)).mkdir(parents=True, exist_ok=True)
    pts_destination = np.float32(points.pts_destination)
    h, _ = cv.findHomography(
        np.float32([[0, 0], [0, 100], [100 , 100], [100, 0]]), pts_destination
    )
    h_inv = np.linalg.inv(h).flatten()
    h_inv = ' '.join(map(str, h_inv))
    with open(destination, 'w') as f:
        f.write('h_inv: ' + h_inv)


def get_camera_calibration_path(config, camera_id):
    return f"{get_source_config_directory(config)}/{camera_id}/homography_matrix/h_inverse.txt"
