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

# Handle the cases where you run it directly or as a built and installed package (2nd option)
if __name__ == "__main__":
    from utils import ogr_utils, io_utils
else:
    from .utils import ogr_utils, io_utils

logger = logging.getLogger()
vrt_template: str = None
out_file: str = None
db_friendly: bool = False
data_format: str = None


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
    "--with_vsicurl",
    is_flag=True,
    help="if possible, use an online connection string (with vsicurl)",
)
@click.option(
    "--data_format",
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
    with_vsicurl,
    data_format,
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

    download_config = {
        "filename": os.path.splitext(out_file)[0] if out_file else "",
        "relative_to_file": relative_to_file,
        "db_friendly": db_friendly,
        "with_vsicurl": with_vsicurl,
        "data_format": data_format,
        "template": template,
    }
    data_source = source
    source_paths = ogr_utils.build_source_paths(data_source, download_config)
    print(source_paths)
    is_remote= source.startswith("http")
    vrt_xml = ogr_utils.build_vrt(source_paths, template, is_remote)
    if vrt_xml:
        if out_file:
            with open(out_file, "w") as f:
                f.write(vrt_xml)
                print(f"VRT file written to {out_file}")
        else:
            print(vrt_xml)
    else:
        print("error build VRT file")


if __name__ == "__main__":
    cli(auto_envvar_prefix="OGR2VRT")
