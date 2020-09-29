FROM continuumio/miniconda3

SHELL ["/bin/bash", "-c"]

USER root

RUN conda create -n geoedf -c conda-forge python=3.7 netcdf4 requests pika gdal shapely pyproj pyhdf h5py hdfeos2

RUN mkdir -p /app
RUN mkdir -p /srv/idata/

COPY . /app
RUN mv /app/idatatest/ /srv/idata/

WORKDIR /app

RUN chmod +x entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
