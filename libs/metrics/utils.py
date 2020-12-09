from .face_mask_usage import FaceMaskUsageMetric
from .occupancy import OccupancyMetric
from .social_distancing import SocialDistancingMetric


def compute_hourly_metrics(config):
    SocialDistancingMetric.compute_hourly_metrics(config)
    FaceMaskUsageMetric.compute_hourly_metrics(config)
    OccupancyMetric.compute_hourly_metrics(config)


def compute_daily_metrics(config):
    SocialDistancingMetric.compute_daily_metrics(config)
    FaceMaskUsageMetric.compute_daily_metrics(config)
    OccupancyMetric.compute_daily_metrics(config)
