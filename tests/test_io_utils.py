import unittest

from ogr2vrt_simple.utils import io_utils

class TestExtensionFromUrl(unittest.TestCase):
    def test_no_ext(self):
        """
        header: text/csv
        """
        url = "https://www.data.gouv.fr/fr/datasets/r/c53cd4d4-4623-4772-9b8c-bc72a9cdf4c2"
        ext = io_utils.get_extension_from_url(url)
        self.assertEqual(ext, "")

    def test_csv(self):
        """
        header: text/csv
        """
        url = "https://raw.githubusercontent.com/etalab/transport-base-nationale-covoiturage/main/bnlc-.csv"
        ext = io_utils.get_extension_from_url(url)
        self.assertEqual(ext, ".csv")

    def test_zip(self):
        """
        header: text/csv
        """
        url = "https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/shp/poly.zip"
        ext = io_utils.get_extension_from_url(url)
        self.assertEqual(ext, ".zip")


class TestExtensionFromHeaders(unittest.TestCase):
    def test_csv(self):
        """
        header: text/csv
        """
        url = "https://www.data.gouv.fr/fr/datasets/r/c53cd4d4-4623-4772-9b8c-bc72a9cdf4c2"
        ext = io_utils.get_extension_from_headers(url)
        self.assertEqual(ext, ".csv")

    def test_csv2(self):
        """
        header: text/csv; charset=utf-8
        """
        url = "https://metropole-europeenne-de-lille.opendatasoft.com/api/explore/v2.1/catalog/datasets/ouvrages-acquis-par-les-mediatheques-/exports/csv"
        ext = io_utils.get_extension_from_headers(url)
        self.assertEqual(ext, ".csv")

    def test_csv_streaming(self):
        """
        header: text/csv; charset=utf-8
        """
        url = "https://metabase.dora.fabrique.social.gouv.fr/public/question/769d4131-f739-4e6b-8ca5-0af2b09ba930.csv"
        ext = io_utils.get_extension_from_headers(url)
        self.assertEqual(ext, ".csv")

    def test_csv_from_rawgithub(self):
        """
        header: text/plain; charset=utf-8
        This is documented: raw.github will send files as plain/text. Which means we cannot detect the file type in this case
        """
        url = "https://raw.githubusercontent.com/etalab/transport-base-nationale-covoiturage/main/bnlc-.csv"
        ext = io_utils.get_extension_from_headers(url)
        self.assertEqual(ext, ".txt")

    def test_application_csv(self):
        """
        header: application/csv; charset=utf-8
        Check proper extension detection when mime type is application/csv
        """
        url = "https://www.data.gouv.fr/fr/datasets/r/d22ba593-90a4-4725-977c-095d1f654d28"
        ext = io_utils.get_extension_from_headers(url)
        self.assertEqual(ext, ".csv")

    def test_zip(self):
        """
        header: application/zip
        """
        url = "https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/shp/poly.zip"
        ext = io_utils.get_extension_from_url(url)
        self.assertEqual(ext, ".zip")


class TestIsArchive(unittest.TestCase):
    def test_zip(self):
        self.assertTrue(io_utils.is_archive("zip"))

    def test_csv(self):
        self.assertFalse(io_utils.is_archive("csv"))

    def test_gz(self):
        self.assertFalse(io_utils.is_archive("gz"))


class TestGuessCurlMode(unittest.TestCase):
    def test_vsicurl(self):
        url = "https://www.data.gouv.fr/fr/datasets/r/c53cd4d4-4623-4772-9b8c-bc72a9cdf4c2"
        streaming = io_utils.is_streaming(url)
        self.assertFalse(streaming)

    def test_vsicurl_streaming(self):
        url = "https://www.data.gouv.fr/fr/datasets/r/d22ba593-90a4-4725-977c-095d1f654d28"
        streaming = io_utils.is_streaming(url)
        self.assertTrue(streaming)


class TestGetDataFullSize(unittest.TestCase):
    def test_get_data_full_size(self):
        url = "https://www.data.gouv.fr/fr/datasets/r/c53cd4d4-4623-4772-9b8c-bc72a9cdf4c2"
        size = io_utils.get_data_full_size(url)
        with self.subTest():
            self.assertGreater(float(size.split(" ")[0]), 3)
        with self.subTest():
            self.assertEqual(size.split(" ")[1], "MiB")


class TestFindPathsInArchive(unittest.TestCase):
    def test_find_shp_in_zip(self):
        path = "../sample_data/poly.zip"
        paths = io_utils.find_paths_in_archive(path, ".zip", ".shp")
        self.assertEqual(paths, ["poly.shp"])

    def test_fin_several_in_zip(self):
        path = "../sample_data/poly.zip"
        paths = io_utils.find_paths_in_archive(path, ".zip", ".shp,.dbf")
        self.assertEqual(paths, ["poly.dbf","poly.shp"])


if __name__ == '__main__':
    unittest.main()
