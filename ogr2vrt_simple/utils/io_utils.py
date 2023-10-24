"""
Utility functions for I/O operations
"""
import logging
import mimetypes
import os
import tarfile
import urllib
import zipfile
from abc import ABC, abstractmethod
from urllib.parse import urlparse
from urllib.request import urlretrieve
from uuid import uuid4

import humanize

compression_extension_list = [".zip", ".tgz", ".tar.gz", ".gz", ".rar", ".7z"]
archive_extension_list = [".zip", ".tgz", ".tar.gz", ".rar", ".7z"]
common_dataset_extensions = [
    ".csv",
    ".xlsx",
    ".xls",
    ".ods",
    ".shp",
    ".gpkg",
    ".geojson",
]

default_download_config = {
    "with_vsicurl": False,
    "data_format": "",
    "filename": "",
    "relative_to_file": True,
}


def download_dataset(url: str, filename: str = None, extension: str = None) -> str:
    """
    Download the data, save it as temporary file.
    :param url:
    :return: tuple[file path:str , extension: str, is an archive: bool]
    """
    if not filename:
        filename = f"{uuid4()}"

    # Download the dataset
    file_path, http_headers = urlretrieve(url, filename)

    # Set file extension if needed
    if not os.path.splitext(file_path)[1]:
        os.rename(file_path, file_path + extension)
        file_path = file_path + extension
    return file_path
