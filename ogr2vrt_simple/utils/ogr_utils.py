"""
Utility functions around OGR library
"""
import logging
import os
from dataclasses import dataclass, field

try:
    # Python < 3.9
    import importlib_resources as ilr
except ImportError:
    import importlib.resources as ilr

from jinja2 import Template
from osgeo import ogr
from typing import List, Dict, Optional

from . import data_structures

default_template = "templates/vrt.j2"
vsimappings = {
    ".zip": "/vsizip/",
    ".tgz": "/vsitar/",
    ".tar.gz": "/vsitar/",
    ".rar": "/vsirar/",
    ".7z": "/vsi7z/",
}


@dataclass
class OgrSourcePath:
    """
    A path to an OGR layer is more complicated than a simple os.path or URL. It can chain several vsi* prefixes, os.path
    and, in the case of an archive or a multiple-layers files like geopackage, an internal path to the layer.
    """
    path_or_url: str
    prefix: List[str] = field(default_factory=list)
    archive_internal_paths: List[str] = field(default_factory=lambda: [""])


def is_valid_ogr_path(vsistring: str) -> bool:
    """
    Tries to open the dataset addresses by the vsistring
    :param vsistring:
    :return:
    """
    in_data_source = ogr.Open(vsistring)
    return in_data_source is not None


def collect_layers(ogr_source: OgrSourcePath, db_friendly: bool = True, relative_to: str | os.PathLike = None) -> List[dict]:
    """
    Opens each available OGR layer from `ogr_source` path and collects its structure information
    :param ogr_source:
    :param db_friendly:
    :param relative_to: if provided, relative paths will be made relative to this path. Should only be used on
    file-based paths
    :return: list of DataLayer objects
    """
    layers_collection = []
    for p in ogr_source.archive_internal_paths:
        try:
            full_path = "".join(ogr_source.prefix) + ogr_source.path_or_url + p
            layers = collect_layers_for_file(full_path, db_friendly)
            if relative_to:
                s = os.path.relpath(full_path, os.path.dirname(relative_to))
            else:
                s = ogr_source.path_or_url
            if layers:
                layers_collection.append({
                    "source_path": "".join(ogr_source.prefix) + s + p,
                    "layers": layers
                })
        except Exception as e:
            # This is probably expected since we might encounter some false-positive files
            # when processing all eligible files
            logging.debug(f"Error trying to collect layers for path {OgrSourcePath}: {e}")
    return layers_collection


def collect_layers_for_file(filename: str, db_friendly: bool = True) -> List[data_structures.DataLayer]:
    """
    Opens each available OGR layer from `filename` file and collects its structure information
    :param filename: full path to an OGR supported file (can be inside an archive)
    :param db_friendly:
    :param relative_to: if provided, relative paths will be made relative to this path
    :return: list of DataLayer objects
    """
    layers: list[data_structures.DataLayer] = []

    in_data_source = ogr.Open(filename)
    for layer_idx in range(in_data_source.GetLayerCount()):
        layer = in_data_source.GetLayerByIndex(layer_idx)
        layers.append(
            data_structures.DataLayer(ogr_layer=layer, db_friendly=db_friendly)
        )
    return layers


def layers2vrt(
        layers_collection: List[Dict], vrt_template: str = None
):
    try:
        if vrt_template:
            logging.debug(f"Using template {vrt_template}")
            with open(vrt_template) as tplfile:
                template = Template(tplfile.read())
        else:
            logging.debug(f"Using default template")
            tplcontent = (
                ilr.files("ogr2vrt_simple")
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
