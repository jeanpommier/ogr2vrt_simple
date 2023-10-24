"""
Utility functions around OGR library
"""
import importlib
import logging
from importlib.resources import files

from jinja2 import Template
from osgeo import ogr

from . import data_structures

default_template = "templates/vrt.j2"
vsimappings = {
    ".zip": "/vsizip/",
    ".tgz": "/vsitar/",
    ".tar.gz": "/vsitar/",
    ".rar": "/vsirar/",
    ".7z": "/vsi7z/",
}


def is_valid_ogr_path(vsistring: str) -> bool:
    """
    Tries to open the dataset addresses by the vsistring
    :param vsistring:
    :return:
    """
    in_data_source = ogr.Open(vsistring)
    return in_data_source is not None


def collect_layers(filename: str, db_friendly: bool = True):
    layers: list[data_structures.DataLayer] = []

    in_data_source = ogr.Open(filename)
    for layer_idx in range(in_data_source.GetLayerCount()):
        layer = in_data_source.GetLayerByIndex(layer_idx)
        layers.append(
            data_structures.DataLayer(ogr_layer=layer, db_friendly=db_friendly)
        )
    if len(layers) > 0:
        return layers
    else:
        return None


def layers2vrt(
        layers_collection: list[dict], vrt_template: str = None
):
    try:
        if vrt_template:
            logging.debug(f"Using template {vrt_template}")
            with open(vrt_template) as tplfile:
                template = Template(tplfile.read())
        else:
            logging.debug(f"Using default template")
            tplcontent = (
                importlib.resources.files("ogr2vrt_simple")
                .joinpath(default_template)
                .read_text(encoding="utf-8")
            )
            template = Template(tplcontent)

        vrt_xml = template.render(layers_collection=layers_collection)
        return vrt_xml
    except Exception as e:
        logging.debug("An exception occurred:", e)


def vsiprefix_from_archive_extension(ext: str):
    """
    Map archive extension with vsizip, vsitar etc.
    :param ext:
    :return:
    """
    if ext in vsimappings.keys():
        return vsimappings[ext]
    else:
        return None
