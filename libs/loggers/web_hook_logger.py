import logging
import requests

from requests.exceptions import ConnectionError

from .logger_template import LoggerTemplate

logger = logging.getLogger(__name__)


class WebHookLogger(LoggerTemplate):

    def __init__(self, config, camera_id):
        self.camera_id = camera_id
        self.web_hook_endpoint = config.get_section_dict("Logger")["WebHooksEndpoint"]

    def log_objects(self, objects, violating_objects, violating_objects_index_list, violating_objects_count,
                    detected_objects_cout, environment_score, time_stamp, version):
        request_data = {
            "version": version,
            "timestamp": time_stamp,
            "detected_objects": detected_objects_cout,
            "violating_objects": violating_objects_count,
            "environment_score": environment_score,
            "detections": str(objects),
            "violations_indexes": str(violating_objects_index_list)
        }
        try:
            requests.put(self.web_hook_endpoint, data=request_data)
        except ConnectionError:
            logger.error(f"Connection with endpoint {self.web_hook_endpoint} can't be established")
