from invoke import task, exceptions
from .common import docker, constants, config, ROOT_DIR

valid_backend_names = constants.D_BACKENDS


def _build(c, name, local=False, frontend_build_skip=False):
    if not frontend_build_skip and name != constants.D_FRONTEND:
        docker.auto_build(c, constants.D_FRONTEND, local=local)
        if docker.get_host(c, name, local) != docker.get_host(c, constants.D_FRONTEND, local):
            # Transfer the frontend image from where it has been built to the host of `name` docker image.
            # Push from the source host and pull from the target host.
            docker.auto_push(c, constants.D_FRONTEND, local=local)
            docker.auto_pull(c, constants.D_FRONTEND, host=docker.get_host(c, name, local))

    docker.auto_build(c, name, local=local)


@task(help={'name': '|'.join(constants.D_ALL)})
def build(c, name, local=False, frontend_build_skip=False):
    assert name in constants.D_ALL
    _build(c, name, local=local, frontend_build_skip=frontend_build_skip)


@task(help={'name': '|'.join(valid_backend_names)})
def run(c, name, local=False, port=None, rm=True, build_skip=False, frontend_build_skip=False, dev_mode=False,
        tunnel_skip=False, shell=False):
    """
    This command builds the frontend on gpu server (in case of --local, on local machine),
    """
    assert name in valid_backend_names

    if not build_skip:
        _build(c, name, local=local, frontend_build_skip=frontend_build_skip)

    host_username = config.get_config(c, 'develop.host_username')

    if local:
        data_mount = f'{ROOT_DIR}/data'
    elif name == constants.D_CORAL_DEV_BORAD:
        data_mount = f'/home/mendel/{host_username}/data'
    elif name == constants.D_JETSON_NANO:
        data_mount = f'/home/teamtpu/{host_username}/data'
    else:
        data_mount = f'/home/{host_username}/data'

    volumes = []

    if dev_mode:
        volumes.append(f'{data_mount}/root:/root')

    mount_repo = local and dev_mode

    if mount_repo:
        volumes.append(f'{ROOT_DIR}:/repo')
    else:
        # only mount data dir
        volumes.append(f'{data_mount}:/repo/data')

    if port is None:
        port = config.get_config(c, 'develop.host_ports.backend')

    env = ['DEV_ALLOW_ALL_ORIGINS=true' if dev_mode else None]

    tunnel_host = docker.get_host(c, name, local)
    tunnel = not tunnel_skip and not local and tunnel_host
    if tunnel:
        tunnel_handle = c.run(f'ssh -N -L {port}:127.0.0.1:{port} {tunnel_host}', asynchronous=True)

    if shell:
        it = True
        entrypoint = "bash"
    else:
        it = entrypoint = None

    try:
        docker.auto_run(c, name, p=[f'{port}:8000'], v=volumes, rm=rm, local=local, e=env, it=it, entrypoint=entrypoint)
    finally:
        if tunnel and not c.config.run.get('dry', False):
            try:
                tunnel_handle.runner.kill()
                tunnel_handle.join()
            except exceptions.UnexpectedExit:
                pass


@task
def frontend(c):
    with c.cd(f'{ROOT_DIR}/frontend'):
        c.run('yarn start')
