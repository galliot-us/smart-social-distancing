class LoggerTemplate:

    def __init__(self, config, camera_id):
        raise NotImplementedError

    def log_objects(self, objects, violating_objects, violating_objects_index_list, violating_objects_count,
                    detected_objects_cout, environment_score, time_stamp, version):
        raise NotImplementedError
