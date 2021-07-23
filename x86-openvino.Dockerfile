FROM openvino/ubuntu18_runtime
USER root

# The `python3-opencv` package isn't built with gstreamer. So we need to manually build opencv.
ARG OPENCV_VERSION=4.5.3
# http://amritamaz.net/blog/opencv-config
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        curl \
        git \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-vaapi \
        libavcodec-dev \
        libavformat-dev \
        libgstreamer-plugins-base1.0-dev \
        libgstreamer1.0-dev \
        libsm6 \
        libswscale-dev \
        libxext6 \
        libxrender-dev \
        libpython3.6-dev \
        mesa-va-drivers \
        python3-dev \
        python3-numpy \
    && rm -rf /var/lib/apt/lists/* \
    && cd /tmp/ \
    && curl -L https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.tar.gz -o opencv.tar.gz \
    && tar zxvf opencv.tar.gz && rm opencv.tar.gz \
    && cd /tmp/opencv-${OPENCV_VERSION} \
    && mkdir build \
    && cd build \
    && cmake \
        -DBUILD_opencv_python3=yes \
        -DPYTHON_EXECUTABLE=$(which python3) \
        -DCMAKE_BUILD_TYPE=RELEASE \
        -DBUILD_TESTS=OFF \
        -DBUILD_PERF_TESTS=OFF \
        -DBUILD_EXAMPLES=OFF \
        -DINSTALL_TESTS=OFF \
        -DBUILD_opencv_apps=OFF \
        -DBUILD_DOCS=OFF \
        ../ \
    && make -j$(nproc) \
    && make install \
    && cd /tmp \
    && rm -rf opencv-${OPENCV_VERSION} \
    && apt-get purge -y \
        cmake \
        git \
        libgstreamer-plugins-base1.0-dev \
        libgstreamer1.0-dev \
        libxrender-dev \
        python3-dev \
    && apt-get autoremove -y

# https://askubuntu.com/questions/909277/avoiding-user-interaction-with-tzdata-when-installing-certbot-in-a-docker-contai
ARG DEBIAN_FRONTEND=noninteractive

COPY api/requirements.txt /

RUN apt-get update && apt-get install -y --no-install-recommends \
        tzdata \
        pkg-config \
        python3-dev \
        python3-numpy \
        python3-pillow \
        python3-pip \
        python3-scipy \
        python3-wget \
        supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --upgrade pip setuptools==41.0.0 wheel && pip install -r /requirements.txt \
    && apt-get purge -y \
        python3-dev \
    && apt-get autoremove -y

# Remove the opencv which is included in Openvino and is incompatible with globally-installed gstreamer
RUN rm -rf /opt/intel/openvino/opencv /opt/intel/openvino/python/cv2.* /opt/intel/openvino/python/python3/cv2.*

ADD docker/x86-openvino/openvino_setupvars.py /opt/openvino_setupvars.py
ENV DEV_ALLOW_ALL_ORIGINS=true
ENV CONFIG_FILE=config-x86-openvino.ini

COPY . /repo
WORKDIR /repo

HEALTHCHECK --interval=30s --retries=2 --start-period=15s CMD bash healthcheck.bash
CMD env `python3 /opt/openvino_setupvars.py` supervisord -c supervisord.conf -n
