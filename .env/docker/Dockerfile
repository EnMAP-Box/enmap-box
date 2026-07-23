ARG QGIS_TEST_VERSION=latest
FROM  qgis/qgis:${QGIS_TEST_VERSION}

SHELL ["/bin/bash", "-c"]

LABEL org.opencontainers.image.authors="benjamin.jakimow@geo.hu-berlin.de"

LABEL Description="Docker container with QGIS + EnMAP-Box" Vendor="enmap.org"

ENV VIRTUAL_ENV=/opt/virtualenvs/enmapbox

RUN apt update \
    &&  apt install -y \
         pyqt5-dev-tools \
     	 python3-pip \
     	 python3-venv \
     	 python3-h5py \
      	 python3-pyqt5.qtopengl \
      	 python3-netcdf4 \
       	 python3-astropy \
    && apt autoremove -y \
    && apt clean

COPY ./.env/linux/requirements_ubuntu.txt /tmp/
COPY ./requirements_developer.txt /tmp/



RUN python3 -m venv --system-site-packages $VIRTUAL_ENV \
     && source $VIRTUAL_ENV/bin/activate \
     && python3 -m pip install --upgrade pip \
     && python3 -m pip install --no-cache-dir -r tmp/requirements_ubuntu.txt \
     && python3 -m pip install --no-cache-dir -r tmp/requirements_developer.txt


# RUN python3 -m venv --upgrade-deps --system-site-packages venv/enmapbox
# ENV PATH="/venv/enmapbox/bin:/usr/local/bin:${PATH}"

# RUN echo "Basic python environment:"
# RUN python3 --version
# RUN pip list

ENV PYTHONPATH="${PYTHONPATH}:/usr/share/qgis/python/plugins"

# Avoid sqlcmd termination due to locale -- see https://github.com/Microsoft/mssql-docker/issues/163
# RUN echo "nb_NO.UTF-8 UTF-8" > /etc/locale.gen
# RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
# RUN locale-gen
# ENV PATH="/venv/enmapbox/bin:/usr/local/bin:${PATH}"

# ENV LANG=C.UTF-8

WORKDIR /

# Set the entrypoint
ENTRYPOINT ["/bin/bash", "-c", "source ${VIRTUAL_ENV}/bin/activate && exec \"$@\"", "--"]


