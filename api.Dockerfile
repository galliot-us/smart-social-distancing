FROM python:3.8-slim

RUN python3 -m pip install --upgrade pip setuptools==41.0.0 && pip install aiofiles fastapi uvicorn 
ENV DEV_ALLOW_ALL_ORIGINS=true
WORKDIR /repo 
ENTRYPOINT ["python3", "start_api.py"]
CMD ["--config", "config-api.ini"]
