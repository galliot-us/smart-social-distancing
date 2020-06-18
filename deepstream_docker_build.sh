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

# change this to your docker hub user if you fork this and want to push it
readonly USER_NAME="neuralet"
# DeepStream constants:
readonly DS_PYBIND_URL="https://developer.nvidia.com/deepstream-getting-started#python_bindings"
# Dockerfile names
readonly DOCKERFILE="deepstream.Dockerfile"
# https://www.cyberciti.biz/faq/bash-get-basename-of-filename-or-directory-name/
readonly THIS_SCRIPT_BASENAME="${0##*/}"
# change this to use a newer gst-cuda-plugin version
readonly CUDA_PLUGIN_VER="0.3.1"

# get the docker tag suffix from the git branch
TAG_SUFFIX="deepstream-$(git rev-parse --abbrev-ref HEAD)"
if [[ $TAG_SUFFIX == "deepstream-master" ]]; then
  # if we're on master, just use "deepstream"
  TAG_SUFFIX="deepstream"
fi

function build() {
  exec docker build --pull -f $DOCKERFILE \
    -t "$USER_NAME/smart-distancing:$TAG_SUFFIX-$1" \
    --build-arg CUDA_PLUGIN_TAG="${CUDA_PLUGIN_VER}-$1" \
    .
}

function run() {
  exec docker build --pull -f $DOCKERFILE \
    -t "$USER_NAME/smart-distancing:$TAG_SUFFIX-$1" \
    --build-arg CUDA_PLUGIN_TAG="${CUDA_PLUGIN_VER}-$1" \
    .
}

main() {
  local ARCH="$(arch)"
case "$1" in
  build)
      build $ARCH
      ;;
  run)
      run $ARCH
      ;;
  *)
      echo "Usage: $ARCH"
esac
}

main "$1"