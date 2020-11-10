[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# Smart Social Distancing

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

**Hardware**

A host edge device. We currently support the following:

* NVIDIA Jetson Nano
* NVIDIA Jetson TX2
* Coral Dev Board
* AMD64 node with attached Coral USB Accelerator
* X86 node (also accelerated with Openvino)

The features supported, the detection accuracy reached and the performance can vary from device to device.
 
**Software**

You should have [Docker](https://docs.docker.com/get-docker/) on your device.

### Install

Make sure you have the prerequisites and then clone this repository to your local system by running this command:

```bash
git clone https://github.com/neuralet/smart-social-distancing.git
cd smart-social-distancing
```

### Download a sample video
If you don't have any camera to test the solution you can use any video as an input source. You can download an example with the following command.

```bash
# Download a sample video file from multiview object tracking dataset
# The video is complied from this dataset: https://researchdatafinder.qut.edu.au/display/n27416
./download_sample_video.sh
```

### Usage
The smart social distancing app consists of two components: the `frontend` and the `processor`. 

#### Frontend
The frontend is a public [webapp](http://beta.lanthorn.ai) provided by [lanthorn](https://www.lanthorn.ai/) where you can signup for free. This web app allows you to configure some aspects of the processor (such as notifications and calibration) using a friendly UI. Moreover, it provides a dashboard that helps you to analyze the data that your cameras are processing. 

#### Processor

Make sure you have `Docker` installed on your device by following [these instructions](https://docs.docker.com/install/linux/docker-ce/debian).

##### Optional Parameters

This is a list of optional parameters for the `docker run` commands.
They are included in the examples of this section.

**Logging in the system's timezone**

By default all docker containers use **UTC** as timezone, passing the flag ``` -e TZ=`./timezone.sh` ``` will make the container run on your system's timezone.

You may hardcode a value rather than using the `timezone.sh` script, such as `US/Pacific`. Changing the processor's timezone allows to have better control of when the `reports` are generated and the hours to correlate to the place where the processor is running.

Please note that the bash script may require permissions to execute `chmod +777 timezone.sh`

**Persisting changes on the config.ini file**

Adding the respective `config.ini` as a volume (as for example `-v "$PWD/config-jetson.ini":/repo/config-jetson.ini`). Will allow for syncing changes of said file.

##### Enabling SSL

We recommend exposing the processors' APIs using HTTPS. To do that, you need to add as a volume (for example  `-v "$PWD/certificates/processor":/repo/certs` ) a folder with a valid certificate for the processor (with its corresponding private key) and configure it in the `config-*.ini` file (`SSLCertificateFile` and `SSLKeyFile` configurations).

If you don't have a certificate for the processor, you can create a self-signed one using [openssl](https://www.openssl.org/) and the scripts `create_ca.sh` and `create_processor_certificate.sh`.

```bash
# 1) Create your own CA (certification authority)
./create_ca.sh
# After the script execution, you should have a folder `certificates/ca` with the corresponding *.key, *.pem and *.srl files

# 2) Create a certificate for the processor
./create_processor_certificate.sh <PROCESSOR_IP>
# After the script execution, you should have a folder `certificates/processor` with the corresponding *.key, *.crt, *.csr and *.ext files
```

As you are using a self-signed certificate you will need to import the created CA (using the `.pem` file) in your browser as a trusted CA.

##### Run on Jetson Nano
* You need to have JetPack 4.3 installed on your Jetson Nano.

```bash
# 1) Download TensorRT engine file built with JetPack 4.3:
./download_jetson_nano_trt.sh

# 2) Build Docker image for Jetson Nano (This step is optional, you can skip it if you want to pull the container from neuralet dockerhub)
docker build -f jetson-nano.Dockerfile -t "neuralet/smart-social-distancing:latest-jetson-nano" .

# 3) Run Docker container:
docker run -it --runtime nvidia --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data -v "$PWD/config-jetson.ini":/repo/config-jetson.ini -v "$PWD/certificates/processor":/repo/certs -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-jetson-nano
```

##### Run on Jetson TX2
* You need to have JetPack 4.3 installed on your Jetson TX2.

```bash
# 1) Download TensorRT engine file built with JetPack 4.3:
./download_jetson_tx2_trt.sh

# 2) Build Docker image for Jetson TX2 (This step is optional, you can skip it if you want to pull the container from neuralet dockerhub)
docker build -f jetson-tx2.Dockerfile -t "neuralet/smart-social-distancing:latest-jetson-tx2" .

# 3) Run Docker container:
docker run -it --runtime nvidia --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data -v "$PWD/config-jetson.ini":/repo/config-jetson.ini -v "$PWD/certificates/processor":/repo/certs -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-jetson-tx2
```

##### Run on Coral Dev Board
```bash
# 1) Build Docker image (This step is optional, you can skip it if you want to pull the container from neuralet dockerhub)
docker build -f coral-dev-board.Dockerfile -t "neuralet/smart-social-distancing:latest-coral-dev-board" .

# 2) Run Docker container:
docker run -it --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data -v "$PWD/config-coral.ini":/repo/config-coral.ini -v "$PWD/certificates/processor":/repo/certs -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-coral-dev-board
```

##### Run on AMD64 node with a connected Coral USB Accelerator
```bash
# 1) Build Docker image (This step is optional, you can skip it if you want to pull the container from neuralet dockerhub)
docker build -f amd64-usbtpu.Dockerfile -t "neuralet/smart-social-distancing:latest-amd64" .

# 2) Run Docker container:
docker run -it --privileged -p HOST_PORT:8000 -v "$PWD/data":/repo/data -v "$PWD/config-coral.ini":/repo/config-coral.ini -v "$PWD/certificates/processor":/repo/certs -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-amd64
```

##### Run on x86
```bash

# If you use the OpenPifPaf model, download the model first:
./download-x86-openpifpaf-model.sh

# If you use the MobileNet model run this instead:
# ./download_x86_model.sh

# 1) Build Docker image (This step is optional, you can skip it if you want to pull the container from neuralet dockerhub)
docker build -f x86.Dockerfile -t "neuralet/smart-social-distancing:latest-x86_64" .

# 2) Run Docker container:
docker run -it -p HOST_PORT:8000 -v "$PWD/data":/repo/data -v "$PWD/config-x86.ini":/repo/config-x86.ini -v "$PWD/certificates/processor":/repo/certs -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-x86_64
```

##### Run on x86 using OpenVino
```bash
# download model first
./download_openvino_model.sh

# 1) Build Docker image (This step is optional, you can skip it if you want to pull the container from neuralet dockerhub)
docker build -f x86-openvino.Dockerfile -t "neuralet/smart-social-distancing:latest-x86_64_openvino" .

# 2) Run Docker container:
docker run -it -p HOST_PORT:8000 -v "$PWD/data":/repo/data -v "$PWD/config-x86-openvino.ini":/repo/config-x86-openvino.ini -v "$PWD/certificates/processor":/repo/certs  -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-x86_64_openvino
```

### Configurations
You can read and modify the configurations in `config-*.ini` files, accordingly:

`config-jetson.ini`: for Jetson Nano / TX2

`config-coral.ini`: for Coral dev board / usb accelerator

`config-x86.ini`: for plain x86 (cpu) platforms without any acceleration

`config-x86-openvino.ini`: for x86 systems accelerated with Openvino

Some examples of changes that you can apply are:

- Under the `[Detector]` section, you can modify the `MinScore` parameter to define the person detection threshold. You can also change the distance threshold by altering the value of `DistThreshold`.
- Under the `[API]` section, you can modify the `SSLEnabled` parameter to enable/disable HTTPS/SSL in the processor
- Under the `[Logger]` section, you can modify the `TimeInterval` to set the desired logging interval. In the same section, you can change the destination of the file with the parameter `LogDirectory`.  


### API usage
After you run the processor on your node, you can use the exposed API to control the Processor's Core, where all the process is getting done.

* Some of the API supported paths are now as the following:

 1- `PUT PROCESSOR_IP:PROCESSOR_PORT/start-process-video`: Sends command `PROCESS_VIDEO_CFG` to core and returns the response. It starts to process the video adressed in the configuration file. If the response is `true`, it means the core is going to try to process the video (no guarantee if it will do it), and if the response is `false`, it means the process can not be started now (e.g. another process is already requested and running)

 2- `PUT PROCESSOR_IP:PROCESSOR_PORT/stop-process-video`: Sends command `STOP_PROCESS_VIDEO` to core and returns the response. It stops processing the video at hand, returns the response `true` if it stopped or `false`, meaning it can not (e.g. no video is already being processed to stop!)

 3- `GET PROCESSOR_IP:PROCESSOR_PORT/config`: It returns the config which is used by processor in json format. This is the file you have used in your Processor's Dockerfile.

 4- `PUT PROCESSOR_IP:PROCESSOR_PORT/config`: It sets the given set of json configurations in the config, and reloads the configuration. Core's engine is also restarted so all methods and members (specially those which were initiated with the old config) can use the updated config (this will stop the processing of the video - if any).

The rest of the endpoints are documented with swagger in the url `PROCESSOR_IP:PROCESSOR_PORT/docs`

 ***NOTE*** Most of the endpoints update the config file given in the Dockerfile. If you don't have this file mounted, these changes will be inside your container and will be lost after stopping it.

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
