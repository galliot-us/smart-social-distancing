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

You can read the [Smart Social Distancing tutorial](https://neuralet.com/docs/tutorials/smart-social-distancing/) on our website to learn more about the codebase architecture and implementation details. The following instructions will help you install the application and get started.

### Prerequisites

**Hardware**  
A host edge device. We currently support the following:
* NVIDIA Jetson Nano
* NVIDIA Jetson TX2
* Coral Dev Board
* AMD64 node with attached Coral USB Accelerator
* X86 node (also accelerated with [OpenVINO](https://docs.openvinotoolkit.org/))

**Software**
* You need to install [Docker](https://docs.docker.com/get-docker/) on your device.

### Install

The smart social distancing application consists of two components; the `frontend` and the `processor`. Each component should be run separately. In the following sections, we will cover the required steps to build and run each component, depending on the device you are using.


#### STEP 1: Clone the repository and download the sample video

Clone this repository to your local system by running this command:

```bash
git clone https://github.com/neuralet/smart-social-distancing.git
cd smart-social-distancing
```
Then, download the sample video:


```bash
# Download a sample video file from multiview object tracking dataset
# The video has been selected from this dataset: https://researchdatafinder.qut.edu.au/display/n27416
./download_sample_video.sh
```

#### STEP 2: Build the Docker image for the frontend

This step is optional if you are not going to build any docker images.

The frontend consists of two Dockerfiles: 
* `frontend.Dockerfile`: Builds the React app.
* `web-gui.Dockerfile`: Builds a FastAPI backend which serves the React app built in the previous Dockerfile.


To build the frontend, run:

```bash
docker build -f frontend.Dockerfile -t "neuralet/smart-social-distancing:latest-frontend" .
```

To run the frontend, run:

```bash
docker build -f web-gui.Dockerfile -t "neuralet/smart-social-distancing:latest-web-gui" .
docker run -it -p HOST_PORT:8000 --rm neuralet/smart-social-distancing:latest-web-gui 
```


To run the frontend on an edge device (only on Jetson), run:

```bash
# Run this commands on your PC/laptop:
docker build -f frontend.Dockerfile -t "neuralet/smart-social-distancing:latest-frontend" .
docker save -o "frontend_base_image.tar" neuralet/smart-social-distancing:latest-frontend
```

Then, move the file `frontend_base_image.tar` that was just built on your PC/laptop to your jetson platform and load it:
```bash
# Copy "frontend_image.tar" to your edge device and run this command on your device:
docker load -i "frontend_base_image.tar"
rm frontend_base_image.tar
```

Finally, build the web-gui image for Jetson:
```bash
docker build -f jetson-web-gui.Dockerfile -t "neuralet/smart-social-distancing:latest-web-gui-jetson" .

# And run it:
docker run -it -p HOST_PORT:8000 --rm neuralet/smart-social-distancing:latest-web-gui-jetson
```

**Important notes**

* If the `frontend` directory on your branch is not identical to the upstream `master` branch, you **must** build the frontend image with the tag "`neuralet/smart-social-distancing:latest-frontend`" *before building the main frontend image*.
Otherwise, skip this step, as we have already built the frontend for the `master` branch on Dockerhub.

* There is a `config-frontend.ini` file which tells the frontend where to find the processor container. You must set the "Processor" section of the config file with the correct IP and port of the processor.

* Building the frontend is resource-intensive. If you plan to host everything on an edge device, we suggest building the docker image on your PC/laptop first and then copying it to the edge device. However, you can always start the frontend container on a PC/laptop and the processor container on the edge device.

#### STEP 3: Build the Docker image for the processor

Follow the instructions according to the device you are using to build the Docker image for the processor.


**Run on Jetson Nano**
* You need to have JetPack 4.3 installed on your Jetson Nano.

```bash
# 1) Download TensorRT engine file built with JetPack 4.3:
./download_jetson_nano_trt.sh

# 2) Build Docker image for Jetson Nano (This step is optional. You can skip it if you want to pull the container from neuralet Dockerhub)
docker build -f jetson-nano.Dockerfile -t "neuralet/smart-social-distancing:latest-jetson-nano" .

# 3) Run Docker container:
docker run -it --runtime nvidia --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data -v "$PWD/config-jetson.ini":/repo/config-jetson.ini neuralet/smart-social-distancing:latest-jetson-nano
```

**Run on Jetson TX2**
* You need to have JetPack 4.3 installed on your Jetson TX2.

```bash
# 1) Download TensorRT engine file built with JetPack 4.3:
./download_jetson_tx2_trt.sh

# 2) Build Docker image for Jetson TX2 (This step is optional. You can skip it if you want to pull the container from neuralet Dockerhub)
docker build -f jetson-tx2.Dockerfile -t "neuralet/smart-social-distancing:latest-jetson-tx2" .

# 3) Run Docker container:
docker run -it --runtime nvidia --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data -v "$PWD/config-jetson.ini":/repo/config-jetson.ini neuralet/smart-social-distancing:latest-jetson-tx2
```

**Run on Coral Dev Board**
```bash
# 1) Build Docker image (This step is optional. You can skip it if you want to pull the container from neuralet Dockerhub)
docker build -f coral-dev-board.Dockerfile -t "neuralet/smart-social-distancing:latest-coral-dev-board" .

# 2) Run Docker container:
docker run -it --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data -v "$PWD/config-skeleton.ini":/repo/config-skeleton.ini neuralet/smart-social-distancing:latest-coral-dev-board
```

**Run on AMD64 node with a connected Coral USB Accelerator**
```bash
# 1) Build Docker image (This step is optional. You can skip it if you want to pull the container from neuralet Dockerhub)
docker build -f amd64-usbtpu.Dockerfile -t "neuralet/smart-social-distancing:latest-amd64" .

# 2) Run Docker container:
docker run -it --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data -v "$PWD/config-skeleton.ini":/repo/config-skeleton.ini neuralet/smart-social-distancing:latest-amd64
```

**Run on x86**
```bash
# 1) Build Docker image (This step is optional. You can skip it if you want to pull the container from neuralet Dockerhub)
docker build -f x86.Dockerfile -t "neuralet/smart-social-distancing:latest-x86_64" .

# 2) Run Docker container:
docker run -it -p HOST_PORT:8000 -v "$PWD/data":/repo/data -v "$PWD/config-x86.ini":/repo/config-x86.ini neuralet/smart-social-distancing:latest-x86_64
```

**Run on x86 using OpenVino**
```bash
# download model first
./download_openvino_model.sh

# 1) Build Docker image (This step is optional. You can skip it if you want to pull the container from neuralet Dockerhub)
docker build -f x86-openvino.Dockerfile -t "neuralet/smart-social-distancing:latest-x86_64_openvino" .

# 2) Run Docker container:
docker run -it -p HOST_PORT:8000 -v "$PWD/data":/repo/data -v "$PWD/config-x86-openvino.ini":/repo/config-x86-openvino.ini neuralet/smart-social-distancing:latest-x86_64_openvino
```

### Configurations
You can read and modify the configurations in `config-*.ini` files, accordingly:

`config-jetson.ini`: for Jetson Nano / TX2 

`config-coral.ini`: for Coral dev board / USB accelerator

`config-x86.ini`: for plain x86 (CPU) platforms without any acceleration

`config-x86-openvino.ini`: for x86 systems accelerated with OpenVINO


### API usage
After you run the processor's docker on your node, no matter if your frontend docker is running or not, you can use the Processor's API to control the Processor's Core, where all the process is getting done. 

* The API supported paths are now as the following:

 * `PROCESSOR_IP:PROCESSOR_PORT/process-video-cfg`: Sends command `PROCESS_VIDEO_CFG` to the Core and returns the response. 
It starts to process the video addressed in the configuration file. A true response means that the Core is going to try to process the video (with no guarantee), and a false response indicates that the process cannot start now. For example, it returns false when another process is already requested and running.

* `PROCESSOR_IP:PROCESSOR_PORT/stop-process-video`: Sends command `STOP_PROCESS_VIDEO` to the Core and returns the response. 
It stops processing the video at hand and returns a true or false response depending on whether the request is valid or not. For example, it returns false when no video is already being processed to be stopped.

* `PROCESSOR_IP:PROCESSOR_PORT/get-config`: Returns the config used by both the processor's API and Core.
Note that the config is shared between the API and Core. This command returns a single configuration set in JSON format specified in the Processor's Dockerfile.

* `PROCESSOR_IP:PROCESSOR_PORT/set-config`: Sets the given set of JSON configurations as the config for both API and Core and reloads the configuration. 
Note that the config is shared between the API and the Core. When setting the config, the Core's engine restarts so that all the methods and members (especially those initiated with the old config) can use the updated config. This attempt will stop processing the video - if any.

 > The config file given in the Dockerfile will be updated, but this will be inside your Docker and will be lost after Docker stops running. 

* Usage example: 

While the Processor's docker is up and running (you have to put the video file under `data/` before running this command):

```bash
curl -d '{"App": { "VideoPath" : "/repo/data/YOUR_VIDEO.mp4"} }' -H "Content-Type: application/json" -X POST http://PROCESSOR_IP:PROCESSOR_PORT/set-config 
```
Enter `http://PROCESSOR_IP:PROCESSOR_PORT/process-video-cfg` in your browser. If you look at the terminal that is running the Docker, you can see that your video is being loaded and processed. You can also refresh your dashboard to see the output.

> You may find some residual files stored under `data/web_gui/static/` that are from the previous streams and plots. This issue needs to be handled separately. You can mannually clean that path for now.


## Issues and Contributing

The project is under substantial active development; you can find our roadmap at https://github.com/neuralet/neuralet/projects/1. Feel free to open an issue, send a Pull Request, or reach out if you have any feedback.
* [Submit a feature request](https://github.com/neuralet/neuralet/issues/new?assignees=&labels=&template=feature_request.md&title=).
* If you spot a problem or bug, please let us know by [opening a new issue](https://github.com/neuralet/neuralet/issues/new?assignees=&labels=&template=bug_report.md&title=).


## Contact Us

* Visit our website at https://neuralet.com
* Email us at covid19project@neuralet.com
* Check out our other models at https://github.com/neuralet.
