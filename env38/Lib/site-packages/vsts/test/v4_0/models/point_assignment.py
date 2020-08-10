# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PointAssignment(Model):
    """PointAssignment.

    :param configuration:
    :type configuration: :class:`ShallowReference <test.v4_0.models.ShallowReference>`
    :param tester:
    :type tester: :class:`IdentityRef <test.v4_0.models.IdentityRef>`
    """

    _attribute_map = {
        'configuration': {'key': 'configuration', 'type': 'ShallowReference'},
        'tester': {'key': 'tester', 'type': 'IdentityRef'}
    }

    def __init__(self, configuration=None, tester=None):
        super(PointAssignment, self).__init__()
        self.configuration = configuration
        self.tester = tester
