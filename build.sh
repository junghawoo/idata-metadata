#!/usr/bin/env bash

python3 -u /app/update-qgis-project.py $@

cp /app/themesConfig.json /app/qwc2-demo-app/

yarn run themesconfig

cp /app/qwc2-demo-app/themes.json /idata_project_dir

exec "$@"
