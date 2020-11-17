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
The frontend is a public [web app](https://beta.lanthorn.ai) provided by [lanthorn](https://www.lanthorn.ai/) where you can signup for free. 
This web app allows you to configure some aspects of the processor (such as notifications and camera calibration) using a friendly UI. 
Moreover, it provides a dashboard that helps you to analyze the data that your cameras are processing. 

The frontend site uses HTTPs, in order to have it communicate with the processor, the latter must be either **Running with SSL enabled** (See `Enabling SSL` on this Readme), **or** you must edit your site settings for `https://beta.lanthorn.ai` in order to allow for Mixed Content (Insecure Content). **Without doing any of these, communication with the local processor will fail**

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

##### Run on x86 with GPU
Note that you should have [Nvidia Docker Toolkit](https://github.com/NVIDIA/nvidia-docker) to run the app with GPU support
```bash

# If you use the OpenPifPaf model, download the model first:
./download-x86-openpifpaf-model.sh

# If you use the MobileNet model run this instead:
# ./download_x86_model.sh

# 1) Build Docker image (This step is optional, you can skip it if you want to pull the container from neuralet dockerhub)
docker build -f x86-gpu.Dockerfile -t "neuralet/smart-social-distancing:latest-x86_64_gpu" .

# 2) Run Docker container:
Notice: you must have Docker >= 19.03 to run the container with `--gpus` flag.
docker run -it --gpus all -p HOST_PORT:8000 -v "$PWD/data":/repo/data -v "$PWD/config-x86.ini":/repo/config-x86.ini -v "$PWD/certificates/processor":/repo/certs -e TZ=`./timezone.sh` neuralet/smart-social-distancing:latest-x86_64_gpu
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

You can also modify some of them using the [UI](https://beta.lanthorn.ai). 
If you choose this option, make sure to mount the config file as a volume to keep the changes after any restart of the container.

All the configurations are grouped in *sections* and some of them can vary depending on the chosen device.

- `[App]`
  - `Resolution`: Specifies the image resolution that the whole processor will use. If you are using a single camera we recommend using that resolution.
  - `Encoder`: Specifies the video encoder used by the processing pipeline.
  - `MaxProcesses`: Defines the number of processes executed in the processor. If you are using multiple cameras per processor we recommend increasing this number.
  - `ScreenshotPeriod`: Defines a time period (expressed in minutes) to take a screenshot of all the cameras and store them in S3. If you set the value to 0, no screenshots will be taken.
  - `ScreenshotS3Bucket`: Configures the S3 Bucket used to store the screenshot.
  - `ScreenshotsDirectory`: Configures the folder dedicated to storing all the images (for example the heatmap reports) generated by the processor. We recommend to set this folder to a mounted directory (such as */repo/data/processor/static/screenshots*)
  - `DashboardURL`: Sets the url where the frontend is running. Unless you are using a custom domain, you should keep this value as https://beta.lanthorn.ai/.
  - `EnableSlackNotifications`: A boolean parameter to enable/disable the Slack integration for notifications and daily reports. We recommend not editing this parameter directly and manage it from the [UI](https://beta.lanthorn.ai) to configure your workspace correctly.
  - `SlackChannel`: Configures the slack channel used by the notifications. The chosen slack channel must exist in the configured workspace.

- `[Api]`
  - `Host`: Configures the host IP of the processor's API (inside docker). We recommend don't change that value and keep it as *0.0.0.0*.
  - `Post`: Configures the port of the processor's API (inside docker). Take care that if you change the default value (*8000*) you will need to change the startup command to expose the configured endpoint.
  - `SSLEnabled`: A boolean parameter to enable/disable https/ssl in the API. We recommend setting this value in *True*. 
  - `SSLCertificateFile`: Specifies the location of the SSL certificate (required when you have *SSL enabled*). If you generate it following the steps defined in this Readme you should put */repo/certs/<your_ip>.crt*
  - [`SSLKeyFile`]: Specifies the location of the SSL key file (required when you have *SSL enabled*). If you generate it following the steps defined in this Readme you should put */repo/certs/<your_ip>.crt*

- `[Core]`:
  - `Host`: Sets the host IP of the *QueueManager* (inside docker).
  - `QueuePort`: Sets the port of the *QueueManager* (inside docker).
  - `QueueAuthKey`: Configures the auth key required to interact with the *QueueManager*.

- `[Area_N]`:

  A single processor can manage multiple areas and all of them must be configured in the config file. You can generate this configuration in 3 different ways: directly in the config file, using the [UI](https://beta.lanthorn.ai) or using the API.
  - `Id`: A string parameter to identify each area. This value must be *unique*.
  - `Name`: A string parameter to name each area. Although you can repeat the same name in multiple areas, we recommend don't do that.
  - `Cameras`: Configures the cameras (using the *ids*) included in the area. If you are configuring multiple cameras you should write the ids separated by commas. Each area should have at least one camera.
  - `NotifyEveryMinutes` and `ViolationThreshold`: Defines the *period of time* and *number of social distancing violations* desired to send notifications. For example, if you want to notify when *occurs more than 10 violations every 15 minutes*, you must set `NotifyEveryMinutes` in 15 and `ViolationThreshold` in 10.
  -`Emails`: Defines the emails list to receive the notification. Multiple emails can be written separating them by commas.
  - `OccupancyThreshold`: Defines the occupancy violation threshold. For example, if you want to notify when *there is more than 20 persons in the area* you must set `OccupancyThreshold` in 20.
  - `DailyReport`: When the parameter is set in *True*, the information of the previous day is sent in a summary report.
  - `DailyReportTime`: If the daily report is enabled, you can choose the time to receive the report. By default, the report is sent at 06:00.

- `[Source_N]`:

  In the config files, we use the *source* sections to specifies the camera's configurations. Similarly to the areas, a single processor can manage multiple cameras and all of them must be configured in the config file. You can generate this configuration in 3 different ways: directly in the config file, using the [UI](https://beta.lanthorn.ai) or using the API.

  - `Id`: A string parameter to identify each camera. This value must be *unique*.
  - `Name`: A string parameter to name each area. Although you can repeat the same name in multiple cameras, we recommend don't do that.
  - `VideoPath`: Sets the path or url required to get the camera's video stream.
  - `Tags`: List of tags (separated by commas). This field only has an informative propose, change that value doesn't affect the processor behavior.
  - `NotifyEveryMinutes` and `ViolationThreshold`: Defines the *period of time* and *number of social distancing violations* desired to send notifications. For example, if you want to notify when *occurs more than 10 violations every 15 minutes*, you must set `NotifyEveryMinutes` in 15 and `ViolationThreshold` in 10.
  -`Emails`: Defines the emails list to receive the notification. Multiple emails can be written separating them by commas.
  - `DailyReport`: When the parameter is set in *True*, the information of the previous day is sent in a summary report.
  - `DailyReportTime`: If the daily report is enabled, you can choose the time to receive the report. By default, the report is sent at 06:00.
  - `DistMethod`: Configures the chosen distance method used by the processor to detect the violations. There are three different values: CalibratedDistance, CenterPointsDistance and FourCornerPointsDistance. If you want to use *CalibratedDistance* you will need to calibrate the camera from the [UI](https://beta.lanthorn.ai).

- `[Detector]`:
  - `Device`: Specifies the device. The available values are *Jetson*, *EdgeTPU*, *Dummy*, *x86*
  - `Name`: Defines the detector's models used by the processor. The models available varies from device to device. Information about the supported models are specified in a comment in the corresponding *config-<device>.ini* file.
  - `ImageSize`: Configures the moedel input size. When the image has a different resolution, it is resized to fit the model ones. The available values of this parameter depends on the model chosen.
  - `ModelPath`: Some of the supported models allow you to overwrite the default one. For example, if you have a specific model trained for your scenario you can use it.
  - `ClassID`: When you are using a multi-class detection model, you can definde the class id related to pedestrian in this parameter.
  - `MinScore`: Defines the person detection threshold. Any person detected by the model with a score less than the threshold will be ignored.

- `[Classifier]`:

  Some of the supported devices includes the *facemask detection* feature. If you want to include this feature, you need to specify the classifier section.
  - `Name`: Name of the facemask classifier used.
  - `ImageSize`: Configures the moedel input size. When the image has a different resolution, it is resized to fit the model ones. The available values of this parameter depends on the model chosen.
  - `ModelPath`: The same behavior as in the section `Detector`.
  - `MinScore`: Defines the facemask detection threshold. Any facemask detected by the model with a score less than the threshold will be ignored.


- `[PostProcessor]`:
  - `MaxTrackFrame`: Defines the number of frames that an object should disappear to be considered as lost.
  - `NMSThreshold`: Configures the threshold of minimum IoU to detect two boxes as referring to the same object.
  - `DefaultDistMethod`: Defines the default distance algorithm for the cameras without *DistMethod* configuration.
  - `DistThreshold`: Configures the distance threshold for the *social distancing violations*
  - `Anonymize`: A boolean parameter to enable/disable anonymization of faces in videos and screenshots.

- `[Logger]`:
  - `Name`: Configures the chosen logger. For now, we only support the *csv_logger*.
  - `TimeInterval`: Sets the desired logging interval for objects detections and violations.
  - `LogDirectory`: Defines the location where the generated files will be stored.
  - `EnableReports`: A boolean parameter to enable/disable the reports generation.
  - `HeatmapResolution`: Sets the resolution used by the heatmap report.
  - `WebHooksEndpoint`: Configures an endpoint to receive in real-time the objects detections and violations.

### API usage
After you run the processor on your node, you can use the exposed API to control the Processor's Core, where all the process is getting done.

The available endpoints are grouped in the following subapis:
- `/config`: provides a pair of endpoint to retrieve and overwrite the current configuration file.
- `/cameras`: provides endpoints to execute all the CRUD operations required by cameras. These endpoints are very useful to edit the camera's configuration without restarting the docker process. Additionally, this subapi exposes the calibration endpoints.
- `/areas`: provides endpoints to execute all the CRUD operations required by areas.
- `/reports`: a set of endpoints to retrieve the data generated by the processor.
- `/slack`: a set of endpoints required to configure Slack correctly in the processor. We recommend to use these endpoints from the [UI](https://beta.lanthorn.ai) instead of calling them directly.
 
 Additionally, the API exposes 2 endpoints to stop/start the video processing
 - `PUT PROCESSOR_IP:PROCESSOR_PORT/start-process-video`: Sends command `PROCESS_VIDEO_CFG` to core and returns the response. It starts to process the video adressed in the configuration file. If the response is `true`, it means the core is going to try to process the video (no guarantee if it will do it), and if the response is `false`, it means the process can not be started now (e.g. another process is already requested and running)
 
 - `PUT PROCESSOR_IP:PROCESSOR_PORT/stop-process-video`: Sends command `STOP_PROCESS_VIDEO` to core and returns the response. It stops processing the video at hand, returns the response `true` if it stopped or `false`, meaning it can not (e.g. no video is already being processed to stop!)

The complete list of endpoints, with a short description and the signature specification is documented (with swagger) in the url `PROCESSOR_IP:PROCESSOR_PORT/docs`

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
