import argparse
import logging
import schedule
import time

from libs.backups.s3_backup import raw_data_backup
from libs.config_engine import ConfigEngine
from libs.reports.notifications import (send_daily_report_notification, send_daily_global_report,
                                        send_weekly_global_report)

logger = logging.getLogger(__name__)


def main(config):
    logging.basicConfig(level=logging.INFO)
    if isinstance(config, str):
        config = ConfigEngine(config)

    # Schedule configured periodic tasks
    periodic_tasks_names = [x for x in config.get_sections() if x.startswith("PeriodicTask_")]
    for p_task in periodic_tasks_names:
        if not config.get_boolean(p_task, "Enabled"):
            continue
        task_name = config.get_section_dict(p_task).get("Name")
        if task_name == "s3_backup":
            bucket_name = config.get_section_dict(p_task).get("BackupS3Bucket")
            if not bucket_name:
                logger.info("S3 Backup task doesn't have a bucket configured.")
                continue
            logger.info("Backup enabled!")
            backup_interval = int(config.get_section_dict(p_task).get("BackupInterval", 30))
            schedule.every(backup_interval).minutes.do(raw_data_backup, config=config, bucket_name=bucket_name)
        else:
            raise ValueError(f"Not supported periodic task named: {task_name}")

    # Schedule daily/weekly reports for sources
    sources = config.get_video_sources()
    for src in sources:
        if src['daily_report']:
            schedule.every().day.at(src['daily_report_time']).do(
                send_daily_report_notification, config=config, entity_info=src)
    if config.get_boolean("App", "DailyGlobalReport"):
        schedule.every().day.at(config.get_section_dict("App")["GlobalReportTime"]).do(
            send_daily_global_report, config=config, sources=sources
        )
    if config.get_boolean("App", "WeeklyGlobalReport"):
        schedule.every(7).days.at(config.get_section_dict("App")["GlobalReportTime"]).do(
            send_weekly_global_report, config=config, sources=sources
        )

    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    main(args.config)
