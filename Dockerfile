FROM continuumio/miniconda3

SHELL ["/bin/bash", "-c"]

USER root

RUN apt-get update && apt-get -y install qgis qgis-plugin-grass npm git

RUN conda create -n geoedf -c conda-forge netcdf4 requests pika gdal shapely pyproj pyhdf h5py hdfeos2 qgis pyqt=5

ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib:/usr/lib/qgis/plugins/lib:$LD_LIBRARY_PATH

RUN npm install npm@latest -g && npm install -g yarn

RUN mkdir -p /app
RUN mkdir -p /srv/idata/

COPY . /app
RUN mv /app/idatatest/ /srv/idata/

ENV NVM_DIR=/usr/local/nvm
ENV NODE_VERSION=12.18.3

WORKDIR $NVM_DIR

RUN apt-get -y install curl

# Install nvm with node and npm
RUN curl https://raw.githubusercontent.com/creationix/nvm/v0.35.3/install.sh | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default

ENV NODE_PATH=$NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH=$NVM_DIR/v$NODE_VERSION/bin:$PATH

RUN cd /app  && \
     git clone --recursive https://github.com/qgis/qwc2-demo-app.git && \
     cd qwc2-demo-app && \
     yarn install --ignore-engines

WORKDIR /app

RUN chmod +x entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
