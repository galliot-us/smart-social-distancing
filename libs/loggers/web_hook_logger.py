import logging
import requests

from requests.exceptions import ConnectionError

logger = logging.getLogger(__name__)


class WebHookLogger:

    def __init__(self, config, camera_id):
        self.camera_id = camera_id
        self.web_hook_endpoint = config.get_section_dict("Logger")["WebHooksEndpoint"]

    def log_objects(self, objects, violating_objects, violating_objects_index_list, violating_objects_count,
                    detected_objects_cout, environment_score, time_stamp, version):
        request_data = {
            'Version': version,
            'Timestamp': time_stamp,
            'DetectedObjects': detected_objects_cout,
            'ViolatingObjects': violating_objects_count,
            'EnvironmentScore': environment_score,
            'Detections': str(objects),
            'ViolationsIndexes': str(violating_objects_index_list)
        }
        try:
            requests.put(self.web_hook_endpoint, data=request_data)
        except ConnectionError:
            logger.error(f"Connection with endpoint {self.web_hook_endpoint} can't be established")
