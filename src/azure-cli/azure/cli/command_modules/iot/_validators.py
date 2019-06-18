# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from argparse import ArgumentError
from .custom import SimpleAccessRights


def validate_policy_permissions(ns):
    if ns.permissions is None or ns.permissions == []:
        raise ArgumentError(None, 'the following arguments are required: --permissions')

    allowed = [x.value.lower() for x in SimpleAccessRights]
    for p in ns.permissions:
        if p not in allowed:
            raise ValueError('Unrecognized permission "{}"'.format(p))
