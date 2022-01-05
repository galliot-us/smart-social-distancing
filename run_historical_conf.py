from configparser import RawConfigParser
import argparse
import io
import os


def new_camera(camera, camera_index, config_file):
    add_config = f"""
        [Source_{camera_index}]
        VideoPath = /repo/data/historical_data/videos/{camera}
        Tags = tags_{camera}
        Name = name_{camera}
        Id = {camera_index}
        Emails =
        EnableSlackNotifications = False
        NotifyEveryMinutes = 0
        ViolationThreshold = 60
        DistMethod =
        DailyReport = False
        DailyReportTime = 06:00
        LiveFeedEnabled = True
    """
    new_config = RawConfigParser(allow_no_value=True)
    new_config.readfp(io.StringIO(add_config))

    with open(config_file, 'a') as add_configfile:
        new_config.write(add_configfile)

def delete_camera(config_file):
    config.read(config_file)
    for section in config.sections():
        if 'Source_' in section:
            config.remove_section(section)

    with open(config_file, 'w') as del_configfile:
        config.write(del_configfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Processor's automatic setting.")
    parser.add_argument('--ini_file', type=str, default=os.environ['DEFAULT_INI_CONFIG'])
    parser.add_argument('--data_hist', type=str, default=os.environ['DEFAULT_HIST_VIDEOS_FOLDER'])
    args = parser.parse_args()
    config = RawConfigParser(allow_no_value=True)
    ini_file = args.ini_file
    config.read(ini_file)
    list_cameras = os.listdir(args.data_hist)
    delete_camera(ini_file)
    for i, camera in enumerate(list_cameras):
        new_camera(camera, i, ini_file)
