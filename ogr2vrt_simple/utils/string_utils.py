"""
String utility functions
"""

import re

from unidecode import unidecode


def db_friendly_name(s):
    """
    Convert a human-friendly name to a DB-friendly one (no space, accent, all-lowercase)
    Actually it does
     - unidecode removes all accents
     - lowercase the string
     - replace everything that is not (alphanumeric or _) by _
    ex. 'Číslo žiadosti' -> 'cislo_ziadosti'
    :param s:
    :return:
    """
    return re.sub(r"[\W]", "_", unidecode(s)).lower()
