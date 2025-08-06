from enum import IntEnum

from pydantic_xml.typedefs import EntityLocation


class NodeType(IntEnum):
    """Field data location."""

    ELEMENT = EntityLocation.ELEMENT
    ATTRIBUTE = EntityLocation.ATTRIBUTE
    WRAPPED = EntityLocation.WRAPPED
