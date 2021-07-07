#!/bin/bash
cd $AZ_BATCH_TASK_WORKING_DIR
source $AZ_BATCH_NODE_SHARED_DIR/miniconda/bin/activate base
conda init
conda list
pdal --version
python3 $AZ_BATCH_NODE_SHARED_DIR/lidar_application.py --inputfile $1 --outputfile $2
