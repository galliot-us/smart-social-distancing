from invoke import task, exceptions
from .common import docker, constants, config, ROOT_DIR

valid_backend_names = constants.D_BACKENDS


@task(help={'name': '|'.join(constants.D_ALL)})
def build(c, name, local=False, frontend_build_skip=False):
    assert name in constants.D_ALL
    if not frontend_build_skip:
        docker.auto_build(c, 'frontend', local=local)
    docker.auto_build(c, name, local=local)


@task(help={'name': '|'.join(valid_backend_names)})
def run(c, name, local=False, port=None, rm=True, build_skip=False, frontend_build_skip=False, dev_mode=False,
        tunnel_skip=False, shell=False):
    assert name in valid_backend_names
    username = config.get_config(c, 'develop.username')

    if not frontend_build_skip:
        docker.auto_build(c, constants.D_FRONTEND, host=docker.get_host(c, name, local))

    if local:
        data_mount = f'{ROOT_DIR}/data'
    elif name == constants.D_CORAL_DEV_BORAD:
        data_mount = f'/home/mendel/{username}/data'
    elif name == constants.D_JETSON_NANO:
        data_mount = f'/home/teamtpu/{username}/data'
    else:
        data_mount = f'/home/{username}/data'

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

    if not build_skip:
        docker.auto_build(c, name, local=local)

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
        c.run('npm start')
