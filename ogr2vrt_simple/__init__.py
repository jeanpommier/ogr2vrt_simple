"""ogr2vrt *simple*, generate a simple VRT file from an OGR-compatible dataset"""
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "0.1.11"

from .vrt_data_sources.http_source import HttpSource
from .vrt_data_sources.file_source import FileSource
from .vrt_data_sources import archive_extension_list, compression_extension_list, \
    common_dataset_extensions
from .utils.ogr_utils import vsimappings, vsiprefix_from_archive_extension, \
    is_valid_ogr_path, collect_layers, layers2vrt
