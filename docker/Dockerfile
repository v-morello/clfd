FROM ubuntu:22.04

ARG PSRCHIVE_VERSION=2024-12-02

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
        python-is-python3

# Ubuntu 22.04 ships with pip 22.0.2 which does not work with the modern pyproject.toml format
# Also, PSRCHIVE won't build with numpy 2 yet
RUN pip install --upgrade pip && \
    pip install "numpy<2.0.0" "swig>3"

# Build PSRCHIVE with Python bindings
RUN git clone --branch ${PSRCHIVE_VERSION} --depth=1 git://git.code.sf.net/p/psrchive/code psrchive && \
    cd psrchive && \
    ./bootstrap && \
    ./configure --enable-shared --enable-static F77=gfortran && \
    make -j8 && \
    make install

ENV LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH}
ENV PYTHONPATH=/usr/local/lib/python3.10/site-packages:${PYTHONPATH}

# Check build is successful
RUN python -c "import psrchive"
