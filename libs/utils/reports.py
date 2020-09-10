import os
import numpy as np
import pandas as pd
import logging
import glob
from datetime import datetime, timedelta, date


def parse_date_range(dates):
    """Generator. From a continuous sorted list of datetime64 yields tuples (start_date, end_date) for each week encompassed"""
    while not dates.empty:
        start = 0
        end = (7 - dates[start].weekday()) - 1
        if end > len(dates):
            end = len(dates) - 1

        yield (dates[start], dates[end])
        dates = dates[end+1:]


class ReportsService:

    def __init__(self):
        self.logger = logging.getLogger(__name__)


    def hourly_report(self, camera_id, from_date, to_date):
        """Returns a report of hourly detection and violations for a specific camera taking the mean for each hour in a range of dates
            Args:
                camera_id (str): id of an existing camera
                from_date (date): start of the date range
                to_date (date): end of the date range

            Returns:
                result (dict): {
                    'hours': [str],
                    'detected_objects': [float],
                    'violating_objects': [float]
                }
                Ex: {'dates': [00, 01, ...], 'detected_objects': [7273.0, 0.5, ...], 'violating_objects': [4920.3, 0.4, ...]}
        """
        log_dir = os.getenv('LogDirectory')
        dir_path = os.path.join(log_dir, camera_id, "objects_log")
        date_range = pd.date_range(start=from_date, end=to_date)
        hours = list(range(0, 24))
        detected_objects = np.zeros(24)
        violating_objects = np.zeros(24)
        iters = 0
        for date in date_range:
            file_path = os.path.join(dir_path, f"report_{date.strftime('%Y-%m-%d')}.csv")
            if os.path.exists(file_path):
                iters += 1
                df = pd.read_csv(file_path).drop(['Number'], axis=1)
                detected_objects = detected_objects + df['DetectedObjects'].to_numpy()
                violating_objects = violating_objects + df['ViolatingObjects'].to_numpy()

        if iters != 0:
            detected_objects = detected_objects/iters
            violating_objects = violating_objects/iters

        report = {
            'hours': hours,
            'detected_objects': np.around(detected_objects, 1).tolist(),
            'violating_objects': np.around(violating_objects, 1).tolist(),
        }
        return report

    def daily_report(self, camera_id, from_date, to_date):
        """Returns a report of daily detection and violations for a specific camera in a range of dates
            Args:
                camera_id (str): id of an existing camera
                from_date (date): start of the date range
                to_date (date): end of the date range

            Returns:
                result (dict): {
                    'dates': [str], # str="NameOfDay iso8601_date"
                    'detected_objects': [int],
                    'violating_objects': [int]
                }
                Ex: {'dates': [Tuesday 2020-08-18, ...], 'detected_objects': [7273, ...], 'violating_objects': [4920, ...]}
        """
        date_range = pd.date_range(start=from_date, end=to_date)
        base_results = {key.strftime('%Y-%m-%d'): {'DetectedObjects': 0, 'ViolatingObjects': 0} for key in date_range}

        log_dir = os.getenv('LogDirectory')
        file_path = os.path.join(log_dir, camera_id, "objects_log", "report.csv")
        df = pd.read_csv(file_path).drop(['Number'], axis=1)
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

        mask = (df['Date'] >= pd.to_datetime(from_date)) & (df['Date'] <= pd.to_datetime(to_date))
        filtered_reports = df.loc[mask]
        filtered_reports['Date'] = filtered_reports['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        filtered_reports = filtered_reports.set_index('Date').T

        # Dictionary union. Favour the actual results over the initialized ones
        merged_report = dict(base_results, **filtered_reports.to_dict())
        merged_report = {datetime.strptime(key, '%Y-%m-%d'): merged_report[key] for key in merged_report}

        dates = []
        detected_objects = []
        violating_objects = []
        for date in sorted(merged_report):
            dates.append(date.strftime('%A %Y-%m-%d'))
            detected_objects.append(merged_report[date]['DetectedObjects'])
            violating_objects.append(merged_report[date]['ViolatingObjects'])

        report = {
            'dates': dates,
            'detected_objects': detected_objects,
            'violating_objects': violating_objects,
        }
        return report

    def weekly_report(self, camera_id, number_of_weeks=0, from_date=None, to_date=None):
        """Returns a report of weekly detection and violations for a specific camera in a range of dates
            Args:
                camera_id (str): id of an existing camera
                number_of_weeks (int): Takes priority over date range. Number of weeks to bring reports back from
                from_date (date): Only considered if number_of_weeks is non-positive. Start of the date range
                to_date (date): Only considered if number_of_weeks is non-positive. End of the date range

            Returns:
                result (dict): {
                    'weeks': [str], # str="iso8601_date iso8601_date"
                    'detected_objects': [int],
                    'violating_objects': [int]
                }
                Ex: {'dates': ["2020-07-03 2020-07-05", ...], 'detected_objects': [7273, ...], 'violating_objects': [4920, ...]}
        """
        number_of_days = number_of_weeks*7
        weeks = []
        detected_objects = []
        violating_objects = []

        if number_of_days > 0:
            # Separate weeks in range taking a number of weeks ago, considering the week ended yesterday
            date_range = pd.date_range(end=date.today() - timedelta(days=1), periods=number_of_days)
            start_dates = date_range[0::7]
            end_dates = date_range[6::7]
            week_span = list(zip(start_dates, end_dates))
        elif isinstance(from_date, date) and isinstance(to_date, date):
            # Separate weeks in range considering the week starts on Monday
            date_range = pd.date_range(start=from_date, end=to_date)
            week_span = list(parse_date_range(date_range))
        else:
            week_span = []

        for (start_date, end_date) in week_span:
            week_data = self.daily_report(camera_id, start_date, end_date)
            weeks.append(f"{start_date.strftime('%Y-%m-%d')} {end_date.strftime('%Y-%m-%d')}")
            detected_objects.append(sum(week_data['detected_objects']))
            violating_objects.append(sum(week_data['violating_objects']))

        report = {
            'weeks': weeks,
            'detected_objects': detected_objects,
            'violating_objects': violating_objects,
        }
        return report

    def heatmap(self, camera_id, from_date, to_date):
        """Returns the sum of the heatmaps for a specified range of dates
        Args:
            camera_id (str): id of an existing camera
            from_date (date): start of the date range
            to_date (date): end of the date range

        Returns:
            result (dict): {
                'heatmap': [(150,150) grid],
                'not_found_dates': [array[str]]
            }
        """
        log_dir = os.getenv('LogDirectory')
        heatmap_resolution = os.getenv('HeatmapResolution').split(",")
        heatmap_x = int(heatmap_resolution[0])
        heatmap_y = int(heatmap_resolution[1])
        file_path = os.path.join(log_dir, camera_id, "objects_log", "heatmap_")

        date_range = pd.date_range(start=from_date, end=to_date)
        heatmap_total = np.zeros((heatmap_x, heatmap_y))
        not_found_dates = []

        for date in date_range:
            try:
                heatmap = np.load(f"{file_path}{date.strftime('%Y-%m-%d')}.npy")
                heatmap_total = np.add(heatmap_total, heatmap)
            except IOError:
                not_found_dates.append(date.strftime('%Y-%m-%d'))

        return {"heatmap": heatmap_total.tolist(),
                "not_found_dates": not_found_dates}

    def peak_hour_violations(self, camera_id):
        log_dir = os.getenv('LogDirectory')
        dir_path = os.path.join(log_dir, camera_id, "objects_log")
        files = glob.glob(f"{dir_path}/report_*.csv")
        violating_objects = np.zeros(24)
        for file_path in files:
            df = pd.read_csv(file_path).drop(['Number'], axis=1)
            violating_objects = violating_objects + df['ViolatingObjects'].to_numpy()
        violating_objects = violating_objects / len(files)

        return int(np.argmax(violating_objects))

    def average_violations(self, camera_id):
        log_dir = os.getenv('LogDirectory')
        file_path = os.path.join(log_dir, camera_id, "objects_log", "report.csv")
        df = pd.read_csv(file_path).drop(['Number'], axis=1)
        return round(df['ViolatingObjects'].mean(), 1)

    def camera_with_most_violations(self):
        log_dir = os.getenv('LogDirectory')
        cameras = os.listdir(log_dir)
        cameras_violations = {}
        for camera_id in cameras:
            file_path = os.path.join(log_dir, camera_id, "objects_log", "report.csv")
            if os.path.exists(file_path):
                df = pd.read_csv(file_path).drop(['Number'], axis=1)
                cameras_violations[camera_id] = df['ViolatingObjects'].mean()

        return max(cameras_violations, key=cameras_violations.get)
