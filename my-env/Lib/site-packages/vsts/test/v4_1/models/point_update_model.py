# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PointUpdateModel(Model):
    """PointUpdateModel.

    :param outcome:
    :type outcome: str
    :param reset_to_active:
    :type reset_to_active: bool
    :param tester:
    :type tester: :class:`IdentityRef <test.v4_1.models.IdentityRef>`
    """

    _attribute_map = {
        'outcome': {'key': 'outcome', 'type': 'str'},
        'reset_to_active': {'key': 'resetToActive', 'type': 'bool'},
        'tester': {'key': 'tester', 'type': 'IdentityRef'}
    }

    def __init__(self, outcome=None, reset_to_active=None, tester=None):
        super(PointUpdateModel, self).__init__()
        self.outcome = outcome
        self.reset_to_active = reset_to_active
        self.tester = tester
