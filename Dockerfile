FROM python:3.11.8-alpine3.18
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Add add dependencies 
RUN apk add build-base \
    libffi-dev \
    python3-dev \
    py3-setuptools \
    tiff-dev \
    jpeg-dev \
    openjpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    libwebp-dev \
    tcl-dev \
    tk-dev \
    harfbuzz-dev \
    fribidi-dev \
    libimagequant-dev \
    libxcb-dev \
    libpng-dev \
    postgresql-dev \
    gdal-dev \
    gdal \
    geos-dev \
    geos \
    busybox-openrc

RUN export LD_LIBRARY_PATH=/usr/local/lib
RUN mkdir /run/openrc
RUN touch /run/openrc/softlevel
# Application specific   
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/

RUN apk add curl

RUN chmod +x entrypoint.sh

ENTRYPOINT ["/code/entrypoint.sh"]