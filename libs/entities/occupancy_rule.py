from datetime import time, datetime

class OccupancyRule:

    def __init__(self, json_value: dict):
        self.days = json_value["days"]
        start_time = json_value["start_hour"].split(":")
        self.start_hour = time(int(start_time[0]), int(start_time[1]))
        finish_time = json_value["finish_hour"].split(":")
        self.finish_hour = time(int(finish_time[0]), int(finish_time[1]))
        self.occupancy_threshold = json_value["max_occupancy"]

    def date_is_included(self, date: datetime):
        return self.days[date.weekday()] and self.start_hour <= date.time() and self.finish_hour > date.time()