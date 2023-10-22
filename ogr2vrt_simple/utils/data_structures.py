"""
Data structures used for internal representation of the VRT configuration
Uses dataclasses
"""
from dataclasses import dataclass, field

from osgeo import ogr

from . import string_utils


@dataclass
class FieldDefinition:
    name: str
    output_name: str
    type: str
    width: int


@dataclass
class DataLayer:
    """
    Represent a data layer, can be an excel sheet, a geopackage layer, etc.
    CSV files, shapefiles, have only 1 layer. Excel, LibreOffice Calc, geopackage can have several
    """

    ogr_layer: ogr.Layer
    db_friendly: bool = field(default=True)
    layer_name: str = field(init=False)
    fields_definition: list[FieldDefinition] = field(init=False)

    def __post_init__(self):
        self.layer_name = self.ogr_layer.GetName()

        defs = []
        layer_schema = self.ogr_layer.GetLayerDefn()
        for field_idx in range(layer_schema.GetFieldCount()):
            field = layer_schema.GetFieldDefn(field_idx)
            defs.append(
                FieldDefinition(
                    field.GetName(),
                    string_utils.db_friendly_name(field.GetName())
                    if self.db_friendly
                    else field.GetName(),
                    field.GetTypeName(),
                    field.GetWidth(),
                )
            )
        self.fields_definition = defs
