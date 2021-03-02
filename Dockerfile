FROM debian:latest

# Install miniconda 3
RUN apt-get -qq update && apt-get -qq -y install curl bzip2 \
    && curl -sSL https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -bfp /usr/local \
    && rm -rf /tmp/miniconda.sh \
    && conda install -y python=3 \
    && conda update conda \
    && apt-get -qq -y remove curl bzip2 \
    && apt-get -qq -y autoremove \
    && apt-get autoclean \
    && rm -rf /var/lib/apt/lists/* /var/log/dpkg.log \
    && conda clean --all --yes

ENV PATH /opt/conda/bin:$PATH


# RUN apt-get -qq update && apt-get -y install libgdal-dev
RUN apt-get -qq update && apt-get -y install build-essential libgdal-dev


# === MB-System ===
ARG GMT_SOURCE_TAG
ARG PROJ_SOURCE_TAG
ARG DEBIAN_FRONTEND=noninteractive


# Install all dependencies except for proj and gmt from default repos
RUN apt-get update && \
    apt-get install -y locales && \
    locale-gen en_US.UTF-8

RUN apt-get install -y \
        build-essential \
	    clang \
	    git \
	    cmake \
	    libfftw3-dev \
	    netcdf-bin \
	    libnetcdf-dev \
	    python3 \
	    libmotif-dev \
	    libglu1-mesa-dev \
	    mesa-common-dev



# Install MB-System Dependencies
RUN apt-get update -qq && apt-get -y install \
    gmt libgmt5 libgmt-dev gmt-gshhg gmt-common \
    libx11-dev xorg-dev libmotif-dev libmotif-common \
    libglu1-mesa libglu1-mesa-dev mesa-common-dev \
    build-essential gfortran \
    libfftw3-3 libfftw3-dev libproj-dev gdal-bin libgdal-dev 

# conflicting libtiff installs causes an error, so uninstall this one
# RUN conda uninstall libtiff


COPY ./MB-System-5.7.5.tar.gz MB-System-5.7.5.tar.gz
RUN tar xvzf MB-System-5.7.5.tar.gz && cd MB-System-5.7.5 \
    && ./configure --with-gdal-config=/usr/bin \
    && make && make install

# Re-build the dynamic links
RUN ldconfig -v


# Install Laszip
RUN apt-get -y install ninja-build git cmake vim wget zip

RUN git clone https://github.com/LASzip/LASzip.git \
    && cd LASzip \
    && git checkout 3.1.0 \
    && cmake . -DCMAKE_INSTALL_PREFIX=/usr && make && make install


# Install PDAL
RUN git clone https://github.com/PDAL/PDAL.git \
    && cd PDAL \
    && mkdir build && cd build \
    && cmake -DWITH_LASZIP=ON -DBUILD_PLUGIN_MBIO=ON -G Ninja .. \
    && ninja


# Install PDAL Python Extension
RUN cd /PDAL/build/ && ninja install \
    && git clone https://github.com/PDAL/python pdalextension \
    && cd pdalextension \
    && pip3 install . \
    && pip3 install numpy


RUN conda install -c conda-forge jupyterlab -y
RUN conda install -c conda-forge gdal -y

ADD /api/data /usr/api/data
ADD /api/output_images /usr/api/output_images
ADD /api/process.py /usr/api/
ADD /api/server.py /usr/api/
ADD /api/requirements.txt /usr/api/

RUN cd /usr/api && pip install -r requirements.txt


ENV GDAL_DATA=/usr/share/gdal
# ENV PDAL_DRIVER_PATH=/usr/lib
# ENV PROJ_LIB=/usr/share/proj

ENTRYPOINT cd /usr/api && python server.py
