# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccountRights(Model):
    """AccountRights.

    :param level:
    :type level: object
    :param reason:
    :type reason: str
    """

    _attribute_map = {
        'level': {'key': 'level', 'type': 'object'},
        'reason': {'key': 'reason', 'type': 'str'}
    }

    def __init__(self, level=None, reason=None):
        super(AccountRights, self).__init__()
        self.level = level
        self.reason = reason
