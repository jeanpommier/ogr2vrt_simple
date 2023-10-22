import os
import unittest

from ogr2vrt_simple.utils import ogr_utils

class TestBuildSourcePath(unittest.TestCase):
    def test_zipped_shp_with_relative_path(self):
        """
        Basic case
        """
        download_config = {
            "data_format": ".shp",
            "relative_to_file": True
        }
        url = "../sample_data/poly.zip"
        p = ogr_utils.build_source_paths(url, download_config)
        self.assertEqual(p, [{
                                "path": "/vsizip/../sample_data/poly.zip/poly.shp",
                                "confidence": 1,
                                "kind": "local",
                            }]
                         )


    def test_zipped_shp_with_relative_path_no_specified_format(self):
        """
        We don't say which format, it should find only shp one in here
        """
        download_config = {
            "data_format": "",
            "relative_to_file": True
        }
        url = "../sample_data/poly.zip"
        p = ogr_utils.build_source_paths(url, download_config)
        self.assertEqual(p, [{
                                "path": "/vsizip/../sample_data/poly.zip/poly.shp",
                                "confidence": 1,
                                "kind": "local",
                            }]
                         )

    def test_tgz_gpkg_with_path(self):
        """
        Should fin the proper path to the gpkg file in the archive
        """
        download_config = {
            "data_format": ".gpkg",
            "relative_to_file": True
        }
        url = "../sample_data/sagui.tgz"
        p = ogr_utils.build_source_paths(url, download_config)
        self.assertEqual(p, [{
                                "path": "/vsitar/../sample_data/sagui.tgz/sagui/data/layers/layers.gpkg",
                                "confidence": 1,
                                "kind": "local",
                            }]
                         )

    def test_online_csv(self):
        """
        Source is online and CSV
        """
        download_config = {
            "data_format": ".csv",
            "filename": "testing.csv",
            "relative_to_file": False,
            "with_vsicurl": False,
        }
        url = "https://www.data.gouv.fr/fr/datasets/r/c53cd4d4-4623-4772-9b8c-bc72a9cdf4c2"
        p = ogr_utils.build_source_paths(url, download_config)
        self.assertEqual(p, [{
                                "path": "CSV:/vsicurl/https://www.data.gouv.fr/fr/datasets/r/c53cd4d4-4623-4772-9b8c-bc72a9cdf4c2",
                                "confidence": 0.8,
                                "kind": "remote",
                            },{
                                "path": "CSV:testing.csv",
                                "confidence": 1,
                                "kind": "local",
                            }]
                         )

    def test_online_csv_absolute(self):
        """
        Source is online and CSV
        """
        download_config = {
            "data_format": ".csv",
            "filename": "/tmp/testing.csv",
            "relative_to_file": False,
            "with_vsicurl": False,
        }
        url = "https://www.data.gouv.fr/fr/datasets/r/c53cd4d4-4623-4772-9b8c-bc72a9cdf4c2"
        p = ogr_utils.build_source_paths(url, download_config)
        # os.remove("/tmp/testing.csv") # clean up
        self.assertEqual(p, [{
                                "path": "CSV:/vsicurl/https://www.data.gouv.fr/fr/datasets/r/c53cd4d4-4623-4772-9b8c-bc72a9cdf4c2",
                                "confidence": 0.8,
                                "kind": "remote",
                            },{
                                "path": "CSV:/tmp/testing.csv",
                                "confidence": 1,
                                "kind": "local",
                            }]
                         )

class TestBuildVrt(unittest.TestCase):
    def test_zipped_remote_shp(self):
        """
        Basic case
        """
        download_config = {
            "data_format": ".",
            "relative_to_file": True
        }
        paths = [{
            'path': '/vsizip/57306a55-549a-468e-973a-8de4c648d08e.zip/poly.shp',
            'confidence': 1,
            'kind': 'local'
        }, {
            'path': '/vsizip//vsicurl/https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/shp/poly.zip/poly.shp',
            'confidence': 0.8,
            'kind': 'remote'
        }]
        expected_xml = """<?xml version="1.0" encoding="UTF-8"?>
<OGRVRTDataSource>
  <OGRVRTLayer name="poly">
    <SrcDataSource relativeToVRT="1">poly.shp</SrcDataSource>
    <!--<SrcSql dialect="sqlite">SELECT * FROM 'poly'</SrcSql>-->
    <SrcLayer>poly</SrcLayer>
    <Field name="area" src="AREA" type="Real" width="12"/>
    <Field name="eas_id" src="EAS_ID" type="Integer64" width="11"/>
    <Field name="prfedea" src="PRFEDEA" type="String" width="16"/>
  </OGRVRTLayer>
</OGRVRTDataSource>"""
        vrt_xml = ogr_utils.build_vrt(paths, vrt_template="../ogr2vrt_simple/templates/vrt.j2")
        self.assertEqual(vrt_xml, expected_xml)

    # def tearDown(self):
    #     if os.path.exists("/tmp/testing.csv"):
    #         os.remove("/tmp/testing.csv")
    #     pass


if __name__ == '__main__':
    unittest.main()
