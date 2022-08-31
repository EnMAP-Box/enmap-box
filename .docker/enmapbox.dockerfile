# see https://docs.docker.com/docker-cloud/builds/advanced/
# using ARG in FROM requires min v17.05.0-ce
ARG DOCKER_TAG=latest

FROM  qgis/qgis:latest
MAINTAINER Benjamin Jakimow <benjamin.jakimow@geo.hu-berlin.de>

LABEL Description="Docker container with QGIS" Vendor="QGIS.org"

# build timeout in seconds, so no timeout by default
ARG BUILD_TIMEOUT=360000

COPY ../. enmap-box

ENV QT_QPA_PLATFORM=offscreen

RUN cd enmap-box && \
    python3 -m pip install -r requirements.txt && \
    python3 scripts/setup_repository.py && \
    python3 scripts/create_plugin.py && \
    mkdir -p ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins && \
    cp -r deploy/enmapboxplugin ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins && \
    cp -r enmapboxtestdata ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/enmapboxplugin && \
    qgis_process plugins enable enmapboxplugin

RUN rm -rf enmap-box
CMD ["qgis_process"]