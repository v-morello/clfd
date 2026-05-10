################################################################################
# base stage: used for CI pipelines
################################################################################
FROM ubuntu:22.04 AS base

ARG PSRCHIVE_VERSION=2024-12-02
ARG VENV_PATH=/opt/venv

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        git \
        autoconf \
        libtool \
        pkg-config \
        gfortran \
        fftw3-dev \
        libcfitsio-dev \
        python3 \
        python3-dev \
        python3-pip \
        python-is-python3 \
        python3-venv

# Create a virtual environment
RUN python -m venv ${VENV_PATH}

# Ensure venv is used for all subsequent commands
ENV PATH=${VENV_PATH}/bin:"${PATH}"

# Ubuntu 22.04 ships with pip 22.0.2 which does not work with the modern pyproject.toml format
# Upgrade setuptools to support editable installs
# PSRCHIVE won't build with numpy 2 yet
RUN pip install --upgrade pip setuptools && \
    pip install "numpy<2.0.0" "swig>3"

# Ensures configure script finds Python library path
RUN ln -s /usr/lib/python3.10/config-3.10-x86_64-linux-gnu ${VENV_PATH}/lib/python3.10/config

# Build PSRCHIVE with Python bindings
# --with-python-sys-prefix ensures it looks for Python headers and libraries in the virtual environment
RUN git clone --branch ${PSRCHIVE_VERSION} --depth=1 git://git.code.sf.net/p/psrchive/code src/psrchive && \
    cd src/psrchive && \
    ./bootstrap && \
    ./configure --enable-shared --enable-static --with-python-sys-prefix F77=gfortran && \
    make -j8 && \
    make install

ENV LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH}

# Check build is successful
RUN python -c "import psrchive"

################################################################################
# devcontainer stage: extends base with a non-root user
# non-root user avoids creating root-owned files on the host
################################################################################
FROM base AS devcontainer

ARG USERNAME=user
ARG USER_UID=1000
ARG USER_GID=${USER_UID}

# Make sure the virtual environment is owned by the non-root user
RUN groupadd --gid ${USER_GID} ${USERNAME} \
    && useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME} --shell /bin/bash \
    && chown -R ${USERNAME}:${USERNAME} ${VENV_PATH}

USER ${USERNAME}
WORKDIR /home/${USERNAME}
