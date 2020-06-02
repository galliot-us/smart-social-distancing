# docker can be installed on the dev board following these instructions: 
# https://docs.docker.com/install/linux/docker-ce/debian/#install-using-the-repository , step 4: x86_64 / amd64
# 1) build: docker build -f amd64-usbtpu.Dockerfile -t "neuralet/smart-social-distancing:latest-amd64" .
# 2) run: docker run -it --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data neuralet/smart-social-distancing:latest-amd64

FROM amd64/debian:buster

RUN apt-get update && apt-get install -y wget gnupg usbutils \
    && rm -rf /var/lib/apt/lists \
    && wget -qO - https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -

RUN echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | tee /etc/apt/sources.list.d/coral-edgetpu.list

#ARG OPENCV_VERSION=4.3.0
#RUN apt-get update && apt-get install -y --no-install-recommends \
#        cmake \
#        curl \
#        g++ \
#        gcc \
#        git \
#        gstreamer1.0-plugins-bad \
#        gstreamer1.0-plugins-good \
#        gstreamer1.0-plugins-ugly \
#        gstreamer1.0-vaapi \
#        libavcodec-dev \
#        libavformat-dev \
#        libgstreamer-plugins-base1.0-dev \
#        libgstreamer1.0-dev \
#        libsm6 \
#        libswscale-dev \
#        libxext6 \
#        libxrender-dev \
#        make \
#        mesa-va-drivers \
#        pkg-config \
#        python3-dev \
#        python3-numpy \
#    && rm -rf /var/lib/apt/lists/* \
#    && cd /tmp/ \
#    && curl -L https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.tar.gz -o opencv.tar.gz \
#    && tar zxvf opencv.tar.gz && rm opencv.tar.gz \
#    && cd /tmp/opencv-${OPENCV_VERSION} \
#    && mkdir build \
#    && cd build \
#    && cmake -DBUILD_opencv_python3=yes -DPYTHON_EXECUTABLE=$(which python3) ../ \
#    && make -j$(nproc) \
#    && make install \
#    && cd /tmp \
#    && rm -rf opencv-${OPENCV_VERSION} \
#    && apt-get purge -y \
#        cmake \
#        git \
#        libgstreamer-plugins-base1.0-dev \
#        libgstreamer1.0-dev \
#        libxrender-dev \
#        python3-dev \
#    && apt-get autoremove -y

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libedgetpu1-std \
        pkg-config \
        python3-dev \
        python3-numpy \
        python3-opencv \
        python3-pillow \
        python3-pip \
        python3-scipy \
        python3-wget \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --upgrade pip setuptools==41.0.0 wheel && pip install \
        https://dl.google.com/coral/python/tflite_runtime-2.1.0.post1-cp37-cp37m-linux_x86_64.whl \
        aiofiles \
        fastapi \
        uvicorn \
    && apt-get purge -y \
        build-essential \
        pkg-config \
        python3-dev \
    && apt-get autoremove -y

ENTRYPOINT ["python3", "neuralet-distancing.py"]
CMD ["--config", "config-skeleton.ini"]
WORKDIR /repo
EXPOSE 8000

COPY --from=neuralet/smart-social-distancing:latest-frontend /frontend/build /srv/frontend

COPY . /repo
