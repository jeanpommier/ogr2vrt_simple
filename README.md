# vrt-kickoff
**Generate a simple VRT file from an OGR-compatible dataset**

Generate a VRT file from an OGR-compatible source.
The result is to be considered as a "kickoff" VRT file, to refine according to your desires
but it will save you some time.

It mostly targets and was tested with spreadsheet data (xls, xslx, ods, csv) but actually should work with most data sources supported by the OGR drivers

Are currently detected:
- the datasource path
- for each layer (depending on the source, there might be one or more layers):
  - the layer name
  - for each field in this layer
    - name
    - type if available (defaults to string)
    - width (precision) if available

By default, the VRT file will be generated alonside the source file, extension .vrt

---
## Install

Create a virtual env and install the requirements

        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt

_**You will need the gdal library**_. It is not listed in the requirements.txt file, because the installation depends on having the proper libraries already installed on your computer.

The simplest way:
- install gdal, libgdal-dev, python3-dev packages on your computer
- install pygdal using
     
        pip install pygdal=="`gdal-config --version`.*"
        
### Compatibility
This code has been tested under python 3.9. It will probably work with an older version of python3, but with no garanties.

## Run it
```bash
python3 ogr2vrt.py path-to-your-file
```

List options: 
```bash
python3 ogr2vrt.py --help
````
