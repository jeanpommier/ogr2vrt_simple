# ogr2vrt *simple*
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

By default, the VRT file will be generated alongside the source file, extension .vrt

## Features
- Support file as datasource
- Support plain URL as datasource:
  - E.g. https://www.data.gouv.fr/fr/datasets/r/c53cd4d4-4623-4772-9b8c-bc72a9cdf4c2
  - Autodetects the file format if provided in the headers
  - Supports streaming service (e.g. https://www.data.gouv.fr/fr/datasets/r/d22ba593-90a4-4725-977c-095d1f654d28)
  - find path to dataset inside an archive e.g. https://open-data.s3.fr-par.scw.cloud/bdnb_millesime_2022-10-d/millesime_2022-10-d_dep59/open_data_millesime_2022-10-d_dep59_gpkg.zip)
  - determine if needs to download the file as a first step or can use vsicurl functions

**_Does not support (yet)_**:
- non-UTF-8 csv files

---

## Install
- _**You will need the GDAL/OGR library**_. It is not listed in the requirements.txt file, because the installation depends on having the proper libraries already installed on your computer.

  The simplest way:
  - install gdal, libgdal-dev, python3-dev packages on your computer
  - install [GDAL package](https://pypi.org/project/GDAL/) using 
  ```
  pip install GDAL==$(gdal-config --version)
  ```

- Create a virtual env and install the app
```
python3 -m venv .venv
source .venv/bin/activate
pip install ogr2vrt-simple
```

---
## Develop
  
### Compatibility
**python >=3.9**

It probably works with any python 3 but was tested mostly under python 3.9 and above

### Using poetry
This is now the recommended way

- Install [poetry](https://python-poetry.org/docs/#installation)
- Install the dependencies: `poetry install`
- Run the script:
```
# Install the dependencies: 
poetry install
#activate the environment
poetry shell 
# You have to install the GDAL library using pip, it doesn't seem to work with poetry directly
pip install GDAL==$(gdal-config --version)

cd ogr2vrt_simple/
python3 cli.py generate-vrt --help
```


### Simply using pip
_This should still work._ 

Create a virtual env and install the requirements
```
python3 -m venv .venv
source .venv/bin/activate
pip install GDAL==$(gdal-config --version)
pip install -r requirements.txt
```

_**You will need the GDAL/OGR library**_. See above in the [install](#install) section
      
### Run it
```bash
cd ogr2vrt_simple/
# Generate VRT file for a local file (zipped shapefile)
python3 cli.py generate-vrt  https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/shp/poly.zip

# Generate VRT file for a remote CSV resource
python3 cli.py generate-vrt  --with_vsicurl https://www.data.gouv.fr/fr/datasets/r/c53cd4d4-4623-4772-9b8c-bc72a9cdf4c2
```

List options: 
```bash
python3 cli.py generate-vrt  --help
````

### Build

Use Poetry to build this script:
```
# Build
poetry build

# install 
poetry install

# test it
ogr2vrt_cli --help

# Publish it to test-pypi
poetry publish -r test-pypi
# ... or to pypi
poetry publish
```