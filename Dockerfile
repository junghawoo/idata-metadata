FROM continuumio/miniconda3

# File Author / Maintainer
MAINTAINER Rajesh Kalyanam "rkalyana@purdue.edu"

SHELL ["/bin/bash", "-c"]

USER root

RUN conda init bash \
        && conda create -n env -c anaconda python=3.6 netcdf4 requests \
        && conda install -n env -c conda-forge pika gdal shapely pyproj=1.9.6 pyhdf h5py hdfeos2

ENV PATH /opt/conda/envs/env/bin:${PATH}
RUN echo "conda activate env" > ~/.bashrc

RUN mkdir -p /app

COPY . /app

WORKDIR /app

ENTRYPOINT ["entrypoint.sh"]
