#!/usr/bin/env python3

"""
Generate a VRT file from an OGR-compatible source.
The result is to be considered as a "kickoff" VRT file, to refine according to your desires
but it will save you some time.

Code licensed against CC0 (Creative Commons zero) license
Author: Jean Pommier <jean.pommier@pi-geosolutions.fr>
"""

import click
import logging
import os

from ogr2vrt_simple.vrt_data_sources.file_source import FileSource
from ogr2vrt_simple.vrt_data_sources.http_source import HttpSource

# Handle the cases where you run it directly or as a built and installed package (2nd option)
if __name__ == "__main__":
    from utils import ogr_utils, io_utils
else:
    from .utils import ogr_utils, io_utils

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

@click.group()
def cli():
    pass


@cli.command()
# @click.option('--api_url', default=default_inpn_api_url, help='URL to the contact point reference service')
# @click.option('-t','--template_file', default='templates/poc_xml.j2', help='Jinja2 template to structure each POC')
# @click.option('-d', '--destination_path', default='/tmp/contacts', help='Folder where the contact xml files will be written')
@click.option(
    "-o",
    "--out_file",
    help="Output file name. Default: name of the template, without the jinja extension",
)
@click.option(
    "--relative_to_file",
    is_flag=True,
    help="When building the datasource string, wheter to use absolute path or not. Defaults to absolute",
)
@click.option(
    "-d",
    "--db_friendly",
    is_flag=True,
    help="convert layer and field names to DB-friendly names (no space, accent, all-lowercase)",
)
@click.option(
    "--no_vsicurl",
    is_flag=True,
    help="do not even try to use vsicurl. Prefer download and local use",
)
@click.option(
    "--data_formats",
    help="file extensions to look for when querying an archive (zip, tgz, etc). "
    "Defaults to a list of common data file extensions",
)
@click.option("--logfile", help="logfile path. Default: prints logs to the console")
@click.option("-t", "--template", help="template file path. Default: templates/vrt.j2")
@click.option("-v", "--verbose", is_flag=True, help="verbose output (debug loglevel)")
@click.argument("source")
def generate_vrt(
    out_file,
    relative_to_file,
    db_friendly,
    no_vsicurl,
    data_formats,
    logfile,
    template,
    verbose,
    source,
):
    """
    Generate a VRT file from a OGR-compatible source. The result is to be considered as a "kickoff" VRT file, to
    refine according to your desires but it will save you some time.

    SOURCE can be a local file or a remote URL
    """

    config = {
        "filename": os.path.splitext(out_file)[0] if out_file else "",
        "relative_to_file": relative_to_file,
        "db_friendly": db_friendly,
        "no_vsicurl": no_vsicurl,
        "data_formats": _add_dots(data_formats),
        "template": template,
    }
    data_source = source
    vrt_factory = None
    if source.startswith("http"):
        vrt_factory = HttpSource(data_source, config)
    else:
        vrt_factory = FileSource(data_source, config)
    source_paths = vrt_factory.get_source_paths()
    # print(source_paths)
    vrt_xml = vrt_factory.build_vrt()
    if vrt_xml:
        if out_file:
            with open(out_file, "w") as f:
                f.write(vrt_xml)
                logger.info(f"VRT file written to {out_file}")
        else:
            print(vrt_xml)
    else:
        logger.error("error build VRT file")


def _add_dots(formats: str) -> str:
    """
    In the OGR datasources we will want format extensions with a dot in front.
    Add them if not provided by the user
    :param formats:
    :return:
    """
    if not formats:
        return ""

    fixed = []
    for ext in formats.split(","):
        if not ext.startswith("."):
            fixed.append(f".{ext}")
    return ",".join(fixed)


if __name__ == "__main__":
    cli(auto_envvar_prefix="OGR2VRT")
