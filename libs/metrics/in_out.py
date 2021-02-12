import os
import json
import numpy as np
from datetime import date
from typing import Dict, Iterator, List

from .base import BaseMetric
from constants import IN_OUT
from libs.utils.loggers import get_source_log_directory
from pathlib import Path

class InOutMetric(BaseMetric):

    reports_folder = IN_OUT
    csv_headers = []
    entity = "area"
    live_csv_headers = []

    @classmethod
    def process_csv_row(cls, csv_row: Dict, objects_logs: Dict):
        raise NotImplementedError("Operation not implemented")

    @classmethod
    def generate_hourly_metric_data(cls, objects_logs, entity):
        raise NotImplementedError("Operation not implemented")

    @classmethod
    def generate_daily_csv_data(cls, yesterday_hourly_file):
        raise NotImplementedError("Operation not implemented")

    @classmethod
    def generate_live_csv_data(cls, today_entity_csv, entity, entries_in_interval):
        """
        Generates the live report using the `today_entity_csv` file received.
        """
        raise NotImplementedError("Operation not implemented")

    @classmethod
    def get_trend_live_values(cls, live_report_paths: Iterator[str]) -> Iterator[int]:
        raise NotImplementedError("Operation not implemented")

    @classmethod
    def get_weekly_report(cls, entities: List[str], number_of_weeks: int = 0,
                          from_date: date = None, to_date: date = None) -> Dict:
        raise NotImplementedError("Operation not implemented")

    @classmethod
    def get_in_out_file_path(cls, camera_id, config):
        """ Returns the path to the roi_contour file """
        return f"{get_source_log_directory(config)}/{camera_id}/{IN_OUT}/{IN_OUT}.json"

    @classmethod
    def get_in_out_boundaries(cls, in_out_file_path):
        """ Given the path to the in-out file it loads it and returns it """
        if os.path.exists(in_out_file_path)\
           and Path(in_out_file_path).is_file()\
           and Path(in_out_file_path).stat().st_size != 0:
            with open(in_out_file_path) as json_file:
                in_out_boundaries = json.load(json_file)
            return in_out_boundaries
        else:
            return None
