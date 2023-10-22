"""
Utility functions around OGR library
"""
import os
import urllib
from importlib.resources import files

from jinja2 import Template
from osgeo import ogr

from . import data_structures
from . import io_utils

default_template = "templates/vrt.j2"
vsimappings = {
    ".zip": "/vsizip/",
    ".tgz": "/vsitar/",
    ".tar.gz": "/vsitar/",
    ".rar": "/vsirar/",
    ".7z": "/vsi7z/",
}


def collect_layers(filename: str, db_friendly: bool = True):
    layers: list[ogr.Layer] = []

    inDataSource = ogr.Open(filename)
    for layer_idx in range(inDataSource.GetLayerCount()):
        layer = inDataSource.GetLayerByIndex(layer_idx)
        layers.append(
            data_structures.DataLayer(ogr_layer=layer, db_friendly=db_friendly)
        )
    return layers


def layers2vrt(
    layers_list: list, source_file: str, vrt_template: str
):
    template = None
    try:
        if vrt_template:
            print(f"Using template {vrt_template}")
            with open(vrt_template) as tplfile:
                template = Template(tplfile.read())
        else:
            print(f"Using default template")
            tplcontent = (
                files("ogr2vrt_simple")
                .joinpath(default_template)
                .read_text(encoding="utf-8")
            )
            template = Template(tplcontent)

        vrt_xml = template.render(
            layers=layers_list, source_file=os.path.basename(source_file)
        )
        return vrt_xml
    except Exception as e:
        print("An exception occurred:", e)


def vsiprefix_from_archive_extension(ext: str):
    """
    Map archive extension with vsizip, vsitar etc
    :param ext:
    :return:
    """
    if ext in vsimappings.keys():
        return vsimappings[ext]
    else:
        return None


def get_vsi_curl_prefix(url, headers):
    if io_utils.is_streaming(url, headers):
        return "/vsicurl_streaming/"
    else:
        return "/vsicurl/"


def build_source_paths(url: str, vrt_config: dict = io_utils.default_download_config):
    """
    Take a file path or http(s) URL and produce an optimized vsi source string to use with
    ogrinfo, ogr2ogr, ogr2vrt etc.
    Depending on the situation, you might need to declare a few things in the vrt_config object. Look at
    io_utils.default_download_config to see what's possible to configure
    :param url: http(s) url or file path
    :param vrt_config:
    :return:
    """
    file_path = None
    ext = None
    is_archive = None
    data_format = vrt_config.get("data_format", None)

    if url.startswith("http"):  # It's an online resource
        h = io_utils.get_headers(url)
        ext = io_utils.get_extension_from_headers(url, h)
        is_archive = io_utils.is_archive(ext)
        if is_archive:
            # We have to download the file anyway to figure out the path in the archive
            file_path, ext, is_archive = io_utils.download_source(url, vrt_config)
            paths_inside = io_utils.find_paths_in_archive(file_path, ext, data_format)
            source_paths = []
            for p in paths_inside:
                source_paths.extend(
                    [
                        {
                            "path": vsiprefix_from_archive_extension(ext)
                            + file_path
                            + "/"
                            + p,
                            "confidence": 1,
                            "kind": "local",
                        },
                        {
                            "path": vsiprefix_from_archive_extension(ext)
                            + "/vsicurle/"
                            + url
                            + "/"
                            + p,
                            "confidence": 0.8,
                            "kind": "remote",
                        },
                    ]
                )
                return source_paths
        else:  # online resource but not an archive
            url_params = urllib.parse.urlparse(url).query.split("&")

            # If CSV and no more than 1 url param
            if len(url_params) <= 1 and (ext == ".csv" or data_format == ".csv"):
                paths = [
                    {
                        "path": f"CSV:{get_vsi_curl_prefix(url, h)}{url}",
                        "confidence": 0.8,
                        "kind": "remote",
                    }
                ]
                if vrt_config.get("filename", ""):
                    paths.append(
                        {
                            "path": f"CSV:{vrt_config['filename']}",
                            "confidence": 1,
                            "kind": "local",
                        }
                    )
                return paths

            elif (
                len(url_params) <= 1
                and io_utils.get_extension_from_url(url)
                in io_utils.common_dataset_extensions
            ):
                # File extension is provided in the URL => it should be possible to do vsicurl
                paths = [
                    {
                        "path": f"{get_vsi_curl_prefix(url, h)}{url}",
                        "confidence": 0.7,
                    }
                ]
                if vrt_config.get("filename", ""):
                    paths.append(
                        {
                            "path": f"{vrt_config['filename']}",
                            "confidence": 1,
                            "kind": "local",
                        }
                    )
                return paths

            else:  # It will reuire a download
                # Display some informational messages in some cases

                # If more than 1 URL param, vsicurl won't work (drops the others) => download
                if len(url_params) > 1:
                    print(
                        "Too many GET parameters in the URL. viscurl seems not to consider the params \n"
                        "following the first one. You will not be able to use vsicurl for this data source"
                    )
                if io_utils.get_extension_from_url(url) != ext:
                    print(
                        "The file extension is not part of the URL. Ogr won't be able to recognize the file type. \n"
                        "You will not be able to use vsicurl for this data source"
                    )

                file_path, ext, is_archive = io_utils.download_source(url, vrt_config)
                return [
                    {
                        "path": file_path,
                        "confidence": 1,
                        "kind": "local",
                    }
                ]

    else:  # It's a local(file) resource
        if vrt_config.get("relative_to_file", False):
            file_path = url
        else:
            file_path = os.path.abspath(url)
        ext = os.path.splitext(file_path)[1]
        is_archive = io_utils.is_archive(ext)

        vsistring = ""
        if data_format == ".csv":
            vsistring = "CSV:"

        if is_archive:
            # Figure out the path to the file _inside_ the archive
            paths = io_utils.find_paths_in_archive(
                file_path, ext, vrt_config.get("data_format", None)
            )
            # print(paths)
            if len(paths) > 0:
                vsistring = (
                    vsiprefix_from_archive_extension(ext) + file_path + "/" + paths[0]
                )
            else:
                return []
        else:
            vsistring = file_path
        return [
            {
                "path": vsistring,
                "confidence": 1,
                "kind": "local",
            }
        ]


def build_vrt(
    source_paths: str, vrt_template: str, prefer_remote=True,
):
    """
    Take a list of possible source-paths. Source-paths are strings that define how to access to the
    dataset, with the terminology used by OGR (https://gdal.org/user/virtual_file_systems.html#introduction)
    Source-paths should be supported by any OGR tools, like ogrinfo, ogr2ogr, ogr2vrt
    Online paths, using vsicurl-like syntax, might not work in some tricky cases. this is why we expect in
    those cases to have a fallback source_path referring to a local file (we download the resource)
    :param source_paths:
    :return:
    """
    sources = []
    vrt_xml: str = None
    if prefer_remote:
        sources = [p for p in source_paths if p["kind"] == "remote"]
        if len(sources) > 0:  # There is at least one remote source
            source = None
            if len(sources) > 1:
                print(
                    "There are several possible datasets. You might want to be more specific. "
                    "Trying to guess the right one"
                )
                # TODO: make a better guess
                source = sources[0]
            elif len(sources) == 1:
                source = sources[0]
            try:
                layers = collect_layers(source["path"], db_friendly=True)
                vrt_xml = layers2vrt(
                    layers, source_file=source["path"], vrt_template=vrt_template
                )
            except Exception as e:
                print("An exception occurred:", e)
            if vrt_xml:
                return vrt_xml

        else:
            # do nothing, we'll switch to local source
            print(
                "No remote source could be found. We will be using a local resource instead"
            )

    # If prefer_remote == False or we didn't get any positive outcome, we'll use local sources

    sources = [p for p in source_paths if p["kind"] == "local"]
    source = None
    if len(sources) > 1:
        print(
            "There are several possible datasets. You might want to be more specific. "
            "Trying to guess the right one"
        )
        # TODO: make a better guess
        source = sources[0]
    elif len(sources) == 1:
        source = sources[0]
    try:
        layers = collect_layers(source["path"], db_friendly=True)
        vrt_xml = layers2vrt(
            layers, source_file=source["path"], vrt_template=vrt_template
        )
    except Exception as e:
        print("An exception occurred:", e)
    if vrt_xml:
        return vrt_xml
