"""
String utility functions
"""

import re

from unidecode import unidecode


def db_friendly_name(s):
    """
    Convert a human-friendly name to a DB-friendly one (no space, accent, all-lowercase)
    ex. 'Číslo žiadosti' -> 'cislo_ziadosti'
    :param s:
    :return:
    """
    return re.sub(r"[\.\s-]", "_", unidecode(s)).lower()
