"""
File data source/factory.
Defined by a file path
"""
import logging
import os

import charset_normalizer
import humanize
from ogr2vrt_simple.utils import ogr_utils

from ogr2vrt_simple.vrt_data_sources import archive_extension_list, common_dataset_extensions
from ogr2vrt_simple.vrt_data_sources.abstract_source import AbstractSource


class FileSource(AbstractSource):
    file_path: str = ""
    type: str = "file"
    config: dict = {}
    file_extension: str = None

    def __init__(self, file_path: str, config: dict = None):
        self.file_path = file_path
        if config:
            self.config = config

        # Check that the file exists
        try:
            os.path.getsize(file_path)
        except FileNotFoundError:
            logging.error("File not found.")
            raise FileNotFoundError
        except OSError:
            logging.error("OS error occurred when trying to fetch file size")

    def collect_information(self) -> dict:
        """
        Gather information about the data source.
        path is called url for consistency with the http source
        :return:
        """
        return {
            "url": self.file_path,
            "type": self.type,
            "file_extension": self.get_file_extension(),
            "is_archive": self.is_archive(),
            "is_streaming": False,
            "file_size": self.get_data_full_size(),
            "charset": self.get_charset(),
            "can_be_remotely_accessed": False,
        }

    def is_remote(self) -> bool:
        return False

    def get_file_extension(self) -> str:
        """
        Easy for file-based data
        :return: file extension string
        """
        return os.path.splitext(self.file_path)[1]

    def is_archive(self) -> bool:
        ext = self.get_file_extension()
        return ext in archive_extension_list

    def get_data_full_size(self) -> tuple[int, str]:
        """
        :return: tuple : (byte size, human-friendly file size (str))
        """
        try:
            size = os.path.getsize(self.file_path)
            binary_size = humanize.naturalsize(size, binary=True)
            # print(ct)
            return size, binary_size
        except FileNotFoundError:
            logging.error("File not found.")
            raise FileNotFoundError
        except OSError:
            logging.error("OS error occurred when trying to fetch file size")
            raise OSError

    def get_charset(self):
        if self.is_archive():
            return None
        cn = charset_normalizer.from_path(self.file_path).best()
        if cn:
            return cn.encoding

        return None

    def find_paths_in_archive(self) -> list[str]:
        """
        Scan the archive's content to identify the files that might be a candidate for OGR. By default, will select all
        files which extension is found in the common_dataset_extensions list. Unless data_formats is provided in config dict
        :return:
        """
        if not self.is_archive():
            return []
        data_formats = self.config.get("data_formats", None)
        file_extensions = (
            data_formats.split(",") if data_formats else common_dataset_extensions
        )
        ext = self.get_file_extension()

        if ext == ".zip":
            import zipfile
            with zipfile.ZipFile(self.file_path, "r") as zip_file:
                file_list = zip_file.namelist()
                # print("The file list is:",file_list)
                return [
                    f for f in file_list if os.path.splitext(f)[1] in file_extensions
                ]
        elif ext in (".tar.gz", ".tgz"):
            import tarfile
            with tarfile.open(self.file_path, "r") as tar:
                file_list = tar.getmembers()
                # print("The file list is:", file_list)
                return [
                    f.name
                    for f in file_list
                    if os.path.splitext(f.name)[1] in file_extensions
                ]
        elif ext == ".7z":
            import py7zr
            with py7zr.SevenZipFile(self.file_path, mode='r') as z:
                return [
                    p.filename
                    for p in z.list()
                    if not p.is_directory and os.path.splitext(p.filename)[1] in file_extensions
                ]
        elif ext == ".rar":
            import rarfile
            rf = rarfile.RarFile(self.file_path)
            return [
                p.filename
                for p in rf.infolist()
                if os.path.splitext(p.filename)[1] in file_extensions
            ]
        else:
            print(f"Compression format not supported yet ({other})")
            return []
            # TODO: add support for other compression formats

    def get_source_paths(self) -> list:
        """
        Generate the OGR source path with vsi prefixes and specific logic (e.g. for archives)
        Since there might be several matches, it will always return a list of candidates
        :return:
        """
        fp = os.path.abspath(self.file_path)
        if self.config.get("relative_to_file", False):
            fp = os.path.relpath(self.file_path)
        if self.is_archive():
            pre = ogr_utils.vsiprefix_from_archive_extension(self.get_file_extension())
            return [pre + fp + "/" + p for p in self.find_paths_in_archive()]
        else:
            return [fp]

    def collect_layers(self, path: str = None, db_friendly: bool = False) -> list[dict]:
        """
        Collect layers definition for the data pointed by path.
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
                layers = ogr_utils.collect_layers(s, db_friendly)
                if layers:
                    layers_collection.append({
                        "source_path": s,
                        "layers": layers
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
