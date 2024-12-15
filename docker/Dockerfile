FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        git \
        autoconf \
        libtool \
        pkg-config \
        gfortran \
        fftw3-dev \
        python3 \
        python3-pip \
        python3-dev \
        python-is-python3 \
        libcfitsio-dev

# Ubuntu 22.04 ships with pip 22.0.2 which does not work with modern pyproject.toml format
RUN pip install --upgrade pip

# PSRCHIVE won't build with numpy 2 yet
RUN pip install "numpy<2.0.0" swig

# Build PSRCHIVE with Python bindings
RUN git clone git://git.code.sf.net/p/psrchive/code psrchive
RUN cd psrchive && ./bootstrap && ./configure --enable-shared --enable-static F77=gfortran
RUN cd psrchive && make -j8 && make install
ENV LD_LIBRARY_PATH=/usr/local/lib
ENV PYTHONPATH=/usr/local/lib/python3.10/site-packages

# Install clfd
RUN git clone https://github.com/v-morello/clfd.git
RUN cd clfd && pip install -e .[dev]
