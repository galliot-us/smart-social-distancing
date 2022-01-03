[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# Smart Social Distancing

- [Smart Social Distancing](#smart-social-distancing)
  - [Introduction](#introduction)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Usage](#usage)
  - [Processor](#processor)
    - [Optional Parameters](#optional-parameters)
    - [Configuring AWS credentials](#configuring-aws-credentials)
    - [Enabling SSL](#enabling-ssl)
    - [Configuring OAuth2 in the endpoints](#configuring-oauth2-in-the-endpoints)
    - [Supported video feeds formats](#supported-video-feeds-formats)
    - [Change the default configuration](#change-the-default-configuration)
    - [API usage](#api-usage)
    - [Interacting with the processors' generated information](#interacting-with-the-processors-generated-information)
  - [Issues and Contributing](#issues-and-contributing)
  - [Contact Us](#contact-us)
  - [License](#license)

## Introduction

Smart Distancing is an open-source application to quantify social distancing measures using edge computer vision systems. Since all computation runs on the device, it requires minimal setup and minimizes privacy and security concerns. It can be used in retail, workplaces, schools, construction sites, healthcare facilities, factories, etc.

<div align="center">
  <img  width="100%" src="demo.gif">
</div>

You can run this application on edge devices such as NVIDIA's Jetson Nano / TX2 or Google's Coral Edge-TPU. This application measures social distancing rates and gives proper notifications each time someone ignores social distancing rules. By generating and analyzing data, this solution outputs statistics about high-traffic areas that are at high risk of exposure to COVID-19 or any other contagious virus.

If you want to understand more about the architecture you can read the following [post](https://neuralet.com/article/smart-social-distancing/).


Please join [our slack channel](https://join.slack.com/t/neuralet/shared_invite/zt-g1w9o45u-Y4R2tADwdGBCruxuAAKgJA) or reach out to covid19project@neuralet.com if you have any questions.

## Getting Started

You can read the [Get Started tutorial](https://www.lanthorn.ai/get-started) on Lanthorn's [website](https://www.lanthorn.ai/). The following instructions will help you get started.

### Prerequisites

#### Hardware

A host edge device. We currently support the following:

* NVIDIA Jetson Nano
* NVIDIA Jetson TX2
* Coral Dev Board
* AMD64 node with attached Coral USB Accelerator
* X86 node (also accelerated with Openvino)
* X86 node with Nvidia GPU

The features supported, the detection accuracy reached and the performance can vary from device to device.
 
#### Software

You should have [Docker](https://docs.docker.com/get-docker/) on your device.

Optionally, you can install [docker-compose](https://docs.docker.com/compose) to build and run the processor containers easily.
**In some edge devices, such as Coral or Jetson Nano, the [official installation guide](https://docs.docker.com/compose/install/) 
can fail because there isn't in the repository an already build image for that device architecture. If this is the case, we recommend installing docker-compose using [pip](https://pypi.org/project/docker-compose/)**


#### Download a sample video (Optional)

If you don't have any camera to test the solution you can use any video as an input source. You can download an example with the following command.

```bash
# Download a sample video file from multiview object tracking dataset
# The video is complied from this dataset: https://researchdatafinder.qut.edu.au/display/n27416
./download_sample_video.sh
```

### Usage

The smart social distancing app consists of two components: the `frontend` and the `processor`. 

#### Frontend

The frontend is a public [web app](https://app.lanthorn.ai) provided by [lanthorn](https://www.lanthorn.ai/) where you can signup for free. 
This web app allows you to configure some aspects of the processor (such as notifications and camera calibration) using a friendly UI. 
Moreover, it provides a dashboard that helps you to analyze the data that your cameras are processing. 

The frontend site uses HTTPs, in order to have it communicate with the processor, the latter must be either **Running with SSL enabled** (See [Enabling SSL](#enabling-ssl) on this Readme), **or** you must edit your site settings for `https://app.lanthorn.ai` in order to allow for Mixed Content (Insecure Content). **Without doing any of these, communication with the local processor will fail**

#### Running the processor

Make sure you have `Docker` installed on your device by following [these instructions](https://docs.docker.com/install/linux/docker-ce/debian).
The command that you need to execute will depend on the chosen device because each one has an independent Dockerfile.

There are three alternatives to run the processor in your device:
  1. Using `git` and building the docker image yourself (Follow the guide in [this](#running-the-processor-building-the-image) section). 
  2. Pulling the (already built) image from [Neuralet's Docker Hub repository](https://hub.docker.com/repository/docker/neuralet/smart-social-distancing) (Follow the guide in [this](#running-the-processor-from-neuralet-docker-hub-repository) section).
  3. Using docker-compose to build and run the processor (Follow the guide in [this](#running-the-processor-with-docker-compose) section).

##### Running a proof of concept

If you want to simply run the processor for just trying it out, then from the following steps you should only:
   1. Select your device and find its docker image. On x86, without a dedicated edge device, you should use either:
      a. **If the device has access to an Nvidia GPU:** GPU with TensorRT optimization.
      b. **If the device has access to an Intel CPU:** x86 using OpenVino.
      c. **Otherwise:** x86.
   2. Either **build the image or pull it from Dockerhub**. Don't forget to follow the script and download the model.
   3. Download the sample video running `./download_sample_video.sh`.
   4. Run the processor using the script listed in its device.

This way you can skip security steps such as enabling HTTPs communication or oauth and get a simple version of the processor running to see if it fits your use case.

Afterwards, if you intend on running the processor while consuming from a dedicated video feed, we advise you to return to this README and read it fully.

##### Running the processor building the image

Make sure your system fulfills the prerequisites and then clone this repository to your local system by running this command:

```bash
git clone https://github.com/neuralet/smart-social-distancing.git
cd smart-social-distancing
```

After that, `checkout` to the latest release:
```bash
git fetch --tags
# Checkout to the latest release tag
git checkout $(git tag | tail -1)
```

###### Run on Jetson Nano
* You need to have JetPack 4.3 installed on your Jetson Nano.

```bash
# 1) Download TensorRT engine file built with JetPack 4.3:
./download_jetson_nano_trt.sh

# 2) Build Docker image for Jetson Nano
docker build -f jetson-nano.Dockerfile -t "neuralet/smart-social-distancing:latest-jetson-nano" .

# 3) Run Docker container:
docker run -it --runtime nvidia --privileged -p HOST_PORT:8000 -v "$PWD":/repo -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-jetson-nano
```

###### Run on Jetson TX2
* You need to have JetPack 4.4 installed on your Jetson TX2. If you are using Openpifpaf as a detector, skip the first step as the TensorRT engine will be generated automatically with calling the `generate_tensorrt.bash` script by detector.

```bash
# 1) Download TensorRT engine file built with JetPack 4.3:
./download_jetson_tx2_trt.sh

# 2) Build Docker image for Jetson TX2
docker build -f jetson-tx2.Dockerfile -t "neuralet/smart-social-distancing:latest-jetson-tx2" .

# 3) Run Docker container:
docker run -it --runtime nvidia --privileged -p HOST_PORT:8000 -v "$PWD":/repo -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-jetson-tx2
```

###### Run on Coral Dev Board
```bash
# 1) Build Docker image (This step is optional, you can skip it if you want to pull the container from neuralet dockerhub)
docker build -f coral-dev-board.Dockerfile -t "neuralet/smart-social-distancing:latest-coral-dev-board" .

# 2) Run Docker container:
docker run -it --privileged -p HOST_PORT:8000 -v "$PWD":/repo -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-coral-dev-board
```

###### Run on AMD64 node with a connected Coral USB Accelerator
```bash
# 1) Build Docker image
docker build -f amd64-usbtpu.Dockerfile -t "neuralet/smart-social-distancing:latest-amd64" .

# 2) Run Docker container:
docker run -it --privileged -p HOST_PORT:8000 -v "$PWD":/repo -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-amd64
```

###### Run on x86
```bash

# If you use the OpenPifPaf model, download the model first:
./download-x86-openpifpaf-model.sh

# If you use the MobileNet model run this instead:
# ./download_x86_model.sh

# 1) Build Docker image
docker build -f x86.Dockerfile -t "neuralet/smart-social-distancing:latest-x86_64" .

# 2) Run Docker container:
docker run -it -p HOST_PORT:8000 -v "$PWD":/repo -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-x86_64
```

###### Run on x86 with GPU
Note that you should have [Nvidia Docker Toolkit](https://github.com/NVIDIA/nvidia-docker) to run the app with GPU support
```bash

# If you use the OpenPifPaf model, download the model first:
./download-x86-openpifpaf-model.sh

# If you use the MobileNet model run this instead:
# ./download_x86_model.sh

# 1) Build Docker image
docker build -f x86-gpu.Dockerfile -t "neuralet/smart-social-distancing:latest-x86_64_gpu" .

# 2) Run Docker container:
Notice: you must have Docker >= 19.03 to run the container with `--gpus` flag.
docker run -it --gpus all -p HOST_PORT:8000 -v "$PWD":/repo -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-x86_64_gpu
```

###### Run on x86 with GPU using TensorRT optimization

Note that you should have [Nvidia Docker Toolkit](https://github.com/NVIDIA/nvidia-docker) to run the app with GPU support
```bash


# 1) Build Docker image
docker build -f x86-gpu-tensorrt-openpifpaf.Dockerfile -t "neuralet/smart-social-distancing:latest-x86_64_gpu_tensorrt" .

# 2) Run Docker container:
# Notice: you must have Docker >= 19.03 to run the container with `--gpus` flag.
docker run -it --gpus all -p HOST_PORT:8000 -v "$PWD":/repo -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-x86_64_gpu_tensorrt
```

###### Run on x86 using OpenVino
```bash
# download model first
./download_openvino_model.sh

# 1) Build Docker image
docker build -f x86-openvino.Dockerfile -t "neuralet/smart-social-distancing:latest-x86_64_openvino" .

# 2) Run Docker container:
docker run -it -p HOST_PORT:8000 -v "$PWD":/repo  -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-x86_64_openvino
```

##### Running the processor from neuralet Docker Hub repository

Before running any of the images available in the Docker repository, you need to follow these steps to have your device ready.
  1. Create a `data` folder.
  2. Copy the `config` file (available in this repository) corresponding to your device.
  3. Copy the bash script(s) (available in this repository) required to download the model(s) your device requires.
  4. Optionally, copy the script `timezone.sh` (available in this repository) to run the processor using your system timezone instead of UTC.

Alternatively you may simply pull the folder structure from this repository.

###### Run on Jetson Nano
* You need to have JetPack 4.3 installed on your Jetson Nano.
```bash
# Download TensorRT engine file built with JetPack 4.3:
mkdir data/jetson
./download_jetson_nano_trt.sh

# Run Docker container:
docker run -it --runtime nvidia --privileged -p HOST_PORT:8000 -v $PWD/data:/repo/data -v $PWD/config-jetson-nano.ini:/repo/config-jetson-nano.ini -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-jetson-nano
```

###### Run on Jetson TX2
* You need to have JetPack 4.4 installed on your Jetson TX2. If you are using Openpifpaf as a detector, skip the first step as the TensorRT engine will be generated automatically with calling the `generate_tensorrt.bash` script by detector.

```bash
# Download TensorRT engine file built with JetPack 4.4
mkdir data/jetson
./download_jetson_tx2_trt.sh

# Run Docker container:
docker run -it --runtime nvidia --privileged -p HOST_PORT:8000 -v $PWD/data:/repo/data -v $PWD/config-jetson-tx2.ini:/repo/config-jetson-tx2.ini -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-jetson-tx2
```

###### Run on Coral Dev Board
```bash
# Run Docker container:
docker run -it --privileged -p HOST_PORT:8000 -v $PWD/data:/repo/data -v $PWD/config-coral.ini:/repo/config-coral.ini -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-coral-dev-board
```

###### Run on AMD64 node with a connected Coral USB Accelerator
```bash
# Run Docker container:
docker run -it --privileged -p HOST_PORT:8000 -v $PWD/data:/repo/data -v $PWD/config-coral.ini:/repo/config-coral.ini -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-amd64
```

###### Run on x86
```bash
# Download the models
mkdir data/x86
# If you use the OpenPifPaf model, download the model first:
./download-x86-openpifpaf-model.sh
# If you use the MobileNet model run this instead:
# ./download_x86_model.sh

# Run Docker container:
docker run -it -p HOST_PORT:8000 -v $PWD/data:/repo/data -v $PWD/config-x86.ini:/repo/config-x86.ini -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-x86_64
```

###### Run on x86 with GPU
Note that you should have [Nvidia Docker Toolkit](https://github.com/NVIDIA/nvidia-docker) to run the app with GPU support
```bash
# Download the models
mkdir data/x86
# If you use the OpenPifPaf model, download the model first:
./download-x86-openpifpaf-model.sh
# If you use the MobileNet model run this instead:
# ./download_x86_model.sh

# Docker container:
# Notice: you must have Docker >= 19.03 to run the container with `--gpus` flag.
docker run -it --gpus all -p HOST_PORT:8000 -v $PWD/data:/repo/data -v $PWD/config-x86-gpu.ini:/repo/config-x86-gpu.ini -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-x86_64_gpu
```

###### Run on x86 with GPU using TensorRT optimization

Note that you should have [Nvidia Docker Toolkit](https://github.com/NVIDIA/nvidia-docker) to run the app with GPU support
```bash
# Run Docker container:
# Notice: you must have Docker >= 19.03 to run the container with `--gpus` flag.
docker run -it --gpus all -p HOST_PORT:8000 -v $PWD/data:/repo/data -v $PWD/config-x86-gpu-tensorrt.ini:/repo/config-x86-gpu-tensorrt.ini -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-x86_64_gpu_tensorrt
```

###### Run on x86 using OpenVino
```bash
# Download the model
mkdir data/x86
./download_openvino_model.sh

# Run Docker container:
docker run -it -p HOST_PORT:8000 -v $PWD/data:/repo/data -v $PWD/config-x86-openvino.ini:/repo/config-x86-openvino.ini -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-x86_64_openvino
```
##### Running the processor with docker-compose

###### Run on Jetson Nano
* You need to have JetPack 4.3 installed on your Jetson Nano.

```bash
# 1) Download TensorRT engine file built with JetPack 4.3:
./download_jetson_nano_trt.sh

# 2) Build Docker image for Jetson Nano (you can omit this step and use the docker-hub images)
docker-compose -f docker-compose.yml -f docker-compose-jetson-nano.yml build

# 3) Run Docker container:
docker-compose -f docker-compose.yml -f docker-compose-jetson-nano.yml up
```

###### Run on Jetson TX2
* You need to have JetPack 4.4 installed on your Jetson TX2. If you are using Openpifpaf as a detector, skip the first step as the TensorRT engine will be generated automatically with calling the `generate_tensorrt.bash` script by detector.

```bash
# 1) Download TensorRT engine file built with JetPack 4.3:
./download_jetson_tx2_trt.sh

# 2) Build Docker image for Jetson TX2 (you can omit this step and use the docker-hub images)
docker-compose -f docker-compose.yml -f docker-compose-jetson-tx2.yml build

# 3) Run Docker container:
docker-compose -f docker-compose.yml -f docker-compose-jetson-tx2.yml up
```

###### Run on Coral Dev Board
```bash
# 1) Build Docker image for Coral (you can omit this step and use the docker-hub images)
docker-compose -f docker-compose.yml -f docker-compose-coral-dev.yml build

# 2) Run Docker container:
docker-compose -f docker-compose.yml -f docker-compose-coral-dev.yml up
```

###### Run on AMD64 node with a connected Coral USB Accelerator
```bash
# 1) Build Docker image for Coral USB Accelerator (you can omit this step and use the docker-hub images)
docker-compose -f docker-compose.yml -f docker-compose-amd64.yml build

# 2) Run Docker container:
docker-compose -f docker-compose.yml -f docker-compose-amd64.yml up
```

###### Run on x86
```bash

# If you use the OpenPifPaf model, download the model first:
./download-x86-openpifpaf-model.sh

# If you use the MobileNet model run this instead:
# ./download_x86_model.sh

# 2) Build Docker image for x86 (you can omit this step and use the docker-hub images)
docker-compose -f docker-compose.yml -f docker-compose-x86.yml build

# 3) Run Docker container:
docker-compose -f docker-compose.yml -f docker-compose-x86.yml up
```

###### Run on x86 with GPU
Note that you should have [Nvidia Docker Toolkit](https://github.com/NVIDIA/nvidia-docker) to run the app with GPU support
```bash

# If you use the OpenPifPaf model, download the model first:
./download-x86-openpifpaf-model.sh

# If you use the MobileNet model run this instead:
# ./download_x86_model.sh

# 2) Build Docker image for gpu (you can omit this step and use the docker-hub images)
docker-compose -f docker-compose.yml -f docker-compose-gpu.yml build

# 3) Run Docker container:
docker-compose -f docker-compose.yml -f docker-compose-gpu.yml up
```

###### Run on x86 with GPU using TensorRT optimization

Note that you should have [Nvidia Docker Toolkit](https://github.com/NVIDIA/nvidia-docker) to run the app with GPU support
```bash

# 1) Build Docker image for gpu using TensorRT (you can omit this step and use the docker-hub images)
docker-compose -f docker-compose.yml -f docker-compose-gpu-tensorrt.yml build

# 2) Run Docker container:
docker-compose -f docker-compose.yml -f docker-compose-gpu-tensorrt.yml up
```

###### Run on x86 using OpenVino
```bash
# download model first
./download_openvino_model.sh

# 2) Build Docker image for openvino (you can omit this step and use the docker-hub images)
docker-compose -f docker-compose.yml -f docker-compose-x86-openvino.yml build

# 2) Run Docker container:
docker-compose -f docker-compose.yml -f docker-compose-x86-openvino.yml up
```


## Processor

### Optional Parameters

This is a list of optional parameters for the `docker run` commands.
They are included in the examples of the [Run the processor](#running-the-processor) section.

#### Logging in the system's timezone

By default all docker containers use **UTC** as timezone, passing the flag ``` -e TZ=`./timezone.sh` ``` will make the container run on your system's timezone.

You may hardcode a value rather than using the `timezone.sh` script, such as `US/Pacific`. Changing the processor's timezone allows to have better control of when the `reports` are generated and the hours to correlate to the place where the processor is running.

Please note that the bash script may require permissions to execute (run `chmod +x timezone.sh`)

If you are running the processor directly from the Docker Hub repository, remember to copy/paste the script in the execution folder before adding the flag ``` -e TZ=`./timezone.sh` ```.

#### Persisting changes

We recommend adding the projects folder as a mounted volume (`-v "$PWD":/repo`) if you are building the docker image. If you are using the already built one we recommend creating a directory named `data` and mount it (`-v $PWD/data:/repo/data`).

#### Processing historical data

If you'd like to process historical data (videos stored on the device instead of a stream), you must follow two steps:
- Enable the `HistoricalDataMode` parameter on the device's `config-*.ini` file (see [Change the default configuration](#change-the-default-configuration))
- Run the `/repo/run_historical_metrics.sh` script on the `docker run` command.

Example using `x86`:
```bash
docker run -it -p HOST_PORT:8000 -v "$PWD":/repo -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-x86_64 /repo/run_historical_metrics.sh
```
### Configuring AWS credentials

Some of the implemented features allow you to upload files into an S3 bucket. To do that you need to provide the envs `AWS_BUCKET_REGION`, `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. An easy way to do that is to create a `.env` file (following the template `.env.example`) and pass the flag ```--env-file .env ``` when you run the processor.

### Enabling SSL

We recommend exposing the processors' APIs using HTTPS. To do that, you need to create a folder named `certs` with a valid certificate for the processor (with its corresponding private key) and configure it in the `config-*.ini` file (`SSLCertificateFile` and `SSLKeyFile` configurations).

If you don't have a certificate for the processor, you can create a self-signed one using [openssl](https://www.openssl.org/) and the scripts `create_ca.sh` and `create_processor_certificate.sh`.

```bash
# 1) Create your own CA (certification authority)
./create_ca.sh
# After the script execution, you should have a folder `certs/ca` with the corresponding *.key, *.pem and *.srl files

# 2) Create a certificate for the processor
./create_processor_certificate.sh <PROCESSOR_IP>
# After the script execution, you should have a folder `certs/processor` with the corresponding *.key, *.crt, *.csr and *.ext files
```

As you are using a self-signed certificate you will need to import the created CA (using the `.pem` file) in your browser as a trusted CA.

### Configuring OAuth2 in the endpoints

By default, all the endpoints exposed by the processors are accessible by everyone with access to the LAN. To avoid this vulnerability, the processor includes the possibility of configuring OAuth2 to keep your API secure.

To configure OAuth2 in the processor you need to follow these steps:
  1. Enabling OAuth2 in the API by setting in `True` the parameter `UseAuthToken` (included in the `API` section).
  2. Set into the container the env `SECRET_ACCESS_KEY`. This env is used to encode the JWT token. An easy way to do that is 
     to create a `.env` file (following the template `.env.example`) and pass the flag ```--env-file .env ``` when you run the processor.
  3. Create an API user. You can do that in two ways:
     1. Using the `create_api_user.py` script:

      Inside the docker container, execute the script `python3 create_api_user.py --user=<USER> --password=<PASSWORD>`. For example, if you are using an x86 device, you can execute the following script.
      ```bash
      docker run -it -p HOST_PORT:8000 -v "$PWD":/repo -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-x86_64 python3 create_api_user.py --user=<USER> --password=<PASSWORD>
      ```
     2. Using the `/auth/create_api_user` endpoint:
      Send a POST request to the endpoint `http://<PROCESSOR_HOST>:<PROCESSOR_PORT>/auth/create_api_user` with the following body:
      ```
      {
          "user": <USER>,
          "password": <PASSWORD>
      }
      ```

      After executing one of these steps, the `user` and `password` (hashed) will be stored in the file `/repo/data/auth/api_user.txt` inside the container. To avoid losing that file when the container is restarted, we recommend mounting the `/repo` directory as a volume.
  4. Request a valid token. You can obtain one by sending a PUT request to the endpoint `http://<PROCESSOR_HOST>:<PROCESSOR_PORT>/auth/access_token` with the following body:
      ```
      {
          "user": <USER>,
          "password": <PASSWORD>
      }
      ```
      The obtained token will be valid for 1 week (then a new one must be requested from the API) and needs to be sent as an `Authorization` header in all the requests. If you don't send the token (when the `UseAuthToken` attribute is set in `True`), you will receive a `401 Unauthorized` response.

### Supported video feeds formats
This processor uses [OpenCV VideoCapture](https://docs.opencv.org/3.4/d8/dfe/classcv_1_1VideoCapture.html), which means that it can process:

* Video files that are compatible with [FFmpeg](https://en.wikipedia.org/wiki/FFmpeg)
* Any URL of video stream in a **public protocol** such as RTSP and HTTP (`protocol://host:port/script_name?script_params|auth`)

Please note that:

* Although this processor can read and process a video file, this is mostly a development functionality; this is due to the fact that loggers yield statistics that are time dependant that assume a real-time stream being processed, in which if the processing capacity is lower than the FPS, frames are lost in favour of processing new frames. With a video file all frames are processed and on a slower model this might take a while (and yield wrong analytics).
* Some IP cameras implement their own private protocol that's not compatible with OpenCV.

If you want to integrate an IP camera that uses a private protocol, you should check with the camera provider if the device supports exporting its stream in a public protocol.
For example, [WYZE](https://wyze.com/) doesn't support RTSP as default, but [you have the possibility of installing a firmware that supports it](https://wyzelabs.zendesk.com/hc/en-us/articles/360026245231-Wyze-Cam-RTSP).
Same goes for [Google Nest Cameras](https://developers.google.com/nest/device-access/traits/device/camera-live-stream), although here a token must be kept alive to access the RTSP stream

### Change the default configuration
You can read and modify the configurations in `config-*.ini` files, accordingly:

`config-jetson-nano.ini`: for Jetson Nano

`config-jetson-tx2.ini`: for Jetson TX2

`config-coral.ini`: for Coral dev board / usb accelerator

`config-x86.ini`: for plain x86 (cpu) platforms without any acceleration

`config-x86-openvino.ini`: for x86 systems accelerated with Openvino

Please note that if you modify these values you should also set `[App]` `HasBeenConfigured` to `"True"`.
This allows for a client to recognize if this processor was previously configured.

You can also modify some of them using the [UI](https://app.lanthorn.ai). 
If you choose this option, make sure to mount the config file as a volume to keep the changes after any restart of the container (see section [Persisting changes](#persisting-changes)).

All the configurations are grouped in *sections* and some of them can vary depending on the chosen device.

- `[App]`
  - `HistoricalDataMode`: A boolean parameter that determines wheter to process historical data instead of a video stream.
  - `HasBeenConfigured`: A boolean parameter that states whether the *config.ini* was set up or not.
  - `Resolution`: Specifies the image resolution that the whole processor will use. If you are using a single camera we recommend using that resolution.
  - `Encoder`: Specifies the video encoder used by the processing pipeline.
  - `MaxProcesses`: Defines the number of processes executed in the processor. If you are using multiple cameras per processor we recommend increasing this number.
  - `DashboardURL`: Sets the url where the frontend is running. Unless you are using a custom domain, you should keep this value as https://app.lanthorn.ai/.
  - `DashboardAuthorizationToken`:  Configures the Authorization header required to sync the processor and the dashboard.
  - `SlackChannel`: Configures the slack channel used by the notifications. The chosen slack channel must exist in the configured workspace.
  - `OccupancyAlertsMinInterval`:  Sets the desired interval (in seconds) between occupancy alerts.
  - `MaxThreadRestarts`: Defines the number of restarts allowed per thread.
  - `HeatmapResolution`: Sets the resolution used by the heatmap report.
  - `LogPerformanceMetrics`: A boolean parameter to enable/disable the logging of "Performance Metrics" in the default processor log.
  We recommend enabling it to compare the performance of different devices, models, resolutions, etc.
  When it's enabled, the processor logs will include the following information every time 100 frames are processed:
      - Frames per second (FPS):
      - Average Detector time:
      - Average Classifier time:
      - Average Tracker time:
      - Post processing steps:
        - Average Objects Filtering time:
        - Average Social Distance time:
        - Average Anonymizer time:
  - `LogPerformanceMetricsDirectory`: When `LogPerformanceMetrics` is enabled, you can store the performance metrics into a CSV file setting the destination directory.
  - `EntityConfigDirectory`: Defines the location where the configurations of entities (such as sources and areas) are located.
  - `PorcessAreas`: A boolean parameter to enable/disable the area processing in the processor.

- `[Api]`
  - `Host`: Configures the host IP of the processor's API (inside docker). We recommend don't change that value and keep it as *0.0.0.0*.
  - `Post`: Configures the port of the processor's API (inside docker). Take care that if you change the default value (*8000*) you will need to change the startup command to expose the configured endpoint.
  - `UseAuthToken`: A boolean parameter to enable/disable OAuth2 in the API. If you set this value in *True* remember to follow the steps explained in the section [Configuring OAuth2 in the endpoints](#configuring-oauth2-in-the-endpoints).
  - `SSLEnabled`: A boolean parameter to enable/disable https/ssl in the API. We recommend setting this value in *True*. 
  - `SSLCertificateFile`: Specifies the location of the SSL certificate (required when you have *SSL enabled*). If you generate it following the steps defined in this Readme you should put */repo/certs/<your_ip>.crt*
  - [`SSLKeyFile`]: Specifies the location of the SSL key file (required when you have *SSL enabled*). If you generate it following the steps defined in this Readme you should put */repo/certs/<your_ip>.key*

- `[Core]`:
  - `Host`: Sets the host IP of the *QueueManager* (inside docker).
  - `QueuePort`: Sets the port of the *QueueManager* (inside docker).
  - `QueueAuthKey`: Configures the auth key required to interact with the *QueueManager*.

- `[Area_N]`:

  A single processor can manage multiple areas and all of them must be configured in the config file. You can generate this configuration in 3 different ways: directly in the config file, using the [UI](https://app.lanthorn.ai) or using the API.
  - `Id`: A string parameter to identify each area. This value must be *unique*.
  - `Name`: A string parameter to name each area. Although you can repeat the same name in multiple areas, we recommend don't do that.
  - `Cameras`: Configures the cameras (using the *ids*) included in the area. If you are configuring multiple cameras you should write the ids separated by commas. Each area should have at least one camera.
  - `NotifyEveryMinutes` and `ViolationThreshold`: Defines the *period of time* and *number of social distancing violations* desired to send notifications. For example, if you want to notify when *occurs more than 10 violations every 15 minutes*, you must set `NotifyEveryMinutes` in 15 and `ViolationThreshold` in 10.
  - `Emails`: Defines the emails list to receive the notification. Multiple emails can be written separating them by commas.
  - `EnableSlackNotifications`: A boolean parameter to enable/disable the Slack integration for notifications and daily reports. We recommend not editing this parameter directly and manage it from the [UI](https://app.lanthorn.ai) to configure your workspace correctly.
  - `OccupancyThreshold`: Defines the occupancy violation threshold. For example, if you want to notify when *there is more than 20 persons in the area* you must set `OccupancyThreshold` in 20.
  - `DailyReport`: When the parameter is set in *True*, the information of the previous day is sent in a summary report.
  - `DailyReportTime`: If the daily report is enabled, you can choose the time to receive the report. By default, the report is sent at 06:00.

- `[Source_N]`:

  In the config files, we use the *source* sections to specifies the camera's configurations. Similarly to the areas, a single processor can manage multiple cameras and all of them must be configured in the config file. You can generate this configuration in 3 different ways: directly in the config file, using the [UI](https://app.lanthorn.ai) or using the API.

  - `Id`: A string parameter to identify each camera. This value must be *unique*.
  - `Name`: A string parameter to name each area. Although you can repeat the same name in multiple cameras, we recommend don't do that.
  - `VideoPath`: Sets the path or url required to get the camera's video stream.
  - `Tags`: List of tags (separated by commas). This field only has an informative propose, change that value doesn't affect the processor behavior.
  - `NotifyEveryMinutes` and `ViolationThreshold`: Defines the *period of time* and *number of social distancing violations* desired to send notifications. For example, if you want to notify when *occurs more than 10 violations every 15 minutes*, you must set `NotifyEveryMinutes` in 15 and `ViolationThreshold` in 10.
  - `Emails`: Defines the emails list to receive the notification. Multiple emails can be written separating them by commas.
  - `EnableSlackNotifications`: A boolean parameter to enable/disable the Slack integration for notifications and daily reports. We recommend not editing this parameter directly and manage it from the [UI](https://app.lanthorn.ai) to configure your workspace correctly.
  - `DailyReport`: When the parameter is set in *True*, the information of the previous day is sent in a summary report.
  - `DailyReportTime`: If the daily report is enabled, you can choose the time to receive the report. By default, the report is sent at 06:00.
  - `DistMethod`: Configures the chosen distance method used by the processor to detect the violations. There are three different values: CalibratedDistance, CenterPointsDistance and FourCornerPointsDistance. If you want to use *CalibratedDistance* you will need to calibrate the camera from the [UI](https://app.lanthorn.ai).
  - `LiveFeedEnabled`: A boolean parameter that enables/disables the video live feed for the source.

- `[Detector]`:
  - `Device`: Specifies the device. The available values are *Jetson*, *EdgeTPU*, *Dummy*, *x86*, *x86-gpu*
  - `Name`: Defines the detector's models used by the processor. The models available varies from device to device. Information about the supported models are specified in a comment in the corresponding *config-<device>.ini* file.
  - `ImageSize`: Configures the moedel input size. When the image has a different resolution, it is resized to fit the model ones. The available values of this parameter depends on the model chosen.
  - `ModelPath`: Some of the supported models allow you to overwrite the default one. For example, if you have a specific model trained for your scenario you can use it.
  - `ClassID`: When you are using a multi-class detection model, you can definde the class id related to pedestrian in this parameter.
  - `MinScore`: Defines the person detection threshold. Any person detected by the model with a score less than the threshold will be ignored.
  - `TensorrtPrecision`: When you are using TensorRT version of Openpifpaf with GPU, Set TensorRT Precison 32 for float32 and 16 for float16 precision based on your GPU, if it supports both of them, float32 engine is more accurate and float16 is faster.
  - `DeviceId`: Required to specify the device id of the coral accelerator attached to the computer. This field **is only required when you have multiple accelerators connected to the same computer**.

- `[Classifier]`:

  Some of the supported devices include models that allow for detecting the body-pose of a person.
  This is a key component to **Facemask Detection**.
  If you want to include this feature, you need to uncomment this section, and use a model that supports the Classifier.
  Otherwise, you can delete or uncomment this section of the config file to save on CPU usage.
  - `Device`: Specifies the device. The available values are *Jetson*, *EdgeTPU*, *Dummy*, *x86*, *x86-gpu*
  - `Name`: Name of the facemask classifier used.
  - `ImageSize`: Configures the model input size. When the image has a different resolution, it is resized to fit the model ones. The available values of this parameter depends on the model chosen.
  - `ModelPath`: The same behavior as in the section `Detector`.
  - `MinScore`: Defines the facemask detection threshold. Any facemask detected by the model with a score less than the threshold will be ignored.
  - `TensorrtPrecision`: When you are using TensorRT version of Openpifpaf with GPU, Set TensorRT Precison 32 for float32 and 16 for float16 precision based on your GPU, if it supports both of them, float32 engine is more accurate and float16 is faster.
  - `MinImageSize`: Configures the minimum input size.

- `[Tracker]`:
  - `Name`: Name of the tracker used.
  - `MaxLost`: Defines the number of frames that an object should disappear to be considered as lost.
  - `TrackerIOUThreshold`: Configures the threshold of IoU to consider boxes at two frames as referring to the same object at IoU tracker.

- `[SourcePostProcessor_N]`:

  In the config files, we use the *SourcePostProcessor* sections to specify additional processing steps after running the detector and face mask classifier (if available) on the video sources. We support 3 different ones (identified by the field *Name*) that you enable/disable uncommenting/commenting them or with the *Enabled* flag.
    - `objects_filtering`: Used to remove invalid objects (duplicates or large).
      - `NMSThreshold`: Configures the threshold of minimum IoU to detect two boxes as referring to the same object.
    - `social_distance`: Used to measure the distance between objects and detect social distancing violations.
      - `DefaultDistMethod`: Defines the default distance algorithm for the cameras without *DistMethod* configuration.
      - `DistThreshold`: Configures the distance threshold for the *social distancing violations*
    - `anonymizer`: A step used to enable anonymization of faces in videos and screenshots.

- `[SourceLogger_N]`:

  Similar to the section *SourcePostProcessor_N*, we support multiple loggers (right now 4) that you enable/disable uncommenting/commenting them or with the *Enabled* flag.
  - `video_logger`: Generates a video stream with the processing results. It is a useful logger to monitor in real-time your sources.
  - `s3_logger`: Stores a screenshot of all the cameras in a S3 bucket.
    - `ScreenshotPeriod`: Defines a time period (expressed in minutes) to take a screenshot of all the cameras and store them in S3. If you set the value to 0, no screenshots will be taken.
    - `ScreenshotS3Bucket`: Configures the S3 Bucket used to store the screenshot.
  - `file_system_logger`: Stores the processed data in a folder inside the processor.
    - `TimeInterval`: Sets the desired logging interval for objects detections and violations.
    - `LogDirectory`: Defines the location where the generated files will be stored.
    - `ScreenshotPeriod`: Defines a time period (expressed in minutes) to take a screenshot of all the cameras and store them. If you set the value to 0, no screenshots will be taken.
    - `ScreenshotsDirectory`: Configures the folder dedicated to storing all the images generated by the processor. We recommend to set this folder to a mounted directory (such as */repo/data/processor/static/screenshots*).
  - `web_hook_logger`: Allows you to configure an external endpoint to receive in real-time the object detections and violations.
    - `TimeInterval`: Sets the desired logging interval (in seconds) for objects detections and violations.
    - `Endpoint`: Configures an endpoint url.
    - `Authorization`: Configures the Authorization header. For example: *Bearer <your_token>*.
    - `SendingInterval`: Configures the desired time interval (in seconds) to send data into the configured endpoint.
 
- `[AreaLogger_N]`:

  Similar to the section *SourceLogger_N* (for areas instead of cameras), we support multiple loggers (right now only 1, but we plan to include new ones in the future) that you enable/disable uncommenting/commenting them or with the *Enabled* flag.
  - `file_system_logger`: Stores the occupancy data in a folder inside the processor.
    - `LogDirectory`: Defines the location where the generated files will be stored.

- `[PeriodicTask_N]`:

  The processor also supports the execution of periodic tasks to generate reports, accumulate metrics, backup your files, etc. For now, we support the *metrics* and *s3_backup* tasks. You can enable/disable these functionalities uncommenting/commenting the section or with the *Enabled* flag.
  - `metrics`: Generates different reports (hourly, daily and live) with information about the social distancing infractions, facemask usage and occupancy in your cameras and areas. You need to have it enabled to see data in the [UI](https://app.lanthorn.ai) dashboard or use the `/metrics` endpoints.
      - `LiveInterval`: Expressed in minutes. Defines the time interval desired to generate live information.
  - `s3_backup`: Back up into an S3 bucket all the generated data (raw data and reports). To enable the functionality you need to configure the aws credentials following the steps explained in the section [Configuring AWS credentials](#configuring-aws-credentials).
      - `BackupInterval`: Expressed in minutes. Defines the time interval desired to back up the raw data.
      - `BackupS3Bucket`: Configures the S3 Bucket used to store the backups.


#### Use different models per camera
By default, all video streams are processing running against the same ML model.
When a processing threads starts running it verifies if a configuration .json file exists in the path: /repo/data/processor/config/sources/<camera_id>/ml_models/model_<device>.json
If no custom configuration is detected, a file will be generated using the default values from the `[Detector]` section, documented above. 
These JSONs contain the configuration of which ML Model is used for processing said stream, and can be modified either manually or using the endpoint  `/ml_model` documented below. Please note that models that differ in their location or name regarding the `./download_` scripts must specify their location in the field `file_path`.


### API usage
After you run the processor on your node, you can use the exposed API to control the Processor's Core, where all the process is getting done.

The available endpoints are grouped in the following subapis:
- `/config`: provides a pair of endpoint to retrieve and overwrite the current configuration file.
- `/cameras`: provides endpoints to execute all the CRUD operations required by cameras. These endpoints are very useful to edit the camera's configuration without restarting the docker process. Additionally, this subapi exposes the calibration endpoints.
- `/areas`: provides endpoints to execute all the CRUD operations required by areas.
- `/app`: provides endpoints to retrieve and update the `App` section in the configuration file.
- `/api`: provides endpoints to retrieve the `API` section in the configuration file.
- `/core`: provides endpoints to retrieve and update the `CORE` section in the configuration file.
- `/detector`: provides endpoints to retrieve and update the `Detector` section in the configuration file.
- `/classifier`: provides endpoints to retrieve and update the `Classifier` section in the configuration file.
- `/tracker`: provides endpoints to retrieve and update the `Tracker` section in the configuration file.
- `/source_post_processors`: provides endpoints to retrieve and update the `SourcePostProcessor_N` sections in the configuration file. You can use that endpoint to enable/disable a post processor step, change a parameter, etc.
- `/source_loggers`: provides endpoints to retrieve and update the `SourceLoggers_N` sections in the configuration file. You can use that endpoint to enable/disable a logger, change a parameter, etc.
- `/area_loggers`: provides endpoints to retrieve and update the `AreaLoggers_N` sections in the configuration file. You can use that endpoint to enable/disable a post processor step, change a parameter, etc.
- `/periodict_tasks`: provides endpoints to retrieve and update the `PeriodicTask_N` sections in the configuration file. You can use that endpoint to enable/disable the metrics generation.
- `/metrics`: a set of endpoints to retrieve the data generated by the metrics periodic task.
- `/export`: an endpoint to export (in zip format) all the data generated by the processor.
- `/slack`: a set of endpoints required to configure Slack correctly in the processor. We recommend to use these endpoints from the [UI](https://app.lanthorn.ai) instead of calling them directly.
- `/auth`: a set of endpoints required to configure OAuth2 in the processors' endpoints.
- `/ml_model`: an endpoint to edit the ML model and its parameters, that is used to process certain camera's video feed.
 
 Additionally, the API exposes 2 endpoints to stop/start the video processing
 - `PUT PROCESSOR_IP:PROCESSOR_PORT/start-process-video`: Sends command `PROCESS_VIDEO_CFG` to core and returns the response. It starts to process the video adressed in the configuration file. If the response is `true`, it means the core is going to try to process the video (no guarantee if it will do it), and if the response is `false`, it means the process can not be started now (e.g. another process is already requested and running).
 
 - `PUT PROCESSOR_IP:PROCESSOR_PORT/stop-process-video`: Sends command `STOP_PROCESS_VIDEO` to core and returns the response. It stops processing the video at hand, returns the response `true` if it stopped or `false`, meaning it can not (e.g. no video is already being processed to stop!).

The complete list of endpoints, with a short description and the signature specification is documented (with swagger) in the url `PROCESSOR_IP:PROCESSOR_PORT/docs`.

 ***NOTE*** Most of the endpoints update the config file given in the Dockerfile. If you don't have this file mounted (see section [Persisting changes](#persisting-changes)), these changes will be inside your container and will be lost after stopping it.

### Interacting with the processors' generated information

#### Generated information
The generated information can be split into 3 categories:
  - `Raw data`: This is the most basic level of information. It only includes the results of the detector, classifier, tracker, and any configured post-processor step.
  - `Metrics data`: **Only written if you have enabled the metrics periodic task** (see [section](#change-the-default-configuration)). These include metrics related to occupancy, social-distancing, and facemask usage; aggregated by hour and day.
  - `Notifications`: Situations that require an immediate response (such as surpassing the maximum occupancy threshold for an area) and need to be notified ASAP. The currently supported notification channels are email and slack.

#### Accessing and storing the information
All of the information that is generated by the processor is stored (by default) inside the edge device for security reasons. However, the processor provides features to easily export or backup the data to another system if required.

##### Storing the raw data
The raw data storage is managed by the `SourceLogger` and `AreaLogger` steps. By default, only the `video_logger` and the `file_system_logger` are enabled. As both steps store the data inside the processor (by default the folder `/repo/data/processor/static/`), we strongly recommend mounting that folder to keep the data safe when the process is restarted ([Persisting changes](#persisting-changes)).
Moreover, we recommend keeping active these steps because the [frontend](https://app.lanthorn.ai) and the metrics need them.

If you need to store (or process) the raw data in *real-time* outside the processor, you can activate the `web_hook_logger` and implement an endpoint that handles these events.
The `web_hook_logger` step is configured to send an event (a PUT request) using the following format:

```
{
            "version": ...,
            "timestamp": ...,
            "detected_objects": ...,
            "violating_objects": ...,
            "environment_score": ...,
            "detections": ...,
            "violations_indexes": ...
        }
```

You only need to implement an endpoint that matches the previous signature; configure its URL in the config file and the integration will be done. We recommend this approach if you want to integrate "Smart social distancing" with another existing system with real-time data.

Another alternative is to activate the periodic task `s3_backup`. This task will back up all the generated data (raw data and metrics) inside the configured S3 bucket, according to the time interval defined by the `BackupInterval` parameter. Before enabling this feature remember to configure AWS following the steps defined in the section [Configuring AWS credentials](#configuring-aws-credentials).

##### Accessing the metrics data
The data of aggregated metrics is stored in a set of CSV files inside the device. For now, we don't have implemented any mechanism to store these files outside the processor (the `web_hook_logger` only sends "raw data" events).
However, if you enable the `s3_backup` task, the previous day's metrics files will be backed up at AWS at the beginning of the day.

You can easily visualize the metrics information in the dashboard exposed in the [frontend](https://app.lanthorn.ai).
In addition, you can retrieve the same information through the API (see the metrics section in the API documentation exposed in http://<PROCESSOR_HOST>:<PROCESSOR_PORT>/docs#/Metrics).

##### Exporting the data
In addition to the previous features, the processor exposes an endpoint to export in zip format all the generated data.
The signature of this endpoint can be found in  http://<PROCESSOR_HOST>:<PROCESSOR_PORT>/docs#/Export.

## Issues and Contributing

The project is under substantial active development; you can find our roadmap at https://github.com/neuralet/neuralet/projects/1. Feel free to open an issue, send a Pull Request, or reach out if you have any feedback.
* [Submit a feature request](https://github.com/neuralet/neuralet/issues/new?assignees=&labels=&template=feature_request.md&title=).
* If you spot a problem or bug, please let us know by [opening a new issue](https://github.com/neuralet/neuralet/issues/new?assignees=&labels=&template=bug_report.md&title=).


## Contact Us

* Visit our website at https://neuralet.com
* Email us at covid19project@neuralet.com
* Check out our other models at https://github.com/neuralet.

## License

Most of the code in this repo is licensed under the [Apache 2](https://opensource.org/licenses/Apache-2.0) license.
However, some sections/classifiers include separate licenses.

These include:

* Openpifpaf model for x86 (see [license](libs/detectors/x86/openpifpaf_LICENSE))
* OFM facemask classifier model (see [license](libs/classifiers/x86/OFMClassifier_LICENCE))
