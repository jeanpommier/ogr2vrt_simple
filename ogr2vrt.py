#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate a VRT file from a OGR-compatible source.
The result is to be considered as a "kickoff" VRT file, to refine according to your desires
but it will save you some time.
"""

import argparse
import logging
import re
import os
from jinja2 import Template
from osgeo import ogr
from unidecode import unidecode


logger = logging.getLogger()
vrt_template = "templates/vrt.j2"
out_file = "out.vrt"
db_friendly = False

def main():
    # Input arguments
    parser = argparse.ArgumentParser(description='''
    Generate a VRT file from a OGR-compatible source. The result is to be considered as a "kickoff" VRT file, to 
    refine according to your desires but it will save you some time.
    ''')
    parser.add_argument('file', metavar='source_file', help='path to the source data file (xlsx, ods, csv, shp, gpkg, ...)')
    parser.add_argument('-o', '--out_file',
                        help='Output file name. Default: name of the template, without the jinja extension')
    parser.add_argument('-v', '--verbose', help='verbose output (debug loglevel)',
                        action='store_true')
    parser.add_argument('-d', '--db_friendly', help='convert layer and field names to DB-friendly names (no space, accent, all-lowercase)',
                        action='store_true')
    parser.add_argument('--logfile',
                        help='logfile path. Default: prints logs to the console')
    parser.add_argument('-t', '--template',
                        help='template file path. Default: templates/vrt.j2')
    args = parser.parse_args()


    # INITIALIZE LOGGER
    handler = logging.StreamHandler()
    if args.logfile:
        handler = logging.FileHandler(args.logfile)

    formatter = logging.Formatter(
            '%(asctime)s %(name)-5s %(levelname)-3s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    loglevel = logging.INFO
    if args.verbose:
        loglevel = logging.DEBUG
    logger.setLevel(loglevel)

    # Initialize global vars
    if args.template:
        global vrt_template
        vrt_template = args.template

    global db_friendly
    if args.db_friendly:
        db_friendly = args.db_friendly

    global out_file
    if args.out_file:
        out_file = args.out_file
    else:
        # extract the output file name from the template file (removing the path and the jinja extension)
        # out_file = os.path.splitext(os.path.basename(file))[0] + '.vrt'
        out_file = os.path.splitext(args.file)[0] + '.vrt'

    ogr2vrt(args.file)


class DataLayer():
    """
    Represent a data layer, can be an excel sheet, a geopackage layer, etc.
    CSV files, shapefiles, have only 1 layer. Excel, LibreOffice Calc, geopackage can have several
    """
    def __init__(self, ogr_layer):
        self.ogr_layer = ogr_layer
        self.layer_name = ogr_layer.GetName()
        self.fields_definition = self.load_fields_definition()

    def load_fields_definition(self):
        defs = []
        layer_schema = self.ogr_layer.GetLayerDefn()
        for field_idx in range(layer_schema.GetFieldCount()):
            field = layer_schema.GetFieldDefn(field_idx)
            defs.append({
                'name': field.GetName(),
                'output_name': db_friendly_name(field.GetName()) if db_friendly else field.GetName(),
                'type': field.GetTypeName(),
                'width': field.GetWidth()
            })
        return defs


def db_friendly_name(s):
    """
    Convert a human-friendly name to a DB-friendly one (no space, accent, all-lowercase)
    ex. 'Číslo žiadosti' -> 'cislo_ziadosti'
    :param s:
    :return:
    """
    return re.sub(r"[\s-]", "_", unidecode(s)).lower()


def ogr2vrt(filename):
    layers = collect_layers(filename)
    vrt_xml = layers2vrt(layers, source_file=filename)
    if vrt_xml:
        logger.info("Writing VRT definition to {}".format(out_file))
        with open(out_file, 'w') as f:
            f.write(vrt_xml)


def collect_layers(filename):
    inDataSource = ogr.Open(filename)
    layers = []
    for layer_idx in range(inDataSource.GetLayerCount()):
        layer = inDataSource.GetLayerByIndex(layer_idx)
        layers.append(DataLayer(layer))
    return layers


def layers2vrt(layers_list: list, source_file: str):
    with open(vrt_template) as file_:
        template = Template(file_.read())
        vrt_xml = template.render(layers=layers_list, source_file=source_file)
        return vrt_xml


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()