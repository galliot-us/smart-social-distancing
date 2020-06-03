from invoke import task
from .common import docker, constants, ROOT_DIR


@task
def dockerhub(c):
    for product in constants.D_ALL:
        docker.auto_build(c, product, public_image=True)
        docker.auto_push(c, product, config='~/.neuralet-dev/docker', public_image=True)


@task
def dockerhub_login(c):
    docker.login(c)
