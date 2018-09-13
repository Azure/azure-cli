# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


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


def validate_arg(namespace):
    if isinstance(namespace.arg, list):
        arguments_list = []
        for item in namespace.arg:
            arguments_list.append(validate_task_argument(item, False))
        namespace.arg = arguments_list


def validate_secret_arg(namespace):
    if isinstance(namespace.secret_arg, list):
        secret_arguments_list = []
        for item in namespace.secret_arg:
            secret_arguments_list.append(validate_task_argument(item, True))
        namespace.secret_arg = secret_arguments_list


def validate_set(namespace):
    if isinstance(namespace.set_value, list):
        set_list = []
        for item in namespace.set_value:
            set_list.append(validate_task_value(item, False))
        namespace.set_value = set_list


def validate_set_secret(namespace):
    if isinstance(namespace.set_secret, list):
        set_secret_list = []
        for item in namespace.set_secret:
            set_secret_list.append(validate_task_value(item, True))
        namespace.set_secret = set_secret_list


def validate_task_value(string, is_secret):
    """Extracts a single SetValue in key[=value] format. """
    if string:
        comps = string.split('=', 1)
        if len(comps) > 1:
            return {'type': 'SetValue', 'name': comps[0], 'value': comps[1], 'isSecret': is_secret}
        return {'type': 'SetValue', 'name': comps[0], 'value': '', 'isSecret': is_secret}
    return None


def validate_task_argument(string, is_secret):
    """Extracts a single argument in key[=value] format. """
    if string:
        comps = string.split('=', 1)
        if len(comps) > 1:
            return {'type': 'Argument', 'name': comps[0], 'value': comps[1], 'isSecret': is_secret}
        return {'type': 'Argument', 'name': comps[0], 'value': '', 'isSecret': is_secret}
    return None
