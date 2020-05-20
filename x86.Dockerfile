FROM tensorflow/tensorflow:latest-py3

RUN apt-get update && apt-get install -y pkg-config libsm6 libxext6 libxrender-dev

RUN pip install --upgrade pip setuptools==41.0.0 && pip install opencv-python wget flask scipy image

COPY . /repo
WORKDIR /repo

EXPOSE 8000

ENTRYPOINT ["python", "neuralet-distancing.py"]
CMD ["--config", "config-x86.ini"]
