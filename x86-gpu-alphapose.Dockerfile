FROM nvcr.io/nvidia/tensorflow:20.03-tf2-py3
#RUN apt-get update && apt-get install -y python3-dev  && conda update -y wrapt && pip3 install tensorflow==2.2 openpifpaf wget

#RUN ln -s /usr/local/cuda-10.2/targets/x86_64-linux/lib/libcudart.so.10.2 /usr/lib/x86_64-linux-gnu/libcudart.so.10.1
#RUN pip uninstall python3-opencv python-opencv
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
    && python3 -m pip install --upgrade pip setuptools==41.0.0 && pip install -r /requirements.txt \
    && apt-get purge -y \
        python3-dev \
    && apt-get autoremove -y

RUN apt-get update && apt-get install -y python3-dev
ENV DEV_ALLOW_ALL_ORIGINS=true
ENV AWS_SHARED_CREDENTIALS_FILE=/repo/.aws/credentials
ENV AWS_CONFIG_FILE=/repo/.aws/config
ENV TF_FORCE_GPU_ALLOW_GROWTH=true
ENV CONFIG_FILE=config-x86-gpu.ini
RUN python3 -m site --user-site > /root/tmp_variable && DCN_PATH=$(cat /root/tmp_variable)
COPY . /repo
RUN pip3 install torch==1.2 torchvision==0.4.0
#COPY ./libs/detectors/x86/alphapose/ /alphapose_packages
#COPY ./libs/detectors/x86/alphapose/setup.py /alphapose_packages/setup.py
WORKDIR /repo/libs/detectors/x86/alphapose
#ENV PYTHONPATH=/alphapose_packages
#
#RUN mkdir -p $(cat /root/tmp_variable)/alphapose_package && \
#cd $(cat /root/tmp_variable)/alphapose_package && \
RUN apt-get update && apt-get install -y libyaml-dev && pip3 install cython gdown && python3 setup.py build develop --user
RUN mkdir -p $(cat /root/tmp_variable)/alphapose_package && \
cp /repo/libs/detectors/x86/alphapose/models/layers/dcn/*.so $(cat /root/tmp_variable)/alphapose_package
#mv /repo/libs/detectors/x86/alphapose/setup.py $(cat /root/tmp_variable)/alphapose_package

WORKDIR /repo
HEALTHCHECK --interval=30s --retries=2 --start-period=15s CMD bash healthcheck.bash
CMD supervisord -c supervisord.conf -n
