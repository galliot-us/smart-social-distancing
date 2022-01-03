from configparser import ConfigParser, RawConfigParser
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
    add_configfile.close()  

def edit_camera(camera, camera_index, config_file):
    config.set(f'Source_{camera_index}', 'VideoPath', f'/repo/data/historical_data/videos/{camera}')
    config.set(f'Source_{camera_index}', 'Tags', f'tags_{camera}')
    config.set(f'Source_{camera_index}', 'Name', f'name_{camera}')

    with open(config_file, 'w') as configfile:
        config.write(configfile)
    configfile.close()


if __name__ == '__main__':
    config = RawConfigParser(allow_no_value=True)
    ini_file = 'config-x86.ini'
    config.read(ini_file)
    list_cameras = os.listdir('data/historical_data/')
    if len(list_cameras) > 1:
        for i, camera in enumerate(list_cameras):
            if i == 0:
                edit_camera(camera, i, ini_file)
            elif i > 0:
                new_camera(camera, i, ini_file)
    elif len(list_cameras) == 1:
        if 'Source_0' in config.sections():
            edit_camera(list_cameras[0], 0, ini_file)
        else:
            new_camera(list_cameras[0], 0, ini_file)
    
    