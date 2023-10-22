"""
Utility functions for I/O operations
"""
import mimetypes
import os
import tarfile
import urllib
import zipfile
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


def download_source(url: str, vrt_config: dict = None):
    """
    Download the data, save it as temporary file.
    The tricky part is that with an URL, we don't necessary know the file extension,
    if it is compressed data or what.
    :param vrt_config:
    :param url:
    :return:
    """
    if vrt_config is None:
        vrt_config = default_download_config

    if "filename" not in vrt_config or not vrt_config["filename"]:
        vrt_config["filename"] = f"{uuid4()}"
    # Download the dataset
    file_path, http_headers = urlretrieve(url, vrt_config["filename"])

    # Add the dot to the extension if necessary
    if vrt_config["data_format"] and not vrt_config["data_format"].startswith("."):
        vrt_config["data_format"] = "." + vrt_config["data_format"]

    # Set file extension if needed
    ext = os.path.splitext(file_path)[1]
    if not ext:
        ext = get_extension_from_headers(url, http_headers)
        ext2 = get_extension_from_url(url)
        print(
            f"Detected extensions: {ext} (headers), {ext2} (URL). "
            f"Declared extension: {vrt_config['data_format']}"
        )
        if not is_archive(ext) and vrt_config["data_format"]:
            ext = vrt_config["data_format"]
        os.rename(file_path, file_path + ext)
        file_path = file_path + ext
    return file_path, ext, is_archive(ext)


def find_paths_in_archive(file_path: str, compression: str, data_format: str):
    file_extensions = (
        data_format.split(",") if data_format else common_dataset_extensions
    )
    match compression:
        case ".zip":
            with zipfile.ZipFile(file_path, "r") as zip_file:
                file_list = zip_file.namelist()
                # print("The file list is:",file_list)
                return [
                    f for f in file_list if os.path.splitext(f)[1] in file_extensions
                ]
        case ".tar.gz" | ".tgz":
            with tarfile.open(file_path, "r") as tar:
                file_list = tar.getmembers()
                # print("The file list is:", file_list)
                return [
                    f.name
                    for f in file_list
                    if os.path.splitext(f.name)[1] in file_extensions
                ]
        case other:
            print(f"Compression format not supported yet {compression}")
        # TODO: add support for other compression formats


def analyze_source(url: str):
    """
    Get the source URL and extract as much information as possible about it: format, is it
    an archive or not, if yes where is the dataset in the archive, can it be vsicurled, etc
    :param url:
    :return:
    """
    if url.startswith("http"):
        # look into the headers
        import urllib

        req = urllib.request.Request(url, method="HEAD")
        f = urllib.request.urlopen(req)
        print(f.headers["Content-type"])


def get_headers(url: str):
    """
    Run a HEAD request to get the headers without downloading the data itself
    :param url:
    :return:
    """
    req = urllib.request.Request(url, method="HEAD")
    head = urllib.request.urlopen(req)
    return head.headers


def get_extension_from_headers(url: str, headers=None):
    """
    Try to figure out the file extension (file type) by reading the http headers and parsing the
    declared mime type
    If headers are provided, it will not have to make a request to get them
    :param url:
    :return:
    """
    if not headers:
        headers = get_headers(url)
    ct = headers["Content-type"]
    # print(f"header: {ct}, extension: {extension_from_header(ct)}")

    # Enrich the mimetype DB with some non-standard types
    mimetypes.add_type("application/csv", ".csv", strict=False)

    extension = mimetypes.guess_extension(ct.split(";")[0], strict=False)
    return extension


def get_extension_from_url(url: str):
    path = urllib.parse.urlparse(url).path
    return os.path.splitext(path)[1]


def is_archive(extension: str):
    """
    Check a file extension and determine if it is an archive.
    Add the dot if necessary
    :param extension:
    :return:
    """
    if not extension.startswith("."):
        extension = "." + extension
    return extension in archive_extension_list


def is_streaming(url: str, headers=None):
    """
    In case we want to vsicurl the data, we need to figure out whether it is streaming or
    not (use viscurl or vsicurl_streaming)
    If headers are provided, it will not have to make a request to get them
    :param url:
    :return:
    """
    if not headers:
        headers = get_headers(url)
    ct = headers["Transfer-Encoding"]
    # print(ct)
    if ct == "chunked":
        return True
    else:
        return False


def get_data_full_size(url: str, headers=None):
    """
    Using HEAD request, we can retrieve the full size of the dataset.
    Can be useful in some cases, and good to display in information regarding the dataset
    If headers are provided, it will not have to make a request to get them
    :param url:
    :return:
    """
    if not headers:
        headers = get_headers(url)
    # If it's a streaming service, the full size is not advertised AFAIK
    if is_streaming(url, headers):
        return None

    size = headers["content-length"]
    binary_size = humanize.naturalsize(size, binary=True)
    # print(ct)
    return binary_size


def guess_source_access_url(url: str, no_vsicurl=False):
    """
    Try to figure out how to access the data: depending whether it's a file, an archive file, an URL zipped or not,
    supporting streaming or not, we're not going to access it the same way
    :param url:
    :return:
    """
    access_string = ""
    filename = ""
    download = False

    if url.startswith("http"):  # It's an online resource
        if no_vsicurl:
            # We will download it anyway
            download = True
        else:  # we will try to use /vsicurl-like syntax
            pass

    else:  # Assume for now it's a file
        # TODO: support also ftp://
        extension = os.path.splitext(url)[1]
        if is_archive(extension):
            # We need to look for the data file in there
            pass
        else:
            # simple file, easy case
            access_string = url
