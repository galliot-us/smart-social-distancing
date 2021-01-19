# docker can be installed on the dev board following these instructions:
# https://docs.docker.com/install/linux/docker-ce/debian/#install-using-the-repository , step 4: x86_64 / amd64
# 1) build: docker build -f amd64-usbtpu.Dockerfile -t "neuralet/smart-social-distancing:latest-amd64" .
# 2) run: docker run -it --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data neuralet/smart-social-distancing:latest-amd64

FROM amd64/debian:buster

RUN apt-get update && apt-get install -y wget gnupg usbutils \
    && rm -rf /var/lib/apt/lists \
    && wget -qO - https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -

RUN echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | tee /etc/apt/sources.list.d/coral-edgetpu.list

# The `python3-opencv` package isn't built with gstreamer on Ubuntu. So we need to manually build opencv.
ARG OPENCV_VERSION=4.3.0
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
        python3-pytest \
	python3-requests \
        build-essential \
        libedgetpu1-std \
        supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --upgrade pip setuptools==41.0.0 wheel && pip install -r /requirements.txt \
	https://dl.google.com/coral/python/tflite_runtime-2.1.0.post1-cp37-cp37m-linux_x86_64.whl \
    && apt-get purge -y \
        build-essential \
        python3-dev \
    && apt-get autoremove -y

ENV DEV_ALLOW_ALL_ORIGINS=true

RUN cd / && apt-get update && apt-get install -y git python3-edgetpu && git clone \
    https://github.com/google-coral/project-posenet.git && cd project-posenet && \
    git checkout f74ff7973e4b4349aaad9f50c7f0bc77fe33775b && sed -i 's/sudo / /g' \
    /project-posenet/install_requirements.sh && sh /project-posenet/install_requirements.sh
ENV PYTHONPATH=$PYTHONPATH:/project-posenet
ENV CONFIG_FILE=config-coral.ini

COPY . /repo
WORKDIR /repo
HEALTHCHECK --interval=30s --retries=2 --start-period=15s CMD bash healthcheck.bash
CMD supervisord -c supervisord.conf -n
