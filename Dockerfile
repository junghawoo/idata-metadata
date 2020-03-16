FROM continuumio/miniconda3

SHELL ["/bin/bash", "-c"]

USER root

RUN conda init bash \
        && conda create -n env -c conda-forge python netcdf4 requests pika gdal shapely pyproj pyhdf h5py hdfeos2

ENV PATH /opt/conda/envs/env/bin:${PATH}
RUN echo "conda activate env" > ~/.bashrc

RUN mkdir -p /app
RUN mkdir -p /srv/idata/

COPY . /app
RUN mv /app/idatatest/ /srv/idata/

WORKDIR /app

#RUN apt-get update -y && apt-get --reinstall install  curl
#RUN ["curl", "-XGET", "http://129.114.16.188:8445/solr/hubzero-solr-core/query?q=*canary*"
# wait-for-it script gives rabbitmq server 30 seconds to start before trying to connect 
RUN ["chmod", "+x", "wait-for-it.sh"]


ENTRYPOINT ["./wait-for-it.sh", "idata-pipeline_default:5672", "-t", "30", "--", "python", "processfile.py"]
#ENTRYPOINT ["/app/entrypoint.sh"]
