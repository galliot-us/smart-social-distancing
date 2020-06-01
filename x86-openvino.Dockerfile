FROM openvino/ubuntu18_runtime
ARG OPENCV_VERSION=4.3.0
USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
        cmake \
        g++ \
        gcc \
        git \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-vaapi \
        libavcodec-dev \
        libavcodec-extra \
        libavformat-dev \
        libgstreamer-plugins-base1.0-dev \
        libgstreamer1.0-dev \
        libsm6 \
        libswscale-dev \
        libxext6 \
        libxrender-dev \
        mesa-va-drivers \
        pkg-config \
        python3-numpy \
    && rm -rf /var/lib/apt/lists/*

RUN cd /tmp \
    && curl https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.tar.gz -o opencv.tar.gz -L \
    && tar zxvf opencv.tar.gz && rm opencv.tar.gz \
    && mv opencv-${OPENCV_VERSION} opencv \
    && mkdir opencv/build \
    && cd opencv/build \
    && cmake -DBUILD_opencv_python3=yes -DPYTHON_EXECUTABLE=/usr/local/bin/python3 ../ \
    && make -j$(nproc) \
    && make install \
    && cd /tmp \
    && rm -rf opencv

RUN pip3 install --upgrade pip setuptools==41.0.0 && pip3 install wget fastapi uvicorn aiofiles pyzmq scipy image

# Remove the opencv which is included in Openvino and is incompatible with globally-installed gstreamer
RUN rm -rf /opt/intel/openvino/opencv /opt/intel/openvino/python/cv2.* /opt/intel/openvino/python/python3/cv2.*

ADD docker/x86-openvino/openvino_setupvars.py /opt/openvino_setupvars.py
CMD env `python3 /opt/openvino_setupvars.py` python3 neuralet-distancing.py --config=config-x86-openvino.ini

WORKDIR /repo
EXPOSE 8000

COPY --from=neuralet/smart-social-distancing:latest-frontend /frontend/build /srv/frontend

COPY . /repo
