from invoke import task
from .common import docker, constants, config, ROOT_DIR

valid_backend_names = constants.D_BACKENDS


@task(help={'name': '|'.join(constants.D_ALL)})
def build(c, name, local=False, build_frontend=True):
    assert name in constants.D_ALL
    docker.auto_build(c, 'frontend', local=local)
    docker.auto_build(c, name, local=local)


@task(help={'name': '|'.join(valid_backend_names)})
def run(c, name, local=False, port=None, rm=True, build_frontend=True):
    assert name in valid_backend_names
    username = config.get_config(c, 'develop.username')

    if build_frontend:
        docker.auto_build(c, constants.D_FRONTEND, host=docker.get_host(c, name, local))
        globals()['build'].body(c, name, local=local)

    if local:
        data_mount = f'{ROOT_DIR}/data'
    elif name == constants.D_CORAL_DEV_BORAD:
        data_mount = f'/home/mendel/{username}/data'
    elif name == constants.D_JETSON_NANO:
        data_mount = f'/home/teamtpu/{username}/data'
    else:
        data_mount = f'/home/{username}/data'

    if port is None:
        port = config.get_config(c, 'develop.host_ports.backend')

    docker.auto_build(c, name, local=local)
    docker.auto_run(c, name, p=[f'{port}:8000'], v=[f'{data_mount}:/repo/data', f'{data_mount}/root:/root'], rm=rm,
                    local=local)

@task
def tmp(c):
    from pprint import pprint
    pprint(dir(c))
