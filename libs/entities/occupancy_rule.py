from datetime import time, datetime


class OccupancyRule:

    def __init__(self, json_value: dict):
        self.days = json_value["days"]
        self.start_hour = occ_str_to_time(json_value["start_hour"])
        self.finish_hour = occ_str_to_time(json_value["finish_hour"])
        self.occupancy_threshold = json_value["max_occupancy"]

    def date_is_included(self, date: datetime):
        t = date.time()
        return self.days[date.weekday()] and date_before(self.start_hour, t) and date_before(t, self.finish_hour, strict=True) \
            and not (t.hour == 0 and t.minute == 0 and t < self.start_hour)
        # Exclude case where t == 00:00 and start isn't


def occ_str_to_time(value: str):
    splits = value.split(":")
    if len(splits) != 2:
        return None
    return time(int(splits[0]), int(splits[1]))


# Friendly Occupancy Rules Date Compare :-)
def date_before(start: time, end: time, strict=False):
    """ Returns True iff start < end or end == 00:00 (if strict=True).
        Otherwise returns start <= end or end == 00:00
        :-)
    """
    if strict:
        return start < end or (end.hour == 0 and end.minute == 0)
    return start <= end or (end.hour == 0 and end.minute == 0)
