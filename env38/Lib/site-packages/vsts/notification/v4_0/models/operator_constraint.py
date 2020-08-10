# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class OperatorConstraint(Model):
    """OperatorConstraint.

    :param operator:
    :type operator: str
    :param supported_scopes: Gets or sets the list of scopes that this type supports.
    :type supported_scopes: list of str
    """

    _attribute_map = {
        'operator': {'key': 'operator', 'type': 'str'},
        'supported_scopes': {'key': 'supportedScopes', 'type': '[str]'}
    }

    def __init__(self, operator=None, supported_scopes=None):
        super(OperatorConstraint, self).__init__()
        self.operator = operator
        self.supported_scopes = supported_scopes
