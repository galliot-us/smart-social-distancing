import argparse
import logging
import schedule
import time

from libs.config_engine import ConfigEngine
from libs.reports_tasks import create_daily_report, send_daily_report_notification

logger = logging.getLogger(__name__)


def schedule_reports_tasks(config):
    schedule.every().day.at("00:01").do(create_daily_report, config=config)
    sources = config.get_video_sources()
    areas = config.get_areas()
    for src in sources:
        if src['daily_report']:
            schedule.every().day.at(src['daily_report_time']).do(
                send_daily_report_notification, config=config, entity_info=src)
    for area in areas:
        if area['daily_report']:
            schedule.every().day.at(area['daily_report_time']).do(
                send_daily_report_notification, config=config, entity_info=area)


def main(config):
    logging.basicConfig(level=logging.INFO)
    if isinstance(config, str):
        config = ConfigEngine(config)

    periodic_tasks_names = [x for x in config.get_sections() if x.startswith("PeriodicTask_")]
    for p_task in periodic_tasks_names:
        task_name = config.get_section_dict(p_task).get("Name")
        if task_name == "reports":
            logger.info("Reporting enabled!")
            schedule_reports_tasks(config)
        else:
            raise ValueError(f"Not supported periodic task named: {task_name}")

    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    main(args.config)
