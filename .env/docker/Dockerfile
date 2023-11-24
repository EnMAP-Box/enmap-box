ARG QGIS_TEST_VERSION=latest
FROM  qgis/qgis:${QGIS_TEST_VERSION}
MAINTAINER Benjamin Jakimow <benjamin.jakimow@geo.hu-berlin.de>

LABEL Description="Docker container with QGIS + EnMAP-Box" Vendor="enmap.org"

RUN apt-get update && \
    apt-get -y install python3-pip wget unzip \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update


RUN echo "Basic python environment:"
RUN python3 --version
RUN pip3 list

RUN echo "Install missing EnMAP-Box requirements:"
COPY ./requirements_docker.txt /tmp/
COPY ./requirements_developer.txt /tmp/
RUN pip3 install -r /tmp/requirements_docker.txt
RUN pip3 install -r /tmp/requirements_developer.txt

# Avoid sqlcmd termination due to locale -- see https://github.com/Microsoft/mssql-docker/issues/163
RUN echo "nb_NO.UTF-8 UTF-8" > /etc/locale.gen
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
RUN locale-gen
ENV PATH="/usr/local/bin:${PATH}"

ENV LANG=C.UTF-8

WORKDIR /
