# docker can be installed on the dev board following these instructions:
# https://docs.docker.com/install/linux/docker-ce/debian/#install-using-the-repository , step 4: arm64
# 1) build: docker build -f jetson-nano.Dockerfile -t "neuralet/smart-social-distancing:latest-jetson-nano" .
# 2) run: docker run -it --runtime nvidia --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data neuralet/smart-social-distancing:latest-jetson-nano

FROM nvcr.io/nvidia/l4t-tensorflow:r32.5.0-tf1.15-py3


# The `python3-opencv` package is old and doesn't support gstreamer video writer on Debian. So we need to manually build opencv.
ARG OPENCV_VERSION=4.3.0
# http://amritamaz.net/blog/opencv-config
# RUN apt-get update && apt-get install -y --no-install-recommends \
#         build-essential \
#         ca-certificates \
#         cmake \
#         curl \
#         git \
#         gnupg \
#         gstreamer1.0-plugins-bad \
#         gstreamer1.0-plugins-good \
#         gstreamer1.0-plugins-ugly \
#         gstreamer1.0-vaapi \
#         libavcodec-dev \
#         libavformat-dev \
#         libgstreamer-plugins-base1.0-dev \
#         libgstreamer1.0-dev \
#         libsm6 \
#         libswscale4 \
#         libswscale-dev \
#         libxext6 \
#         libxrender-dev \
#         mesa-va-drivers \
#         nano \
#         pkg-config \
#         python3-pip \
#         vim \
#         zip \
#     && rm -rf /var/lib/apt/lists/* \
#     && cd /tmp/ \
#     && curl -L https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.tar.gz -o opencv.tar.gz \
#     && tar zxvf opencv.tar.gz && rm opencv.tar.gz \
#     && cd /tmp/opencv-${OPENCV_VERSION} \
#     && mkdir build \
#     && cd build \
#     && cmake \
#         -DBUILD_opencv_python3=yes \
#         -DPYTHON_EXECUTABLE=$(which python3) \
#         -DCMAKE_BUILD_TYPE=RELEASE \
#         -DBUILD_TESTS=OFF \
#         -DBUILD_PERF_TESTS=OFF \
#         -DBUILD_EXAMPLES=OFF \
#         -DINSTALL_TESTS=OFF \
#         -DBUILD_opencv_apps=OFF \
#         -DBUILD_DOCS=OFF \
#         ../ \
#     && make -j$(nproc) \
#     && make install \
#     && cd /tmp \
#     && rm -rf opencv-${OPENCV_VERSION} \
#     && apt-get purge -y \
#         cmake \
#         git \
#         libgstreamer-plugins-base1.0-dev \
#         libgstreamer1.0-dev \
#         libxrender-dev \
#     && apt-get autoremove -y

RUN apt-get update && apt-get install -y python3-pip pkg-config zip gnupg

RUN python3 -m pip install pip==20.1

RUN printf 'deb https://repo.download.nvidia.com/jetson/common r32 main\ndeb https://repo.download.nvidia.com/jetson/t210 r32 main' > /etc/apt/sources.list.d/nvidia-l4t-apt-source.list

COPY ./bin/trusted-keys /tmp/trusted-keys
RUN apt-key add /tmp/trusted-keys

# https://askubuntu.com/questions/909277/avoiding-user-interaction-with-tzdata-when-installing-certbot-in-a-docker-contai
ARG DEBIAN_FRONTEND=noninteractive

COPY api/requirements.txt /

# Installing pycuda using already-built wheel is a lot faster
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        graphsurgeon-tf \
        libboost-python-dev \
        libboost-thread-dev \
        libnvinfer6 \
        libnvinfer-dev \
        libhdf5-100 \
        libhdf5-dev \
        python3-libnvinfer \
        python3-libnvinfer-dev \
        pkg-config \
        python3-dev \
        python3-h5py \
        python3-matplotlib \
        python3-numpy \
        python3-pillow \
        python3-pip \
        python3-scipy \
        python3-wget \
        supervisor \
        tensorrt \
        tzdata \
        uff-converter-tf \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf $(which gcc) /usr/local/bin/gcc-aarch64-linux-gnu \
    && ln -sf $(which g++) /usr/local/bin/g++-aarch64-linux-gnu \
    && python3 -m pip install --upgrade pip setuptools==41.0.0 opencv-python wheel protobuf wget pillow pycuda && pip install -r requirements.txt \
    && apt-get purge -y \
    && apt-get autoremove -y
#

RUN wget https://github.com/neuralet/smart-social-distancing/blob/UpdateJetpack4.5/bin/libflattenconcat.so -O /opt/libflattenconcat.so
RUN apt update && apt install -y libtcmalloc-minimal4

ENV LD_PRELOAD="/usr/lib/aarch64-linux-gnu/libtcmalloc_minimal.so.4"
RUN apt update && apt install -y cmake protobuf-compiler libprotobuf-dev
RUN pip install onnx
# ENV relative_path=/repo/adaptive_object_detection 
# ENV PYTHONPATH=/repo:/repo/adaptive_object_detection

RUN apt upgrade

ENV DEV_ALLOW_ALL_ORIGINS=true
ENV CONFIG_FILE=config-jetson-nano.ini
# ENV OPENBLAS_CORETYPE=armv8

COPY . /repo/
WORKDIR /repo
HEALTHCHECK --interval=30s --retries=2 --start-period=15s CMD bash healthcheck.bash
CMD supervisord -c supervisord.conf -n
