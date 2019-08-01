#!/bin/bash

conda activate env
PATH=/opt/conda/envs/env/bin:$PATH
echo $PATH
python processfile.py
