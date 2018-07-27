# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from ._client_factory import cf_acr_registries


def validate_registry_name(cmd, namespace):
    if namespace.registry_name:
        client = cf_acr_registries(cmd.cli_ctx)
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


def validate_build_arg(namespace):
    if isinstance(namespace.build_arg, list):
        build_arguments_list = []
        for item in namespace.build_arg:
            build_arguments_list.append(validate_build_argument(item, False))
        namespace.build_arg = build_arguments_list


def validate_secret_build_arg(namespace):
    if isinstance(namespace.secret_build_arg, list):
        build_arguments_list = []
        for item in namespace.secret_build_arg:
            build_arguments_list.append(validate_build_argument(item, True))
        namespace.secret_build_arg = build_arguments_list


def validate_build_argument(string, is_secret):
    """Extracts a single build argument in key[=value] format. """
    if string:
        comps = string.split('=', 1)
        if len(comps) > 1:
            return {'type': 'DockerBuildArgument', 'name': comps[0], 'value': comps[1], 'isSecret': is_secret}
        return {'type': 'DockerBuildArgument', 'name': comps[0], 'value': '', 'isSecret': is_secret}
    return None
