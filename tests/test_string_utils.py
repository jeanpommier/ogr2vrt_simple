import unittest

from ogr2vrt_simple.utils.string_utils import db_friendly_name


class TestDbFriendly(unittest.TestCase):
    def test_simple(self):
        s = db_friendly_name("Parc de véhicule au 1er janvier 2011")
        self.assertEqual(s, "parc_de_vehicule_au_1er_janvier_2011")

    def test_unidecode_slovak(self):
        s = db_friendly_name("Číslo žiadosti")
        self.assertEqual(s, "cislo_ziadosti")

    def test_parentheses(self):
        s = db_friendly_name("Parc de véhicule au 1er janvier 2011 (en nombre de véhicules)")
        self.assertEqual(s, "parc_de_vehicule_au_1er_janvier_2011__en_nombre_de_vehicules_")


if __name__ == '__main__':
    unittest.main()
