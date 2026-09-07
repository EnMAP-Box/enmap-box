ARG QGIS_VERSION=stable
FROM --platform=linux/amd64 qgis/qgis:${QGIS_VERSION}
LABEL maintainer="Benjamin Jakimow <benjamin.jakimow@geo.hu-berlin.de>"
LABEL description="container to test qgispluginsupport"
SHELL ["/bin/bash", "-c"]

RUN apt update && apt install -y \
    python3-flake8 \
    python3-pytest-xdist \
    python3-pytest-cov \
    python3-pyqtgraph \
    python3-scipy \
    python3-matplotlib \
    python3-defusedxml \
    python3-colorama \
    python3-numpy \
    python3-pandas \
    python3-sympy \
    pyqt6-dev-tools \
    qt6-base-dev \
    qt6-base-dev-tools \
    libxcb-cursor0 \
    python3-netcdf4 \
    python3-opengl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages --no-cache-dir \
    enpt \
    enpt-enmapboxapp \
    enfrosp-enmapboxapp \
    pyvista \
    pyvistaqt \
    astropy \
    numba \
    skops \
    scikit-learn \
    lightgbm \
    xgboost \
    tensorboard

# COPY ./.docker/qgis_setup.sh /tmp/
COPY . /usr/src/

ENV PYTHONPATH=\
/usr/share/qgis/python/:\
/usr/share/qgis/python/plugins:\
/usr/lib/python3/dist-packages/qgis:\
$PYTHONPATH

ENV PATH=/usr/lib/qt6/bin:/usr/lib/qt6/libexec:$PATH

RUN cd /usr/src
RUN ls -l /usr/src
RUN ls -la /usr/lib/qt6/bin

WORKDIR /