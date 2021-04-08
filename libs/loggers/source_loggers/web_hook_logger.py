import logging
import requests

from requests.exceptions import ConnectionError
from starlette import status

from .raw_data_logger import RawDataLogger

logger = logging.getLogger(__name__)


class WebHookLogger(RawDataLogger):

    def __init__(self, config, source: str, logger: str):
        super().__init__(config, source, logger)
        self.web_hook_endpoint = config.get_section_dict(logger)["Endpoint"]
        self.web_hook_authorization = config.get_section_dict(logger)["Authorization"]
        self.pending_requests = []

    def log_objects(self, objects, violating_objects, violating_objects_index_list, violating_objects_count,
                    detected_objects_cout, environment_score, time_stamp, version):
        request_data = {
            "camera_id": self.camera_id,
            "version": version,
            "timestamp": time_stamp,
            "detected_objects": detected_objects_cout,
            "violating_objects": violating_objects_count,
            "environment_score": environment_score,
            "detections": str(objects),
            "violations_indexes": str(violating_objects_index_list)
        }
        headers = {"content-type": "application/json"}
        if self.web_hook_authorization:
            headers["Authorization"] = self.web_hook_authorization
        self.pending_requests.append(request_data)
        try:
            response = requests.put(self.web_hook_endpoint, json=self.pending_requests, headers=headers)
        except ConnectionError:
            logger.error(f"Connection with endpoint {self.web_hook_endpoint} can't be established")
        except Exception as e:
            logger.error(f"Unexpected error connecting with {self.web_hook_endpoint}")
            logger.error(e)
        else:
            if response.status_code == status.HTTP_200_OK:
                self.pending_requests = []
            else:
                logger.error(f"Webhook endpoint returns status {response.status_code}")
                logger.error(response.json())

    def update(self, cv_image, objects, post_processing_data, fps):
        if self.web_hook_endpoint:
            super().update(cv_image, objects, post_processing_data, fps)
