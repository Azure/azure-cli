# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
import re


def get_xml_content(xml, xml_path, xml_uri):
    """Gets the XML content for policies based on the 3 options that a user can provide, with inline taking precedentsm, then file, then uri"""
    xml_content = xml
    if xml_content is None:
        if xml_path is not None:
            xml_content = read_file(xml_path)
        else:
            xml_content = xml_uri
    return xml_content


def read_file(file_path):
    import os
    with open(os.path.realpath(os.path.expanduser(file_path)), 'r') as fs:
        content = fs.read()
        return content


def resolve_version_set_id(version_set_id):
    API_VS_ARM_ID_Reg = "(.*?)/providers/microsoft.apimanagement/service/([^/]+)/apiVersionSets/([^/]+)"
    API_VS_PREFIX = "/apiVersionSets/"

    full_path = None

    if version_set_id is not None:
        if re.match(API_VS_ARM_ID_Reg, version_set_id) is None:
            full_path = API_VS_PREFIX + version_set_id
        else:
            full_path = version_set_id

    return full_path


def get_if_match(if_match=None):
    value = if_match = "*" if if_match is None else if_match
    return value
