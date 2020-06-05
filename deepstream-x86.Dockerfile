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

FROM registry.hub.docker.com/mdegans/gstcudaplugin:latest

# this can't be downloaded directly because a license needs to be accepted,
# (because those who abuse it will care so much about that) and a tarball
# extracted. This is very un-fun:
# https://developer.nvidia.com/deepstream-getting-started#python_bindings
ARG DS_PYBIND_TBZ2='ds_pybind_v0.9.tbz2'
ARG DS_SOURCES_ROOT='/opt/nvidia/deepstream/deepstream/sources'

# copy stuff we need at the start of the build
COPY ${DS_PYBIND_TBZ2} requirements.txt /tmp/

# extract and install the python bindings
RUN mkdir -p ${DS_SOURCES_ROOT} \
    && tar -xf /tmp/${DS_PYBIND_TBZ2} -C ${DS_SOURCES_ROOT}

# install pip, install requirements, remove pip and deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-gi \
        python3-gst-1.0 \
        python3-pip \
        python3-setuptools \
        python3-opencv \
        python3-dev \
        graphviz \
    && pip3 install --require-hashes -r /tmp/requirements.txt \
    && apt-get purge -y --autoremove \
        python3-pip \
        python3-setuptools \
        python3-dev \
    && rm -rf /var/lib/apt/cache/*

# TODO(mdegans) python3-opencv brings in a *ton* of dependencies so 
# it's probably better off removed from the deepstream image

# NOTE(mdegans): these layers are here because docker's multi-line
# copy syntax is dumb and doesn't support copying folders in a sane way.
# one way of getting around this is to use a subdir for your
# project

WORKDIR /repo

COPY --from=neuralet/smart-social-distancing:latest-frontend /frontend/build /srv/frontend
COPY neuralet-distancing.py README.md ${CONFIG_FILE} ./
COPY libs ./libs/
COPY ui ./ui/
COPY tools ./tools/
COPY logs ./logs/
COPY data ./data/

# drop all caps to a regular user
RUN useradd -md /var/smart_distancing -rUs /bin/false smart_distancing \
    && chown -R smart_distancing:smart_distancing /repo/data/web_gui/static/gstreamer
USER smart_distancing:smart_distancing

# copy frontend
COPY --from=neuralet/smart-social-distancing:latest-frontend /frontend/build /srv/frontend

# entrypoint with deepstream.
EXPOSE 8000
ENTRYPOINT [ "/usr/bin/python3", "neuralet-distancing.py" ]
CMD [ "--config", "deepstream.ini" ]
