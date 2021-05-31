import numpy as np
import os
import pandas as pd

from .face_mask_usage import FaceMaskUsageMetric
from .occupancy import OccupancyMetric
from .social_distancing import SocialDistancingMetric
from .in_out import InOutMetric
from .dwell_time import DwellTimeMetric


def compute_hourly_metrics(config):
    SocialDistancingMetric.compute_hourly_metrics(config)
    FaceMaskUsageMetric.compute_hourly_metrics(config)
    OccupancyMetric.compute_hourly_metrics(config)
    InOutMetric.compute_hourly_metrics(config)
    DwellTimeMetric.compute_hourly_metrics(config)


def compute_daily_metrics(config):
    SocialDistancingMetric.compute_daily_metrics(config)
    FaceMaskUsageMetric.compute_daily_metrics(config)
    OccupancyMetric.compute_daily_metrics(config)
    InOutMetric.compute_daily_metrics(config)
    DwellTimeMetric.compute_daily_metrics(config)


def compute_live_metrics(config, live_interval):
    SocialDistancingMetric.compute_live_metrics(config, live_interval)
    FaceMaskUsageMetric.compute_live_metrics(config, live_interval)
    OccupancyMetric.compute_live_metrics(config, live_interval)
    InOutMetric.compute_live_metrics(config, live_interval)
    DwellTimeMetric.compute_live_metrics(config, live_interval)


def generate_heatmap(camera_id, from_date, to_date, report_type):
    """Returns the sum of the heatmaps for a specified range of dates
    Args:
        camera_id (str): id of an existing camera
        from_date (date): start of the date range
        to_date (date): end of the date range
        report_type (str): { 'violations', 'detections' }

    Returns:
        result (dict): {
            'heatmap': [(150,150) grid],
            'not_found_dates': [array[str]]
        }
    """
    log_dir = os.getenv('SourceLogDirectory')
    heatmap_resolution = os.getenv('HeatmapResolution').split(",")
    heatmap_x = int(heatmap_resolution[0])
    heatmap_y = int(heatmap_resolution[1])
    file_path = os.path.join(log_dir, camera_id, "heatmaps", f"{report_type}_heatmap_")

    date_range = pd.date_range(start=from_date, end=to_date)
    heatmap_total = np.zeros((heatmap_x, heatmap_y))
    not_found_dates = []

    for report_date in date_range:
        try:
            heatmap = np.load(f"{file_path}{report_date.strftime('%Y-%m-%d')}.npy")
            heatmap_total = np.add(heatmap_total, heatmap)
        except IOError:
            not_found_dates.append(report_date.strftime('%Y-%m-%d'))

    return {"heatmap": heatmap_total.tolist(),
            "not_found_dates": not_found_dates}
