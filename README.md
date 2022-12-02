# vrt-kickoff
**Generate a simple VRT file from an OGR-compatible dataset**

It mostly targets and was tested with spreadsheet data (xls, xslx, ods, csv) but actually should work with many other data sources supported by the OGR drivers

---
## Install

Create a virtual env and install the requirements

        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt

You will need the gdal library. You will probably have to adjust the version in the requirements.txt file
The simplest way:
- install gdal and libgdal1-dev packages on your computer
- install pygdal using
     
        pip install pygdal=="`gdal-config --version`.*"
        
### Compatibility
This code has been tested under python 3.9. It will probably work with an older version of python3, but with no garanties.
