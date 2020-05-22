from invoke import task
from .common import docker, constants, config

valid_backend_names = constants.D_BACKENDS


@task(help={'name': '|'.join(valid_backend_names)})
def run(c, name, port=None, rm=True):
    assert name in valid_backend_names
    username = config.get_config(c, 'develop.username')

    if name == constants.D_CORAL_DEV_BORAD:
        data_mount = f'/home/mendel/{username}/data'
    elif name == constants.D_JETSON_NANO:
        data_mount = f'/home/teamtpu/{username}/data'
    else:
        data_mount = f'/home/{username}/data'

    if port is None:
        port = config.get_config(c, 'develop.host_ports.backend')

    docker.auto_build(c, 'frontend')
    docker.auto_build(c, name)
    docker.auto_run(c, name, p=[f'{port}:8000'], v=[f'{data_mount}:/repo/data'], rm=rm)
