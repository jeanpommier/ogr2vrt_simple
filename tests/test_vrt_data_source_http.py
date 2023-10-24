import os
import unittest

from ogr2vrt_simple.vrt_data_sources.http_source import HttpSource

sources = [
    "https://www.data.gouv.fr/fr/datasets/r/c53cd4d4-4623-4772-9b8c-bc72a9cdf4c2",
    "https://raw.githubusercontent.com/etalab/transport-base-nationale-covoiturage/main/bnlc-.csv",
    "https://www.data.gouv.fr/fr/datasets/r/d22ba593-90a4-4725-977c-095d1f654d28",
    "https://open-data.s3.fr-par.scw.cloud/bdnb_millesime_2022-10-d/millesime_2022-10-d_dep59/open_data_millesime_2022-10-d_dep59_gpkg.zip",
    "https://open-data.s3.fr-par.scw.cloud/bdnb_millesime_2022-10-d/millesime_2022-10-d_dep59/open_data_millesime_2022-10-d_dep59_csv.zip",
    # streaming:
    "https://metropole-europeenne-de-lille.opendatasoft.com/api/explore/v2.1/catalog/datasets/ouvrages-acquis-par-les-mediatheques-/exports/csv",
    "https://opendata.lillemetropole.fr/api/explore/v2.1/catalog/datasets/vlille-realtime/exports/csv",

    "https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1/datafiles/37dd7056-6c4d-44e0-a720-32d4064f9a26/csv?millesime=2023-05&withColumnName=true&withColumnDescription=true&withColumnUnit=true&orderBy=-COMMUNE_CODE&columns=COMMUNE_CODE,COMMUNE_LIBELLE,CLASSE_VEHICULE,CATEGORIE_VEHICULE,CARBURANT,CRITAIR,PARC_2011,PARC_2012,PARC_2013,PARC_2014,PARC_2015,PARC_2016,PARC_2017,PARC_2018,PARC_2019,PARC_2020,PARC_2021,PARC_2022&COMMUNE_CODE=contains%3A09241",
    "https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1/datafiles/8b35affb-55fc-4c1f-915b-7750f974446a/csv?millesime=2023-09&withColumnName=true&withColumnDescription=true&withColumnUnit=true&DEP_CODE=contains%3A59",

    "https://crinfo.iedu.sk/RISPortal/register/ExportCSV?id=1",
    "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-tertiaire/lines?size=10000&page=1&q_mode=simple&qs=(tv016_departement_code:(%2259%22))&finalizedAt=2022-12-13T09:39:32.665Z&format=csv",
    "https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/shp/poly.zip",
]


class TestHttpSource(unittest.TestCase):
    def test_get_file_extension_datagouv(self):
        src = HttpSource(sources[0])
        self.assertEqual(src.get_file_extension(), ".csv")

    def test_get_file_extension_rawgithub(self):
        """
        raw.github does advertise the service as plain/txt
        :return:
        """
        src = HttpSource(sources[1])
        self.assertEqual(src.get_file_extension(), ".csv")

    def test_get_file_extension_zip(self):
        src = HttpSource(sources[4])
        self.assertEqual(src.get_file_extension(), ".zip")

    def test_get_file_extension_ods(self):
        src = HttpSource(sources[6])
        self.assertEqual(src.get_file_extension(), ".csv")

    def test_get_file_extension_stats_with_urlparams(self):
        src = HttpSource(sources[7])
        self.assertEqual(src.get_file_extension(), ".csv")

    def test_get_file_extension_ademe(self):
        src = HttpSource(sources[10])
        self.assertEqual(src.get_file_extension(), ".csv")

    def test_is_archive(self):
        src = HttpSource(sources[4])
        self.assertTrue(src.is_archive())

    def test_is_not_archive(self):
        src = HttpSource(sources[1])
        self.assertFalse(src.is_archive())

    def test_is_streaming(self):
        src = HttpSource(sources[2])
        self.assertTrue(src.is_streaming())

    def test_is_not_streaming(self):
        src = HttpSource(sources[9])
        self.assertFalse(src.is_streaming())

    def test_collect_info_csv_non_streaming(self):
        src = HttpSource(sources[1])
        infos = src.collect_information()
        with self.subTest():
            self.assertEqual(infos['file_extension'], ".csv")
        with self.subTest():
            self.assertFalse(infos['is_archive'])
        with self.subTest():
            self.assertEqual(infos['charset'], "utf-8")
        with self.subTest():
            self.assertEqual(infos['can_be_remotely_accessed'], 10)

    def test_collect_info_csv_with_streaming(self):
        src = HttpSource(sources[2])
        infos = src.collect_information()
        with self.subTest():
            self.assertEqual(infos['file_extension'], ".csv")
        with self.subTest():
            self.assertFalse(infos['is_archive'])
        with self.subTest():
            self.assertTrue(infos['is_streaming'])
        with self.subTest():
            self.assertEqual(infos['charset'], "utf-8")
        with self.subTest():
            self.assertEqual(infos['can_be_remotely_accessed'], 10)

    def test_get_source_paths(self):
        conf = {
            "relative_to_file": True,
        }
        src = HttpSource("https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/shp/poly.zip", conf)
        paths = src.get_source_paths()
        expected = ["/vsizip//vsicurl/https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/shp/poly.zip/poly.shp"]
        self.assertEqual(paths, expected)

    def test_get_source_paths_with_named_zip_and_no_remote(self):
        conf = {
            "data_format": ".shp",
            "relative_to_file": True,
            "no_vsicurl": True,
            "filename": "polygon",
        }
        src = HttpSource("https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/shp/poly.zip", conf)
        paths = src.get_source_paths()
        self.assertEqual(paths, ["/vsizip/polygon.zip/poly.shp"])

    def test_zipped_shp_with_relative_path_no_specified_format(self):
        conf = {
            "data_format": ".shp",
            "relative_to_file": True,
        }
        src = HttpSource("https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/shp/poly.zip", conf)
        paths = src.get_source_paths()
        expected = ["/vsizip//vsicurl/https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/shp/poly.zip/poly.shp"]
        self.assertEqual(paths, expected)

    def test_build_vrt_zipped_remote_shp(self):
        """
        Basic case
        """
        conf = {
            "relative_to_file": True,
            "db_friendly": True,
        }
        src = HttpSource("https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/shp/poly.zip", conf)
        expected_xml = """<?xml version="1.0" encoding="UTF-8"?>
<OGRVRTDataSource>
  <OGRVRTLayer name="poly">
    <SrcDataSource relativeToVRT="1">/vsizip//vsicurl/https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/shp/poly.zip/poly.shp</SrcDataSource>
    <!--<SrcSql dialect="sqlite">SELECT * FROM 'poly'</SrcSql>-->
    <SrcLayer>poly</SrcLayer>
    <Field name="area" src="AREA" type="Real" width="12"/>
    <Field name="eas_id" src="EAS_ID" type="Integer64" width="11"/>
    <Field name="prfedea" src="PRFEDEA" type="String" width="16"/>
  </OGRVRTLayer>
</OGRVRTDataSource>"""
        vrt_xml = src.build_vrt()
        self.assertEqual(vrt_xml, expected_xml)

    def test_build_vrt_zipped_remote_shp_force_local(self):
        """
        Basic case
        """
        conf = {
            "relative_to_file": True,
            "db_friendly": True,
            "no_vsicurl": True,
            "filename": "polygon",
        }
        src = HttpSource("https://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/shp/poly.zip", conf)
        expected_xml = """<?xml version="1.0" encoding="UTF-8"?>
<OGRVRTDataSource>
  <OGRVRTLayer name="poly">
    <SrcDataSource relativeToVRT="1">/vsizip/polygon.zip/poly.shp</SrcDataSource>
    <!--<SrcSql dialect="sqlite">SELECT * FROM 'poly'</SrcSql>-->
    <SrcLayer>poly</SrcLayer>
    <Field name="area" src="AREA" type="Real" width="12"/>
    <Field name="eas_id" src="EAS_ID" type="Integer64" width="11"/>
    <Field name="prfedea" src="PRFEDEA" type="String" width="16"/>
  </OGRVRTLayer>
</OGRVRTDataSource>"""
        vrt_xml = src.build_vrt()
        self.assertEqual(vrt_xml, expected_xml)

    def tearDown(self):
        try:
            os.remove('polygon.zip')
        except:
            pass


if __name__ == '__main__':
    unittest.main()
