FROM continuumio/miniconda3

# File Author / Maintainer
MAINTAINER Rajesh Kalyanam "rkalyana@purdue.edu"

SHELL ["/bin/bash", "-c"]

USER root

RUN conda init bash \
        && conda create -n env -c anaconda python=3.6 netcdf4 requests \
        && conda install -n env -c conda-forge "icu<64" pika gdal shapely pyproj=1.9.6 pyhdf h5py hdfeos2

ENV PATH /opt/conda/envs/env/bin:${PATH}
RUN echo "conda activate env" > ~/.bashrc

RUN mkdir -p /app
RUN mkdir -p /srv/idata/

COPY . /app
run mv /app/idatatest/ /srv/idata/

WORKDIR /app

RUN ["chmod", "+x", "entrypoint.sh"]

#RUN apt-get update -y && apt-get --reinstall install  curl
#RUN ["curl", "-XGET", "http://129.114.16.188:8445/solr/hubzero-solr-core/query?q=*canary*"

ENTRYPOINT ["/app/entrypoint.sh"]
