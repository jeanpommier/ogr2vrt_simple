FROM ghcr.io/osgeo/gdal:alpine-normal-3.12.2

RUN apk add py3-pip \
  && pip install ogr2vrt_simple --no-cache-dir --break-system-packages

CMD ["ogr2vrt_cli", "--help"]