# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from ._factory import get_acr_service_client


def validate_registry_name(namespace):
    if namespace.registry_name:
        client = get_acr_service_client().registries
        registry_name = namespace.registry_name

        result = client.check_name_availability(registry_name)

        if not result.name_available:  # pylint: disable=no-member
            raise CLIError(result.message)  # pylint: disable=no-member


def validate_headers(namespace):
    """Extracts multiple space-separated headers in key[=value] format. """
    if isinstance(namespace.headers, list):
        headers_dict = {}
        for item in namespace.headers:
            headers_dict.update(validate_header(item))
        namespace.headers = headers_dict


def validate_header(string):
    """Extracts a single header in key[=value] format. """
    result = {}
    if string:
        comps = string.split('=', 1)
        result = {comps[0]: comps[1]} if len(comps) > 1 else {string: ''}
    return result
