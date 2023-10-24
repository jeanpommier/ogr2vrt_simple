"""
Abstract class. Implement this when you define a new data source
"""

from abc import ABC, abstractmethod


class AbstractSource(ABC):

    type: str = ""  # one of http, ftp, file

    @abstractmethod
    def collect_information(self) -> dict:
        """
        Collect the information about the source data
        :return: a dict
        """
        pass

    @abstractmethod
    def is_remote(self) -> bool:
        """
        Determine whether the source is remote (http of ftp) or local
        :return:
        """
        pass

    @abstractmethod
    def is_archive(self) -> bool:
        """
        Determine whether the source is zip-like archive (path to dataset will have to be processed differently)
        :return:
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """
        Try to figure out the file extension (file type)
        :return: file extension string
        """
        pass

    def get_data_full_size(self) -> tuple[int, str]:
        """
        :return: tuple : (byte size, human-friendly file size (str))
        """
        pass
