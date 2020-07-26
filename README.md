[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# Smart Social Distancing

## Introduction

Smart Distancing is an open-source application to quantify social distancing measures using edge computer vision systems. Since all computation runs on the device, it requires minimal setup and minimizes privacy and security concerns. It can be used in retail, workplaces, schools, construction sites, healthcare facilities, factories, etc.

<div align="center">
  <img  width="100%" src="demo.gif">
</div>

You can run this application on edge devices such as NVIDIA's Jetson Nano / TX2 or Google's Coral Edge-TPU. This application measures social distancing rates and gives proper notifications each time someone ignores social distancing rules. By generating and analyzing data, this solution outputs statistics about high-traffic areas that are at high risk of exposure to COVID-19 or any other contagious virus. The project is under substantial active development; you can find our roadmap at https://github.com/neuralet/neuralet/projects/1.

We encourage the community to join us in building a practical solution to keep people safe while allowing them to get back to their jobs. You can read more about the project motivation and roadmap here: https://docs.google.com/presentation/d/13EEt4JfdkYSqpPLpotx9taBHpNW6WtfXo2SfwFU_aQ0/edit?usp=sharing

Please join [our slack channel](https://join.slack.com/t/neuralet/shared_invite/zt-g1w9o45u-Y4R2tADwdGBCruxuAAKgJA) or reach out to covid19project@neuralet.com if you have any questions. 


## Getting Started

You can read the [Smart Social Distancing tutorial](https://neuralet.com/docs/tutorials/smart-social-distancing/) on our website. The following instructions will help you get started.

### Prerequisites

**Hardware**  
A host edge device. We currently support the following:
* NVIDIA Jetson Nano
* NVIDIA Jetson TX2
* Coral Dev Board
* AMD64 node with attached Coral USB Accelerator
* X86 node (also accelerated with Openvino)

**Software**
* You should have [Docker](https://docs.docker.com/get-docker/) on your device.

### Install

Make sure you have the prerequisites and then clone this repository to your local system by running this command:

```bash
git clone https://github.com/neuralet/smart-social-distancing.git
cd smart-social-distancing
```

### Usage

Make sure you have `Docker` installed on your device by following [these instructions](https://docs.docker.com/install/linux/docker-ce/debian).

The smart social distancing app consists of two components which must be run separately.
There is the `frontend` and the `processor`.
In the following sections we will cover how to build and run each of them depending on which device you are using.


**Download Required Files**
```bash
# Download a sample video file from multiview object tracking dataset
./download_sample_video.sh
```

**Building the Docker image for frontend**
(This step is optional if you are not going to build any docker image)

The frontend consists of 2 Dockerfiles: 
* `frontend.Dockerfile`: Builds the React app.
* `web-gui.Dockerfile`: Builds a FastAPI backend which serves the React app built in the previous Dockerfile.

If the `frontend` directory on your branch is not identical to the upstream `master` branch, you MUST build the frontend image with 
tag "`neuralet/smart-social-distancing:latest-frontend`" BEFORE BUILDING THE MAIN FRONTEND IMAGE.
Otherwise, skip this step, as we have already built the frontend for `master` branch on Dockerhub.

* To build the frontend run:

```bash
docker build -f frontend.Dockerfile -t "neuralet/smart-social-distancing:latest-frontend" .
```

* To run the frontend, run:

```bash
docker build -f web-gui.Dockerfile -t "neuralet/smart-social-distancing:latest-web-gui" .
docker run -it -p HOST_PORT:8000 --rm neuralet/smart-social-distancing:latest-web-gui 
```

> Important: There is a `config-frontend.ini` file which tells the frontend where to find the processor container. 
> You must set the "Processor" section of the config file with the correct IP and port of the processor.

---
***NOTE*** Building the frontend is resource intensive. If you are planning to host everything on an edge device, we suggest building the docker image on your PC/laptop first and then copy it to the edge device. However, you can always start the frontend container on a PC/laptop and the processor container on the edge device.
---

* To run the frontend on an edge device (Only possible on jetson for now):

```bash
# Run this commands on your PC/laptop:
docker build -f frontend.Dockerfile -t "neuralet/smart-social-distancing:latest-frontend" .
docker save -o "frontend_base_image.tar" neuralet/smart-social-distancing:latest-frontend
```

* Then, move the file `frontend_base_image.tar` that was just built on your PC/laptop to your jetson platform and load it:
```bash
# Copy "frontend_image.tar" to your edge device and run this command on your device:
docker load -i "frontend_base_image.tar"
rm frontend_base_image.tar
```

* Then build the web-gui image for jetson:
```bash
docker build -f jetson-web-gui.Dockerfile -t "neuralet/smart-social-distancing:latest-web-gui-jetson" .

# And run it:
docker run -it -p HOST_PORT:8000 --rm neuralet/smart-social-distancing:latest-web-gui-jetson
```

**The Next sections explain how to run the processor on different devices**

**Run on Jetson Nano**
* You need to have JetPack 4.3 installed on your Jetson Nano.

```bash
# 1) Download TensorRT engine file built with JetPack 4.3:
./download_jetson_nano_trt.sh

# 2) Build Docker image for Jetson Nano (This step is optional, you can skip it if you want to pull the container from neuralet dockerhub)
docker build -f jetson-nano.Dockerfile -t "neuralet/smart-social-distancing:latest-jetson-nano" .

# 3) Run Docker container:
docker run -it --runtime nvidia --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data neuralet/smart-social-distancing:latest-jetson-nano
```

**Run on Jetson TX2**
* You need to have JetPack 4.3 installed on your Jetson TX2.

```bash
# 1) Download TensorRT engine file built with JetPack 4.3:
./download_jetson_tx2_trt.sh

# 2) Build Docker image for Jetson TX2 (This step is optional, you can skip it if you want to pull the container from neuralet dockerhub)
docker build -f jetson-tx2.Dockerfile -t "neuralet/smart-social-distancing:latest-jetson-tx2" .

# 3) Run Docker container:
docker run -it --runtime nvidia --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data neuralet/smart-social-distancing:latest-jetson-tx2
```

**Run on Coral Dev Board**
```bash
# 1) Build Docker image (This step is optional, you can skip it if you want to pull the container from neuralet dockerhub)
docker build -f coral-dev-board.Dockerfile -t "neuralet/smart-social-distancing:latest-coral-dev-board" .

# 2) Run Docker container:
docker run -it --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data neuralet/smart-social-distancing:latest-coral-dev-board
```

**Run on AMD64 node with a connected Coral USB Accelerator**
```bash
# 1) Build Docker image (This step is optional, you can skip it if you want to pull the container from neuralet dockerhub)
docker build -f amd64-usbtpu.Dockerfile -t "neuralet/smart-social-distancing:latest-amd64" .

# 2) Run Docker container:
docker run -it --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data neuralet/smart-social-distancing:latest-amd64
```

**Run on x86**
```bash
# 1) Build Docker image (This step is optional, you can skip it if you want to pull the container from neuralet dockerhub)
docker build -f x86.Dockerfile -t "neuralet/smart-social-distancing:latest-x86_64" .

# 2) Run Docker container:
docker run -it -p HOST_PORT:8000 -v "$PWD/data":/repo/data neuralet/smart-social-distancing:latest-x86_64
```

**Run on x86 using OpenVino**
```bash
# download model first
./download_openvino_model.sh

# 1) Build Docker image (This step is optional, you can skip it if you want to pull the container from neuralet dockerhub)
docker build -f x86-openvino.Dockerfile -t "neuralet/smart-social-distancing:latest-x86_64_openvino" .

# 2) Run Docker container:
docker run -it -p HOST_PORT:8000 -v "$PWD/data":/repo/data neuralet/smart-social-distancing:latest-x86_64_openvino
```

### Configurations
You can read and modify the configurations in `config-*.ini` files, accordingly:

`config-jetson.ini`: for Jetson Nano / TX2 

`config-coral.ini`: for Coral dev board / usb accelerator

`config-x86.ini`: for plain x86 (cpu) platforms without any acceleration

`config-x86-openvino.ini`: for x86 systems accelerated with Openvion

Under the `[Detector]` section, you can modify the `Min score` parameter to define the person detection threshold. You can also change the distance threshold by altering the value of `DistThreshold`.

## Issues and Contributing

The project is under substantial active development; you can find our roadmap at https://github.com/neuralet/neuralet/projects/1. Feel free to open an issue, send a Pull Request, or reach out if you have any feedback.
* [Submit a feature request](https://github.com/neuralet/neuralet/issues/new?assignees=&labels=&template=feature_request.md&title=).
* If you spot a problem or bug, please let us know by [opening a new issue](https://github.com/neuralet/neuralet/issues/new?assignees=&labels=&template=bug_report.md&title=).


## Contact Us

* Visit our website at https://neuralet.com
* Email us at covid19project@neuralet.com
* Check out our other models at https://github.com/neuralet.
