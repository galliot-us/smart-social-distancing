FROM nvcr.io/nvidia/l4t-base:r32.3.1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
	g++ \ 
	make \
	pkg-config \
        python3-pip \
        python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf $(which gcc) /usr/local/bin/gcc-aarch64-linux-gnu \
    && ln -sf $(which g++) /usr/local/bin/g++-aarch64-linux-gnu \
    && python3 -m pip install --upgrade pip setuptools==41.0.0 \
    && python3 -m pip install \
        aiofiles \
        fastapi \
        uvicorn \
    && apt-get autoremove -y

COPY --from=neuralet/smart-social-distancing:latest-frontend /frontend/build /srv/frontend

COPY ui/requirements.txt /ui/
WORKDIR /ui

RUN python3 -m pip install -r requirements.txt
COPY ui/ /ui
COPY libs/config_engine.py /ui/
COPY config-frontend.ini /ui/

#EXPOSE 8000

ENTRYPOINT ["python3", "web_gui.py"]
CMD ["--config", "config-frontend.ini"]
