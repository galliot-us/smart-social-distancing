import os

from datetime import date

from libs.config_engine import ConfigEngine
from libs.utils.loggers import get_area_log_directory, get_source_log_directory
from libs.uploaders.s3_uploader import S3Uploader


def raw_data_backup(config: ConfigEngine, bucket_name: str):
    s3_uploader = S3Uploader()
    sources = config.get_video_sources()
    source_log_directory = get_source_log_directory(config)
    area_log_directory = get_area_log_directory(config)
    areas = config.get_areas()
    # Backup all the source files
    for src in sources:
        source_directory = os.path.join(source_log_directory, src["id"])
        objects_log_directory = os.path.join(source_directory, "objects_log")
        today_objects_csv = os.path.join(objects_log_directory, str(date.today()) + ".csv")
        bucket_prefix = f"sources/{src['id']}/object_logs"
        if os.path.isfile(today_objects_csv):
            # Upload the today object files to S3
            s3_uploader.upload_file(bucket_name, today_objects_csv, f"{str(date.today())}.csv", bucket_prefix)
    # Backup all the area files
    for area in areas:
        area_directory = os.path.join(area_log_directory, area["id"])
        occupancy_log_directory = os.path.join(area_directory, "occupancy_log")
        today_occupancy_csv = os.path.join(occupancy_log_directory, str(date.today()) + ".csv")
        bucket_prefix = f"areas/{src['id']}/occupancy_log"
        if os.path.isfile(today_objects_csv):
            # Upload the today object files to S3
            s3_uploader.upload_file(bucket_name, today_occupancy_csv, f"{str(date.today())}.csv", bucket_prefix)
