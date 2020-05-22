FROM node:14-alpine as frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json /frontend/
RUN npm install --production
COPY frontend /frontend
RUN npm run build

FROM tensorflow/tensorflow:latest-py3

RUN apt-get update && apt-get install -y pkg-config libsm6 libxext6 libxrender-dev

# get all pip packages
RUN pip install --upgrade pip setuptools==41.0.0 && pip install \
    aiofiles \
    fastapi \
    image \
    scipy \
    uvicorn \
    wget \
    opencv-python \
    pyzmq

COPY --from=neuralet/smart-social-distancing:latest-frontend /frontend/build /srv/frontend

COPY . /repo
WORKDIR /repo

EXPOSE 8000

ENTRYPOINT ["python", "neuralet-distancing.py"]
CMD ["--config", "config-x86.ini"]
