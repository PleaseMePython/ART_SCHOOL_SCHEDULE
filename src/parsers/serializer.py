"""Сериализация XML в нужном виде."""

from xml.etree import ElementTree

from pydantic_xml import BaseXmlModel


def seralizer(model: BaseXmlModel) -> bytes:
    """Сериализация XML в нужном виде."""
    # Если использовать to_xml, то вместо кириллицы будут коды Unicode
    dst_tree = model.to_xml_tree(skip_empty=True, exclude_none=True, exclude_unset=True)

    return ElementTree.tostring(dst_tree, encoding='utf-8')
