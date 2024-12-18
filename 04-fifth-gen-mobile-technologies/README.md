# TP 4: Fifth Generation Mobile Technologies

- **Related course module**: IR.3503 - Virtual Infrastructure
- **Tutorial scope**: 5G Mobile Technologies
- **Technologies**: 5G, Linux

During this tutorial, we will learn few things like:
- What are the main NFs of the 5GC ?
- How can we deploy an end-to-end 5G system ?
- What are the main configuration elements of the 5GC ?


## Prerequisites

### VM deployment

> Skip this step if you have an already created VM

You need to create a VM using a Linux-based distribution of your choosing, e.g. https://lubuntu.me/downloads/ 

To create a VM you can use one of the following VMMs:

  - VirtualBox: https://www.virtualbox.org/
  - Vagrant + VirtualBox: https://www.vagrantup.com
  - VMware Workstation Player: https://www.vmware.com/uk/products/workstation-player.html
  - etc.

- an **ssh client** already configured on you desktop
- **credentials** for your VM

## Environment Setup (~30 minutes)

### Install Docker Engine

Use the official documentation to install docker engine: https://docs.docker.com/engine/install/

### Install Docker Compose

Use the official documentation to install docker compose: https://docs.docker.com/compose/install/

### Install free5gc/gtp5g kernel module

Follow the installation instructions provided here: https://github.com/free5gc/gtp5g

## Configuration (~60 minutes)

### Get free5gc-compose

Git clone the free5gc-compose project from: https://github.com/free5gc/free5gc-compose

### Explore the configuration

 1. What is the configured Public Land Mobile Network (PLMN) ID ?
 2. What are the configured 5G slices ? explain the "sst" and "sd"?
 3. What are the integrity algorithms used by the Access and Mobility management Function ?
 4. What are the ciphering algorithms used by the Access and Mobility management Function ?
 5. What are the supported PLMN IDs by the AUthentication Server Function ? what do you notice if you compare it to AMF PLMN ID?
 6. What is the configured Tracking Area Code for the gNodeB ?
 7. What are the 5G slices supported by the gNodeB ?
 8. What is the N2 service port of the AMF ?
 9. What is the service port of the Network Repository Function ?
 11. What are the available Data Network Names ?
 12. What are the IP pools for each Data network in each slice ?
 13. What is the Subscription Permanent Identifier of the UE default configuration ?
 14. What are the integrity algorithms supported by the UE ?
 15. What are the ciphering algorithms supported by the UE ?

## Deployment of 5G mobile network (~30 minutes)

### NFs

Use the provided docker-compose file to deploy the following components:

  - gNB
  - NRF
  - AMF
  - SMF
  - PCF
  - NSSF
  - AUSF
  - UDM
  - UDR
  - UPF

### WebUI

Connect to the WebUI and verify that your 5GC is up and running.

## Attach a UE, capture traffic, and analyze (~60 minutes)

### UE provisionning


Provision a UE in the 5G core network using the WebUI (localhost:5000),

### Attachment procedure

Start an attachment procedure of the UE to the gNB and core network,  see the **Option 1 or 2** in https://github.com/free5gc/free5gc-compose

### Analysis

Capture the application logs and the registration procedure, and analyse the protocols in use
