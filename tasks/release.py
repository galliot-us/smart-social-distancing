from invoke import task
from .common import docker, constants

@task
def dockerhub(c):
    for product in constants.D_ALL:
        docker.auto_build(c, product)
        docker.auto_push(c, product)

@task
def dockerhub_login(c):
    docker.login(c)
