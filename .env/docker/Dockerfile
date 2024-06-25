ARG QGIS_TEST_VERSION=latest
FROM  qgis/qgis:${QGIS_TEST_VERSION}
MAINTAINER Benjamin Jakimow <benjamin.jakimow@geo.hu-berlin.de>

LABEL Description="Docker container with QGIS + EnMAP-Box" Vendor="enmap.org"

RUN apt update
RUN apt -y install python3-pip python3-venv pyqt5-dev-tools python3-matplotlib \
    python3-h5py python3-pyqt5.qtopengl python3-netcdf4

#    && rm -rf /var/lib/apt/lists/*

RUN apt update
# COPY ./linux/requirements_ubuntu.txt /tmp/
COPY ./.env/linux/requirements_ubuntu.txt /tmp/
COPY ./requirements_developer.txt /tmp/

RUN mkdir .virtualenvs
RUN mkdir .virtualenvs/enmapbox
RUN python3 -m venv --upgrade-deps --system-site-packages .virtualenvs/enmapbox
RUN . .virtualenvs/enmapbox/bin/activate

RUN virtualenv venv

RUN pip3 install typeguard==2.13.3  # version 3.x created several problems
# RUN pip3 install astropy # required for convolution
RUN pip3 install PyOpenGL # required by ImageCube app
RUN pip3 install xgboost # required by XGBoost classifier/regressor, see #960
RUN pip3 install lightgbm # required by LightGBM classifier/regressor, see #960
RUN pip3 install catboost # required by CatBoost classifier/regressor, see #960
RUN pip3 install docutils

# required by parts of EnMAP-Box Applications
RUN pip3 install sympy # required by EnSoMAP
RUN pip3 install numba>=0.57 # required by EnSoMAP
RUN pip3 install enpt-enmapboxapp # required by EnPT
RUN pip3 install scikit-learn>=1.0
RUN pip3 install coverage-badge



RUN echo "Basic python environment:"
RUN python3 --version
RUN pip3 list


# Avoid sqlcmd termination due to locale -- see https://github.com/Microsoft/mssql-docker/issues/163
RUN echo "nb_NO.UTF-8 UTF-8" > /etc/locale.gen
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
RUN locale-gen
ENV PATH="/usr/local/bin:${PATH}"

ENV LANG=C.UTF-8

WORKDIR /
