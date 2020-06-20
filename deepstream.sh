#!/bin/bash
# Copyright (c) 2020 Michael de Gans
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

set -e

# change the default run port
readonly PORT="8000"
# change this to bump the version tag
readonly VERSION="0.1.0"
# change this to your docker hub user if you fork this and want to push it
readonly USER_NAME="neuralet"
# change this to override the arch (should never be necessary)
readonly ARCH="$(arch)"
# frontend dockerfile name
readonly FRONTEND_DOCKERFILE="frontend.Dockerfile"
# Dockerfile name
readonly DOCKERFILE="deepstream.Dockerfile"
# https://www.cyberciti.biz/faq/bash-get-basename-of-filename-or-directory-name/
readonly THIS_SCRIPT_BASENAME="${0##*/}"
# change this to use a newer gst-cuda-plugin version
readonly CUDA_PLUGIN_VER="0.3.3"
# https://stackoverflow.com/questions/4774054/reliable-way-for-a-bash-script-to-get-the-full-path-to-itself
readonly THIS_DIR="$( cd "$(dirname "$0")" > /dev/null 2>&1 ; pwd -P )"
# the primary group to use
if [[ $ARCH = "aarch64" ]]; then
  # on tegra, a user must be in the video group to use the gpu
  readonly GROUP_ID="$(cut -d: -f3 < <(getent group video))"
  declare readonly GPU_ARGS=(
    "--runtime"
    "nvidia"
  )
else
  readonly GROUP_ID=$(id -g)
  declare readonly GPU_ARGS=(
    "--gpus"
    "all"
  )
fi
# the user id to use
if [[ -z "$SUDO_USER" ]]; then
  readonly USER_ID=$UID
else
  echo "sudo user: $SUDO_USER"
  readonly USER_ID="$(id -u $SUDO_USER)"
fi

# this helps tag the image
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
# get the docker tag suffix from the git branch
if [[ $GIT_BRANCH == "master" ]]; then
  # if we're on master, just use "deepstream"
  readonly GIT_BRANCH="latest"
else
  readonly GIT_BRANCH=$GIT_BRANCH
fi

# change this to ovverride the image tag suffix
readonly TAG_SUFFIX1="deepstream-$VERSION-$ARCH"
readonly TAG_SUFFIX2="deepstream-$GIT_BRANCH-$ARCH"

function build() {
  readonly local FRONTEND_TAG="$GIT_BRANCH-frontend"
  set -x
  docker build -f $FRONTEND_DOCKERFILE \
    -t "$USER_NAME/smart-social-distancing:$FRONTEND_TAG" \
    .
  docker build -f $DOCKERFILE \
    -t "$USER_NAME/smart-distancing:$TAG_SUFFIX1" \
    -t "$USER_NAME/smart-distancing:$TAG_SUFFIX2" \
    --build-arg CUDA_PLUGIN_TAG="$CUDA_PLUGIN_VER-$ARCH" \
    --build-arg FRONTEND_BASE="$USER_NAME/smart-social-distancing:$FRONTEND_TAG" \
    .
}

function run() {
  set -x
  exec docker run -it --rm --name smart_distancing \
    "${GPU_ARGS[@]}" \
    -v "$THIS_DIR/deepstream.ini:/repo/deepstream.ini" \
    -v "$THIS_DIR/data:/repo/data" \
    --user $USER_ID:$GROUP_ID \
    -p "$PORT:8000" \
    "$USER_NAME/smart-distancing:$TAG_SUFFIX1" \
    --verbose
}

main() {
case "$1" in
  build)
      build
      ;;
  run)
      run
      ;;
  *)
      echo "Usage: $THIS_SCRIPT_BASENAME {build|run}"
esac
}

main "$1"