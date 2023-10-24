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
    clean = re.sub(r"[\W]", "_", unidecode(s)).lower()
    # see https://docs.python.org/3/library/re.html#re.sub for why \g<0>
    return re.sub(r"^[0-9]", "_\g<0>", clean)
