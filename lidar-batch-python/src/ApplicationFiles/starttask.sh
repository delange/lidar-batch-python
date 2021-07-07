#!/bin/bash
##switch to home
#cd ~
##download miniconda Linux x64 installer
#wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.9.2-Linux-x86_64.sh -O ~/miniconda.sh
#
##run installation in silent mode
#bash ~/miniconda.sh -b -p $HOME/miniconda
#
##environment initialization
#source ~/miniconda/bin/activate
#conda init
#conda list
#conda install -c conda-forge pdal
#pdal --version
#
#---
# openup permissions
chmod 755 $AZ_BATCH_NODE_SHARED_DIR/task.sh
chmod 755 $AZ_BATCH_NODE_SHARED_DIR/lidar_application.py

#download miniconda Linux x64 installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O $AZ_BATCH_NODE_SHARED_DIR/miniconda.sh &&
cd $AZ_BATCH_NODE_SHARED_DIR &&

#run installation in silent mode
bash miniconda.sh -b -p $AZ_BATCH_NODE_SHARED_DIR/miniconda &&

#environment initialization
source $AZ_BATCH_NODE_SHARED_DIR/miniconda/bin/activate &&
conda init &&
conda activate &&
conda list &&
conda install -c conda-forge pdal python-pdal gdal entwine matplotlib &&
pdal --version