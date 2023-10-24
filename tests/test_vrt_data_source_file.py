import os.path
import unittest

from ogr2vrt_simple.vrt_data_sources.file_source import FileSource

sources = [
    "../sample_data/conso-ener.csv",
    "../sample_data/locations.7z",
    "../sample_data/locations.rar",
    "../sample_data/conso-ener-windows1252.csv",
    "../sample_data/locations.zip",
    "../sample_data/sagui.tgz",
]


class TestFileSource(unittest.TestCase):
    def test_get_file_extension(self):
        src = FileSource(sources[0])
        self.assertEqual(src.get_file_extension(), ".csv")

    def test_get_file_extension_archive(self):
        src = FileSource(sources[1])
        self.assertEqual(src.get_file_extension(), ".7z")

    def test_get_data_full_size(self):
        src = FileSource(sources[1])
        self.assertEqual(src.get_data_full_size(), (626, "626 Bytes"))

    def test_get_charset_utf8(self):
        src = FileSource(sources[0])
        self.assertEqual(src.get_charset(), "utf_8")

    def test_get_charset_latin1(self):
        src = FileSource(sources[3])
        self.assertNotEqual(src.get_charset(), "utf_8")

    def test_get_source_paths(self):
        src = FileSource(sources[0])
        p = os.path.abspath(sources[0])
        self.assertEqual(src.get_source_paths(), [p])

    def test_get_source_paths_archive(self):
        src = FileSource(sources[1])
        p = os.path.abspath(sources[1])
        self.assertEqual(src.get_source_paths(), ["/vsi7z/" + p + "/world/locations/locations.csv"])

    def test_get_source_paths_archive_multiple(self):
        src = FileSource(sources[4])
        p = os.path.abspath(sources[4])
        expected = [
            "/vsizip/" + p + "/world/empty.xlsx",
            "/vsizip/" + p + "/world/locations/locations.csv",
        ]
        self.assertEqual(src.get_source_paths().sort(), expected.sort())

    def test_get_source_paths_archive_multiple_but_declared_format(self):
        conf = {
            "data_formats": ".xlsx",
        }
        src = FileSource(sources[4], conf)
        p = os.path.abspath(sources[4])
        expected = [
            "/vsizip/" + p + "/world/empty.xlsx",
        ]
        self.assertEqual(src.get_source_paths(), expected)

    def test_get_source_paths_tgz_gpkg_with_path(self):
        conf = {
            "data_formats": ".gpkg",
            "relative_to_file": True,
        }
        src = FileSource(sources[5], conf)
        expected = [
            "/vsitar/../sample_data/sagui.tgz/sagui/data/layers/layers.gpkg",
        ]
        self.assertEqual(src.get_source_paths(), expected)

    def test_build_vrt_simple(self):
        src = FileSource(sources[4])
        p = os.path.abspath(sources[4])
        vrt = src.build_vrt(db_friendly=True)
        expected = f"""<?xml version="1.0" encoding="UTF-8"?>
<OGRVRTDataSource>
  <OGRVRTLayer name="locations">
    <SrcDataSource relativeToVRT="1">/vsizip/{p}/world/locations/locations.csv</SrcDataSource>
    <!--<SrcSql dialect="sqlite">SELECT * FROM 'locations'</SrcSql>-->
    <SrcLayer>locations</SrcLayer>
    <Field name="lat" src="LAT" type="String" />
    <Field name="lon" src="LON" type="String" />
    <Field name="city" src="CITY" type="String" />
    <Field name="number" src="NUMBER" type="String" />
    <Field name="year" src="YEAR" type="String" />
  </OGRVRTLayer>
</OGRVRTDataSource>"""
        self.assertEqual(vrt, expected)
