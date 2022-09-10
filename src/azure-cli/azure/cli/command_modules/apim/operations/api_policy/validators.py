# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.cli.command_modules.apim._util import (get_xml_content)


def validate_policy_xml_content(namespace):
    """Validates that the xml content has been set"""
    xml_content = get_xml_content(namespace.xml, namespace.xml_path, namespace.xml_uri)

    if xml_content is None or not xml_content:
        raise CLIError('The XML content for a policy is required for creating or updating a policy')
