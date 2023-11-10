# ogr2vrt *simple*
**Generate a simple VRT file from an OGR-compatible dataset**

## Python package
This is mostly a python package, destined to be used by other applications. By itself, it is quite limited. However, we provide a small CLI tool that acts as a commandline VRT generator.

## Command line interface
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

## Use the CLI
Once installed, you will have the `ogr2vrt_cli` command available. For now, it is limited to only one sub-command, `generate-vrt`:
```
# Get help
ogr2vrt_cli generate-vrt --help

# Extract VRT from a remote resource
ogr2vrt_cli generate-vrt https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/shp/poly.zip

# Works also on a API remote source:
ogr2vrt_cli generate-vrt -d 'https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1/datafiles/37dd7056-6c4d-44e0-a720-32d4064f9a26/csv?millesime=2023-05&withColumnName=true&withColumnDescription=true&withColumnUnit=true&orderBy=-COMMUNE_CODE&columns=COMMUNE_CODE,COMMUNE_LIBELLE,CLASSE_VEHICULE,CATEGORIE_VEHICULE,CARBURANT,CRITAIR,PARC_2011,PARC_2012,PARC_2013,PARC_2014,PARC_2015,PARC_2016,PARC_2017,PARC_2018,PARC_2019,PARC_2020,PARC_2021,PARC_2022&COMMUNE_CODE=contains%3A09241'
```

_**Note**: as in the example above, if you are tapping into a remote URL that has special characters in it (e.g. parenthesis), you will have to surround the URL with quotes or escape the characters (this is a shell issue, not a python issue, but an issue that needs to be taken care of anyway)_

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