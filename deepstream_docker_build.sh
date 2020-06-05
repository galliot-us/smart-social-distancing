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
readonly DS_PYBIND_TBZ2="ds_pybind_v0.9.tbz2"  # deepstrem python bindings
readonly DS_PYBIND_URL="https://developer.nvidia.com/deepstream-getting-started#python_bindings"
# Dockerfile names
readonly X86_DOCKERFILE="deepstream-x86.Dockerfile"
readonly TEGRA_DOCKERFILE="deepstream-tegra.Dockerfile"
# https://www.cyberciti.biz/faq/bash-get-basename-of-filename-or-directory-name/
readonly THIS_SCRIPT_BASENAME="${0##*/}"

# get the docker tag suffix from the git branch
# if master, use "latest"
TAG_SUFFIX=$(git rev-parse --abbrev-ref HEAD)
if [[ $TAG_SUFFIX == "master" ]]; then
    TAG_SUFFIX="deepstream"
fi

function check_deps() {
  if [ ! -f ${DS_PYBIND_TBZ2} ]; then
    echo "ERROR: ${DS_PYBIND_TBZ2} needed in same directory as Dockerfile." > /dev/stderr
    echo "Download from: ${DS_PYBIND_URL}" > /dev/stderr
    echo "(it's inside deepstream_python_v0.9.tbz2)" > /dev/stderr
    exit 1
  fi
}

function x86() {
  exec docker build -f $X86_DOCKERFILE -t "$USER_NAME/smart-distancing:$TAG_SUFFIX" .
}

function tegra() {
  exec docker build -f $TEGRA_DOCKERFILE -t "$USER_NAME/smart-distancing:$TAG_SUFFIX" .
}

main() {
  check_deps
case "$1" in
  x86)
      x86
      ;;
  tegra)
      tegra
      ;;
  *)
      echo "Usage: $THIS_SCRIPT_BASENAME {x86|tegra}"
esac
}

main "$1"