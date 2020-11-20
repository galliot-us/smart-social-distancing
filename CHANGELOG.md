# Change Log

This file includes a list of notable changes to this project.

## [0.2.0](https://github.com/neuralet/smart-social-distancing/releases/tag/0.2.0)
Released on 2020-11-20.

#### Added:

* Support for running on x86 with GPU ([#72](https://github.com/neuralet/smart-social-distancing/pull/72))
* Endpoint to get version, device and whether the processor has been set up ([#84](https://github.com/neuralet/smart-social-distancing/pull/84))
* Endpoints to export raw data ([#74](https://github.com/neuralet/smart-social-distancing/pull/74))
* Improve fault tolerance ([#82](https://github.com/neuralet/smart-social-distancing/pull/82))

#### Updated:

* Documentation in Readme (several, mainly ([#73](https://github.com/neuralet/smart-social-distancing/pull/73))
* Refactored Endpoints to not end with / ([#76](https://github.com/neuralet/smart-social-distancing/pull/76))
* Some improvements in face mask detection like adding a label on top of bounding boxes ([#77](https://github.com/neuralet/smart-social-distancing/pull/77))
* Improved Object tracker (IOU tracker added) ([#79](https://github.com/neuralet/smart-social-distancing/pull/79))

#### Fixed:

* An error in face anonymizer when using PoseNet ([#80](https://github.com/neuralet/smart-social-distancing/pull/80), [#81](https://github.com/neuralet/smart-social-distancing/pull/81))

#### Removed:

* Deprecated frontend and ui backend ([#73](https://github.com/neuralet/smart-social-distancing/pull/73))

---

## [0.1.0](https://github.com/neuralet/smart-social-distancing/releases/tag/0.1.0)

This is the first release of the Smart Social Distancing app.
The app is dockerized and can run on Coral Dev Board, Coral USB Accelerator, Jetson Nano, x86 or Openvino.
It supports close contact detection, occupancy alerts and facemask detection on multiple video sources.

It also includes a frontend React App and a separate backend that manages some endpoints which both have been **deprecated** and will be removed in future versions.
