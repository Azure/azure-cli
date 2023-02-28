# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import UnrecognizedArgumentError


def _list_to_dict(enum_list):
    return {item.lower(): item for item in enum_list}


def enum_check(value, enum_list):
    try:
        return _list_to_dict(enum_list)[value.lower()]
    except:
        raise UnrecognizedArgumentError(f'{value} is not recognized, it must be one of {enum_list}')
