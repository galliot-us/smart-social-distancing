FROM nvcr.io/nvidia/tensorrt:20.03-py3

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
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --upgrade pip setuptools==41.0.0 && pip install -r /requirements.txt \
    && apt-get purge -y \
        python3-dev \
    && apt-get autoremove -y

RUN apt-get update && apt-get install -y python3-dev && pip3 install torch==1.5.1 torchvision==0.6.1 openpifpaf==0.12a4
RUN pip3 install tensorflow==2.1.0 Keras-Applications==1.0.8 Keras-Preprocessing==1.1.0 
RUN pip3 install h5py==2.10.0 


RUN apt-get update && apt install -y git autoconf automake libtool curl make g++ unzip supervisor


RUN git clone https://github.com/protocolbuffers/protobuf.git \
&& cd protobuf \
&& git checkout v3.17.3 \
&& git submodule update --init --recursive \
&& chmod +x autogen.sh \
&& ./autogen.sh \
&& ./configure \
&& make -j$(nproc) \
&& make install \
&& ldconfig 

RUN git clone https://github.com/onnx/onnx-tensorrt.git \
&& cd onnx-tensorrt \
&& git checkout 7.0 \
&& git submodule update --init --recursive \
&& mkdir build \
&& cd build \
&& cmake .. -DTENSORRT_ROOT=/usr/src/tensorrt/ \
&& make -j$(nproc) \
&& make install

ENV DEV_ALLOW_ALL_ORIGINS=true
ENV CONFIG_FILE=config-x86-gpu-tensorrt.ini

COPY . /repo
WORKDIR /repo
CMD supervisord -c supervisord.conf -n
