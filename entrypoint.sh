#!/bin/sh

. /opt/conda/bin/activate 
conda activate geoedf

export PATH=/opt/conda/envs/geoedf/bin:$PATH
python3 processfile.py
