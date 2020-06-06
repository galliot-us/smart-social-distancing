# See here for installing Docker for Nvidia on Jetson devices: 
# https://github.com/NVIDIA/nvidia-docker/wiki/NVIDIA-Container-Runtime-on-Jetson

FROM nvcr.io/nvidia/l4t-base:r32.3.1

ENV TZ=US/Pacific
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN wget https://github.com/Tony607/jetson_nano_trt_tf_ssd/raw/master/packages/jetpack4.3/tensorrt.tar.gz -O /opt/tensorrt.tar.gz
RUN tar -xzf /opt/tensorrt.tar.gz -C /usr/local/lib/python3.6/dist-packages/

RUN wget https://github.com/sasikiran/jetson_tx2_trt_ssd/raw/master/libflattenconcat.so -O /opt/libflattenconcat.so

RUN apt-get update && apt-get install -y python3-pip pkg-config

RUN apt-get install -y python3-opencv python3-scipy python3-matplotlib

RUN pip3 install pycuda fastapi uvicorn aiofiles pyzmq

ENTRYPOINT ["python3", "neuralet-distancing.py"]
CMD ["--config", "config-jetson.ini"]
WORKDIR /repo
EXPOSE 8000

COPY --from=neuralet/smart-social-distancing:latest-frontend /frontend/build /srv/frontend
COPY . /repo/
