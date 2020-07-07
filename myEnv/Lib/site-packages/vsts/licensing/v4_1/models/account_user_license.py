# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccountUserLicense(Model):
    """AccountUserLicense.

    :param license:
    :type license: int
    :param source:
    :type source: object
    """

    _attribute_map = {
        'license': {'key': 'license', 'type': 'int'},
        'source': {'key': 'source', 'type': 'object'}
    }

    def __init__(self, license=None, source=None):
        super(AccountUserLicense, self).__init__()
        self.license = license
        self.source = source
