"""
HTTP data source.
Defined by an URL
Expected to provide some information through its HTTP headers
But provide a limited choice for data introspection (thorough introspection will require downloading at least part of it)
"""
import logging
import mimetypes
import os
import re
import tempfile
import urllib
from uuid import uuid4

import humanize

from ogr2vrt_simple.utils import ogr_utils, io_utils
from ogr2vrt_simple.vrt_data_sources import archive_extension_list, common_dataset_extensions
from ogr2vrt_simple.vrt_data_sources.abstract_source import AbstractSource
from ogr2vrt_simple.vrt_data_sources.file_source import FileSource


class HttpSource(AbstractSource):
    url: str = ""  # can actually be URL or file path
    type: str = "http"  # one of http, ftp, file
    config: dict = {}
    http_headers = None
    file_extension: str = None

    # In some cases we can't use remote access and we will fall back on local, hence use those
    vrt_file_source: FileSource = None
    use_vrt_file_source: bool = False
    local_tmp_dir = None

    def __init__(self, url: str, config: dict = None):
        self.url = url
        self._set_type(url)
        if config:
            self.config = config
            if config.get("no_vsicurl", False):
                self.use_vrt_file_source = True

    def collect_information(self):
        # start with HTTP headers
        self.http_headers = self._get_headers()
        self.file_extension = self.get_file_extension()
        can_be, comments = self.can_be_remotely_accessed()
        return {
            "url": self.url,
            "type": self.type,
            "file_extension": self.get_file_extension(),
            "is_archive": self.is_archive(),
            "is_streaming": self.is_streaming(),
            "file_size": self.get_data_full_size(),
            "charset": self.get_charset(),
            "can_be_remotely_accessed": can_be,
            "can_be_remotely_accessed_comments": comments,

        }

    def _set_type(self, url: str):
        if url.startswith("http"):
            self.type = "http"
        elif url.startswith("ftp://"):
            self.type = "ftp"
        else:
            self.type = ""
            logging.error("Remote source URL does not seem to be valid. Are you sure this is a *remote* source ?")

    def is_remote(self):
        return True

    def _get_headers(self):
        """
        Run a HEAD request to get the headers without downloading the data itself
        :return:
        """
        if not self.http_headers:
            req = urllib.request.Request(self.url, method="HEAD")
            head = urllib.request.urlopen(req)
            self.http_headers = head.headers
        return self.http_headers

    def get_file_extension(self) -> str:
        """
        Try to figure out the file extension (file type)
        :return: file extension string
        """
        if not self.file_extension:
            ext = self._get_extension_from_headers()
            if not ext:
                ext = self._get_extension_from_url()
            self.file_extension = ext

        if not self.file_extension.startswith("."):
            self.file_extension = "." + self.file_extension

        return self.file_extension

    def _get_extension_from_content_type_header(self):
        """
        Try to figure out the file extension (file type) by reading the http content-type header and parsing the
        declared mime type
        :return:
        """
        ct = self._get_headers()["Content-type"]
        if not ct:
            return None

        # Enrich the mimetype DB with some non-standard types
        mimetypes.add_type("application/csv", ".csv", strict=False)

        extension = mimetypes.guess_extension(ct.split(";")[0], strict=False)
        return extension

    def _get_extension_from_content_disposition_header(self):
        """
        Try to figure out the file extension (file type) by reading the http content-type header and parsing the
        declared mime type
        :return:
        """
        ct = self._get_headers()["content-disposition"]
        if not ct:
            return None

        pattern = '.*filename=\".*(\.[a-zA-Z]+)\"'
        m = re.match(pattern, ct)
        if m is not None and m.lastindex > 0:
            return m[1]
        else:
            return None

    def _get_extension_from_headers(self):
        """
        Try to figure out the file extension (file type) by reading the http headers
        :return:
        """
        extension = self._get_extension_from_content_type_header()
        # raw.github for instance will present csv as plain/text, so .txt even if ending with .csv
        if extension not in common_dataset_extensions:
            e = self._get_extension_from_content_disposition_header()
            if e in common_dataset_extensions:
                extension = e
            else:
                e = self._get_extension_from_url()
                if e in common_dataset_extensions:
                    extension = e
        return extension

    def _get_extension_from_url(self):
        path = urllib.parse.urlparse(self.url).path
        return os.path.splitext(path)[1]

    def is_archive(self):
        """
        Check a file extension and determine if it is an archive.
        :return:
        """
        return self.get_file_extension() in archive_extension_list

    def get_charset(self, thorough=False):
        """
        Try to get the charset information from the headers
        :return:
        """
        if not self.http_headers:
            self._get_headers()
        try:
            ct = self.http_headers["Content-type"]
            charset = ct.split(";")[1]
            charset = charset.split("=")[1]
            return charset.lower()
        except Exception:
            if thorough:
                pass  # TODO: download the file, run a complex check on file encoding
            return None

    def is_streaming(self):
        """
        In case we want to vsicurl the data, we need to figure out whether it is streaming or
        not (use viscurl or vsicurl_streaming)
        If headers are provided, it will not have to make a request to get them
        :return:
        """
        if not self.http_headers:
            self._get_headers()
        ct = self.http_headers["Transfer-Encoding"]
        # print(ct)
        if ct == "chunked":
            return True
        else:
            return False

    def get_data_full_size(self) -> tuple[int, str]:
        """
        Using HEAD request, we can retrieve the full size of the dataset.
        Can be useful in some cases, and good to display in information regarding the dataset
        If headers are provided, it will not have to make a request to get them
        :return: tuple : (byte size, human-friendly file size (str))
        """
        if not self.http_headers:
            self._get_headers()
        # If it's a streaming service, the full size is not advertised AFAIK
        if self.is_streaming():
            return None

        size = self.http_headers["content-length"]
        if size:
            binary_size = humanize.naturalsize(size, binary=True)
            # print(ct)
            return size, binary_size
        else:
            return None

    def url_params(self):
        return urllib.parse.urlparse(self.url).query.split("&")

    def can_be_remotely_accessed(self) -> tuple[int, str]:
        """
        Determines if the dataset can be accessed using remote vsicurl syntax
        :return: tuple[level of confidence 0-10, comment]
        """
        diagnostics = []  # will contain a list of tuples[level of confidence 0-10, comment]

        if len(self.url_params()) > 1:
            diagnostics.append((0, "The URL has more than 1 url parameter, this is currently not supported "
                                   "by OGR for vsicurl-like access."))

        if self.get_file_extension() == ".csv":
            if self.get_charset() == "utf-8":
                diagnostics.append((10, "The CSV dataset seems to be utf-8 encoded"))
            else:
                diagnostics.append((5, "Unsure: OGR will only support CSV in UTF-8 encoding. Detected "
                                       f"encoding is {self.get_charset()}"))

        if self.is_archive():
            diagnostics.append((8,
                                "The file is an archive; it usually works with a remote access. However, to get the file path in the "
                                "archive, we will anyway need to download it at least one for introspection"))
        else:
            if self._get_extension_from_url():
                if self._get_extension_from_url() in common_dataset_extensions:
                    diagnostics.append((10, "The URL ends with a known and supported extension."))
                else:
                    diagnostics.append((5, "The URL exposes an nrecognized or unsupported extension, not sure "
                                           "OGR will be able to process it"))
            else:
                if self.get_file_extension() == ".csv":
                    diagnostics.append((10, "The URL does not end with an extension but for CSV data, you will " \
                                            "be able to force it by prefixing the path with CSV:."))
                else:
                    diagnostics.append((0, "The URL does not end with an extension, OGR won't be able to identify " \
                                           "the data format."))

        notes, comments = zip(*diagnostics)
        return (
            min(notes),
            "(confidence level, range 0-10)\n" + "\n".join(comments)
        )

    def get_local_file_source(self, use: bool = False) -> FileSource:
        """
        In some cases we won't be able to use a remote source. In those cases, we will link a FileSource Object
        and use it in place
        :param use : if True, will change the flag telling that we are indeed delegating most functions to the FileSource
        :return:
        """
        if not self.vrt_file_source:
            filename = self.config.get("filename", None)
            if filename:
                # Add the extension if needed
                if not os.path.splitext(filename)[1]:  # no extension
                    filename = filename + self.get_file_extension()
            else:
                if not self.local_tmp_dir:
                    self.local_tmp_dir = tempfile.mkdtemp()
                filename = os.path.join(self.local_tmp_dir, f"{uuid4()}{self.get_file_extension()}")
            file_path = io_utils.download_dataset(self.url, filename)
            self.vrt_file_source = FileSource(file_path, self.config)
        if use:
            self.use_vrt_file_source = True

        return self.vrt_file_source

    def use_local_file_source(self) -> bool:
        return self.use_vrt_file_source

    def get_source_paths(self) -> list:
        """
        Generate the OGR source path with vsi prefixes and specific logic (e.g. for archives)
        Since there might be several matches, it will always return a list of candidates
        :return:
        """
        if self.use_local_file_source():
            return self.get_local_file_source().get_source_paths()

        preprefix = "CSV:" if self.get_file_extension() == ".csv" else ""
        if self.is_archive():
            # We will have to download it for some introspection
            file_source = self.get_local_file_source()
            dataset_paths = file_source.find_paths_in_archive()
            vsistrings = []
            # Lookup diagnostics above. If not sure that it's impossible, then we try
            if self.can_be_remotely_accessed()[0] > 0:
                vsizip = ogr_utils.vsiprefix_from_archive_extension(self.get_file_extension())
                for d in dataset_paths:
                    vsicurl = self._check_remote_access_archive(vsizip, d)
                    if vsicurl:
                        vsistrings.append(vsizip + vsicurl + self.url + "/" + d)
            if len(vsistrings) > 0:
                # Then some datasets are accessible through remote protocols => it works
                return vsistrings
            else:
                # Then probably vsi remote protocols are not supported. Falling back on local files
                logging.warning("It is apparently not possible to use vsicurl syntax with this dataset. You will "
                                "have to download it first. We are giving you here a path to the file, "
                                "saved in a temporary folder")
                return self.get_local_file_source(use=True).get_source_paths()
        else:  # not an archive
            vsi = None
            # Lookup diagnostics above. If not sure that it's impossible, then we try
            if self.can_be_remotely_accessed()[0] > 0:
                vsi = self._check_remote_access()
            if vsi:
                return [preprefix + vsi + self.url]
            else:
                # Falling back on local files
                logging.warning("It is apparently not possible to use vsicurl syntax with this dataset. You will "
                                "have to download it first. We are giving you here a random path, please adjust")
                return self.get_local_file_source(use=True).get_source_paths()

    def _check_remote_access(self):
        if self.is_archive():
            logging.warning("Does not support archive files. Please use check_remote_access_archive instead")
            return None
        else:
            if self.is_streaming() or not self.get_data_full_size():
                # We can have a go at streaming protocol
                vsistring = "/vsicurl_streaming/" + self.url
                if self.get_file_extension() == ".csv":
                    vsistring = "CSV:" + vsistring
                if ogr_utils.is_valid_ogr_path(vsistring):
                    return "/vsicurl_streaming/"

            # in case it didn't work or isn't streaming protocol, we try with vsicurl classic
            vsistring = "/vsicurl/" + self.url
            if self.get_file_extension() == ".csv":
                vsistring = "CSV:" + vsistring
            if ogr_utils.is_valid_ogr_path(vsistring):
                return "/vsicurl/"

            # If we reached here, none of them work
            return None

    def _check_remote_access_archive(self, vsizip: str, path: str):
        """
        Find with vsicurl protocol is functional if any. For archive datasets, we have to provide also the
        vsizip or similar prefix and know the path in the archive
        Returns None if no remote protocol works
        :param vsizip: will be one of the values provided by ogr_utils.vsimappings
        :param path: path to the data in the archive
        :return:
        """
        if self.is_streaming() or not self.get_data_full_size():
            # We can have a go at streaming protocol
            vsistring = vsizip + "/vsicurl_streaming/" + self.url + "/" + path
            if ogr_utils.is_valid_ogr_path(vsistring):
                return "/vsicurl_streaming/"

        # in case it didn't work or isn't streaming protocol, we try with vsicurl classic
        vsistring = vsizip + "/vsicurl/" + self.url + "/" + path
        if ogr_utils.is_valid_ogr_path(vsistring):
            return "/vsicurl/"

        # If we reached here, none of them work
        return None

    def collect_layers(self, path: str = None, db_friendly: bool = False) -> list[dict]:
        """
        Collect layers definition for the data pointed by path (path is a vsi-enabled OGR path).
        If path is not provided, it will look at all the paths returned by get_source_paths
        :param path:
        :param db_friendly:
        :return:
        """
        # If param's not set in the function, look in the global config
        if not db_friendly:
            db_friendly = self.config.get("db_friendly", False)

        if path:
            source_paths = [path]
        else:
            source_paths = self.get_source_paths()
        layers_collection = []
        for s in source_paths:
            try:
                layer = ogr_utils.collect_layers(s, db_friendly)
                if layer:
                    layers_collection.append({
                        "source_path": s,
                        "layers": layer
                    })
            except Exception as e:
                if path:
                    # path was explicitly provided => it is expected to work
                    logging.error(f"Error trying to collect layers for path {s}")
                else:
                    # This is probably expected since we might encounter some false-positive files
                    # when processing all eligible files
                    logging.debug(f"Error trying to collect layers for path {s}")
        return layers_collection

    def build_vrt(self, path: str = None, db_friendly: bool = False) -> str:
        """
        Build the VRT file for the data pointed by path.
        If path is not provided, it will look at all the paths returned by get_source_paths
        :param path:
        :param db_friendly:
        :return:
        """
        # If param's not set in the function, look in the global config
        if not db_friendly:
            db_friendly = self.config.get("db_friendly", False)

        layers_collection = self.collect_layers(path, db_friendly)
        vrt_content = ogr_utils.layers2vrt(layers_collection)
        return vrt_content
